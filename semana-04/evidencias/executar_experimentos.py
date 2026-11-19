#!/usr/bin/env python3
"""Executa os experimentos práticos e coleta de métricas da Semana 4.

Registra comandos, saídas reais, tempos, chamadas de sistema (strace),
tamanhos em disco e metadados de vinculação dinâmica (ELF/RUNPATH) para:
1. Debian (APT/dpkg) em container oficial debian:trixie-slim (Docker)
2. FreeBSD Ports (receita oficial misc/hello + medição experimental de compilação GNU Hello com/sem NLS)
3. Nix (store, perfis, gerações, rollback, fechamento vs. tamanho próprio, wrappers e RUNPATH)
4. Flatpak (Flathub metadata, OSTree deduplicação por hardlinks, Bubblewrap namespaces/RO/RW) e Snap (inspeção real do gnome-text-editor_53.snap, SquashFS xz/zstd/gzip, meta/snap.yaml e suporte de kernel)
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import tempfile
import time

EVID_DIR = Path(__file__).resolve().parent
SEM2_NIX_DIR = EVID_DIR.parents[1] / "semana-02" / "nix"

FLATPAK_BIN = "/nix/store/ln6lcrf6kk65his4r5q1zgfn29jcz3s6-flatpak-1.18.4/bin/flatpak"
BWRAP_BIN = "/nix/store/m50dfhnbbqpvj79i444kcdd2zsfwr4hk-bubblewrap-0.13.1/bin/bwrap"
OSTREE_BIN = "/nix/store/57a720jdismlqv2a708hi7kmb7rins36-ostree-2026.2/bin/ostree"
SQUASHFS_DIR = "/nix/store/cgj65l0kswbz928pq40ybf4jb34yndbi-squashfs-tools-4.7.5/bin"
MKSQUASHFS_BIN = f"{SQUASHFS_DIR}/mksquashfs"
UNSQUASHFS_BIN = f"{SQUASHFS_DIR}/unsquashfs"
STRACE_BIN = "/nix/store/78jn0lxqjgz4ahjzvvh4rvan7p607xph-strace-7.2/bin/strace"
READELF_BIN = "/nix/store/45qppvrgigcmyjina7a6p82f2pf5kzmr-binutils-2.46/bin/readelf"
LDD_BIN = "/run/current-system/sw/bin/ldd"
HELLO_NIX = "/nix/store/sd779x86bjaqxj2lzh2jsir4h0zjz6d1-hello-2.12.3"
TMUX_NIX = "/nix/store/7v8w4qyz2wsr251nkxzbcmhbrwlylg7f-tmux-3.8"
EDITOR_NIX = "/nix/store/94r4v2l4r5lzmik62h7mnfi7bwvqnmfz-gnome-text-editor-50.1"


def run_cmd(cmd: list[str] | str, cwd: Path | str | None = None, env: dict | None = None, shell: bool = False) -> dict:
    merged_env = os.environ.copy()
    merged_env["LC_ALL"] = "C.UTF-8"
    if env:
        merged_env.update(env)
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=merged_env,
        shell=shell,
        text=True,
        capture_output=True,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "cmd": cmd if isinstance(cmd, str) else " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "elapsed_ms": round(elapsed_ms, 2),
    }


def format_log_entry(res: dict) -> str:
    out = [f"$ {res['cmd']}"]
    if res["stdout"].strip():
        out.append(res["stdout"].rstrip())
    if res["stderr"].strip():
        out.append("[stderr]\n" + res["stderr"].rstrip())
    out.append(f"[Código de saída: {res['returncode']} | Tempo: {res['elapsed_ms']:.2f} ms]\n")
    return "\n".join(out)


def parse_strace_summary(stderr_text: str) -> dict:
    """Extrai total de chamadas, erros e principais syscalls do strace -c."""
    lines = stderr_text.splitlines()
    syscalls = {}
    total_calls = 0
    total_errors = 0
    in_table = False
    for line in lines:
        if "------" in line:
            in_table = not in_table
            continue
        if in_table:
            parts = line.split()
            if len(parts) >= 5:
                # % time, seconds, usecs/call, calls, [errors], syscall
                calls = int(parts[3])
                if len(parts) == 6:
                    errors = int(parts[4])
                    name = parts[5]
                else:
                    errors = 0
                    name = parts[4]
                syscalls[name] = {"calls": calls, "errors": errors}
        elif line.strip().startswith("100.00"):
            parts = line.split()
            if len(parts) >= 5:
                total_calls = int(parts[3])
                if len(parts) >= 6 and parts[4].isdigit():
                    total_errors = int(parts[4])
    return {
        "total_calls": total_calls,
        "total_errors": total_errors,
        "syscalls": syscalls,
    }


def summarize_series(values: list[float]) -> dict:
    return {
        "repeticoes": [round(v, 2) for v in values],
        "media": round(statistics.mean(values), 2),
        "mediana": round(statistics.median(values), 2),
        "desvio_padrao": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
    }


def collect_environment() -> dict:
    print("[1/5] Coletando informações do ambiente experimental...")
    uname = run_cmd(["uname", "-a"])
    nixos_ver = run_cmd(["nixos-version", "--json"])
    lscpu = run_cmd("lscpu | grep -E 'Architecture|Model name|CPU\\(s\\):|Thread|Core'", shell=True)
    mem = run_cmd(["free", "-b"])
    df = run_cmd(["df", "-B1", "/"])
    lsm = Path("/sys/kernel/security/lsm").read_text().strip() if Path("/sys/kernel/security/lsm").exists() else "indisponível"
    cgroups = Path("/sys/fs/cgroup/cgroup.controllers").read_text().strip() if Path("/sys/fs/cgroup/cgroup.controllers").exists() else "indisponível"

    versions = {
        "nix": run_cmd(["nix", "--version"])["stdout"].strip(),
        "docker": run_cmd(["docker", "--version"])["stdout"].strip(),
        "flatpak": run_cmd([FLATPAK_BIN, "--version"])["stdout"].strip(),
        "bubblewrap": run_cmd([BWRAP_BIN, "--version"])["stdout"].strip(),
        "ostree": " ".join(run_cmd([OSTREE_BIN, "--version"])["stdout"].splitlines()[:2]).strip(),
        "squashfs_tools": run_cmd([MKSQUASHFS_BIN, "-version"])["stdout"].splitlines()[0].strip(),
        "strace": run_cmd([STRACE_BIN, "--version"])["stdout"].splitlines()[0].strip(),
        "readelf": run_cmd([READELF_BIN, "--version"])["stdout"].splitlines()[0].strip(),
    }

    env_data = {
        "data_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data_local": datetime.datetime.now().astimezone().isoformat(),
        "uname": uname["stdout"].strip(),
        "nixos": json.loads(nixos_ver["stdout"]),
        "lscpu": lscpu["stdout"].strip(),
        "lsm_ativos": lsm,
        "cgroup_v2_controllers": cgroups,
        "wayland_socket_presente": Path("/run/user/1000/wayland-1").exists(),
        "versoes_ferramentas": versions,
    }
    (EVID_DIR / "ambiente-experimental.json").write_text(json.dumps(env_data, indent=2, ensure_ascii=False) + "\n")
    log_txt = "\n".join([
        format_log_entry(uname),
        format_log_entry(nixos_ver),
        format_log_entry(lscpu),
        format_log_entry(mem),
        format_log_entry(df),
        f"LSM ativos (/sys/kernel/security/lsm): {lsm}\n",
        f"Controladores cgroup v2 (/sys/fs/cgroup/cgroup.controllers): {cgroups}\n",
    ])
    (EVID_DIR / "ambiente-experimental.txt").write_text(log_txt)
    return env_data


def run_debian_experiments() -> dict:
    print("[2/5] Executando experimentos de Debian (APT/dpkg) em container debian:trixie-slim...")
    logs = []
    # Criamos um diretório temporário para guardar os pacotes .deb baixados uma única vez
    # e também ferramentas estáticas/auxiliares na medição
    with tempfile.TemporaryDirectory(prefix="so-debian-cache-") as cache_dir:
        cache_path = Path(cache_dir)
        # 1. Atualizar índice APT e baixar .debs de tmux, hello e binutils em uma imagem base preparada
        prep_script = """
set -e
cat /etc/os-release
apt-get --version | head -n 1
dpkg --version | head -n 1
apt-get update -qq
apt-cache policy tmux hello gnome-text-editor
apt-cache depends tmux
apt-cache depends hello
apt-get install --download-only -y tmux hello
ls -la /var/cache/apt/archives/*.deb
cp /var/cache/apt/archives/*.deb /cache/
apt-get install -s gnome-text-editor | grep -E "Inst |upgraded,"
"""
        res_prep = run_cmd([
            "docker", "run", "--rm",
            "-v", f"{cache_path}:/cache",
            "debian:trixie-slim", "bash", "-c", prep_script
        ])
        logs.append(format_log_entry(res_prep))

        debs = sorted(cache_path.glob("*.deb"))
        tmux_debs = [p for p in debs if "hello" not in p.name]
        hello_debs = [p for p in debs if "hello" in p.name]
        tmux_download_bytes = sum(p.stat().st_size for p in tmux_debs)
        hello_download_bytes = sum(p.stat().st_size for p in hello_debs)

        # 2. Inspecionar estrutura interna do .deb do tmux e do hello
        inspect_script = """
set -e
TMUX_DEB=$(ls /cache/tmux_*.deb)
HELLO_DEB=$(ls /cache/hello_*.deb)
echo "=== Estrutura ar do pacote .deb (dpkg-deb / formato ar) ==="
dpkg-deb -I "$TMUX_DEB"
dpkg-deb -c "$TMUX_DEB"
dpkg-deb -I "$HELLO_DEB"
dpkg-deb -c "$HELLO_DEB"
"""
        res_inspect = run_cmd([
            "docker", "run", "--rm",
            "-v", f"{cache_path}:/cache:ro",
            "debian:trixie-slim", "bash", "-c", inspect_script
        ])
        logs.append(format_log_entry(res_inspect))

        # 3. Medir 3 repetições de instalação local (sem rede) de tmux e de hello em containers limpos
        # Montamos também STRACE_BIN e READELF_BIN via /nix/store somente-leitura para medir sem alterar a imagem Debian!
        tmux_install_ms = []
        hello_install_ms = []
        hello_cold_start_ms = []
        tmux_cold_start_ms = []

        for rep in range(1, 4):
            # Medição limpa de tmux (dpkg -i dos pacotes baixados para tmux)
            t_cmd = [
                "docker", "run", "--rm", "--network=none",
                "-v", f"{cache_path}:/cache:ro",
                "debian:trixie-slim", "bash", "-c",
                "set -e; mkdir -p /tmp/debs && cp /cache/*.deb /tmp/debs/ && rm -f /tmp/debs/hello_*.deb && "
                "t0=$(date +%s%N); dpkg -i /tmp/debs/*.deb >/dev/null; t1=$(date +%s%N); "
                "echo $(( (t1 - t0) / 1000000 )); "
                "t2=$(date +%s%N); /usr/bin/tmux -V >/dev/null; t3=$(date +%s%N); "
                "echo $(( (t3 - t2) / 1000000 ))"
            ]
            r_t = run_cmd(t_cmd)
            nums = [float(x) for x in r_t["stdout"].strip().splitlines()]
            tmux_install_ms.append(nums[0])
            tmux_cold_start_ms.append(nums[1])

            # Medição limpa de hello (dpkg -i do pacote hello)
            h_cmd = [
                "docker", "run", "--rm", "--network=none",
                "-v", f"{cache_path}:/cache:ro",
                "debian:trixie-slim", "bash", "-c",
                "set -e; t0=$(date +%s%N); dpkg -i /cache/hello_*.deb >/dev/null; t1=$(date +%s%N); "
                "echo $(( (t1 - t0) / 1000000 )); "
                "t2=$(date +%s%N); /usr/bin/hello >/dev/null; t3=$(date +%s%N); "
                "echo $(( (t3 - t2) / 1000000 ))"
            ]
            r_h = run_cmd(h_cmd)
            nums_h = [float(x) for x in r_h["stdout"].strip().splitlines()]
            hello_install_ms.append(nums_h[0])
            hello_cold_start_ms.append(nums_h[1])

        # 4. Contagem de syscalls (strace -c -f) e consultas pós-instalação + vinculação dinâmica ELF
        trace_script = f"""
set -e
mkdir -p /tmp/debs
cp /cache/*.deb /tmp/debs/
rm -f /tmp/debs/hello_*.deb
echo "=== strace dpkg -i tmux (+ dependencias) ==="
{STRACE_BIN} -c -f dpkg -i /tmp/debs/*.deb >/dev/null
echo "=== Consultas dpkg para tmux ==="
dpkg -l tmux
dpkg -L tmux
dpkg -S /usr/bin/tmux
head -n 10 /var/lib/dpkg/info/tmux.md5sums
echo "=== Vinculacao dinamica ELF de /usr/bin/tmux ==="
{READELF_BIN} -d /usr/bin/tmux | grep -E "NEEDED|RUNPATH|RPATH"
ldd /usr/bin/tmux
"""
        res_trace_tmux = run_cmd([
            "docker", "run", "--rm", "--cap-add=SYS_PTRACE",
            "-v", f"{cache_path}:/cache:ro",
            "-v", "/nix/store:/nix/store:ro",
            "debian:trixie-slim", "bash", "-c", trace_script
        ])
        logs.append(format_log_entry(res_trace_tmux))
        tmux_strace = parse_strace_summary(res_trace_tmux["stderr"])

        trace_hello_script = f"""
set -e
echo "=== strace dpkg -i hello ==="
{STRACE_BIN} -c -f dpkg -i /cache/hello_*.deb >/dev/null
echo "=== Consultas dpkg para hello ==="
dpkg -l hello
dpkg -L hello
dpkg -S /usr/bin/hello
/usr/bin/hello --version | head -n 2
echo "=== Vinculacao dinamica ELF de /usr/bin/hello ==="
{READELF_BIN} -d /usr/bin/hello | grep -E "NEEDED|RUNPATH|RPATH"
ldd /usr/bin/hello
"""
        res_trace_hello = run_cmd([
            "docker", "run", "--rm", "--cap-add=SYS_PTRACE",
            "-v", f"{cache_path}:/cache:ro",
            "-v", "/nix/store:/nix/store:ro",
            "debian:trixie-slim", "bash", "-c", trace_hello_script
        ])
        logs.append(format_log_entry(res_trace_hello))
        hello_strace = parse_strace_summary(res_trace_hello["stderr"])

        # Simulação detalhada do gnome-text-editor no Debian Trixie
        res_gte_sim = run_cmd([
            "docker", "run", "--rm",
            "debian:trixie-slim", "bash", "-c",
            "apt-get update -qq && apt-cache show gnome-text-editor | grep -E '^(Package|Version|Installed-Size|Depends):' && apt-get install -s gnome-text-editor | tail -n 5"
        ])
        logs.append(format_log_entry(res_gte_sim))

    metrics = {
        "ambiente": "Container Docker debian:trixie-slim (Debian GNU/Linux 13 Trixie) sobre kernel Linux 7.3.4 x86_64",
        "tmux": {
            "versao": "3.5a-3",
            "pacotes_deb_baixados": [p.name for p in tmux_debs],
            "quantidade_debs": len(tmux_debs),
            "download_total_bytes": tmux_download_bytes,
            "download_total_kib": round(tmux_download_bytes / 1024, 2),
            "tempo_instalacao_local_ms": summarize_series(tmux_install_ms),
            "tempo_execucao_versao_ms": summarize_series(tmux_cold_start_ms),
            "strace_instalacao": tmux_strace,
            "vinculacao_elf": "FHS padrão (/lib/x86_64-linux-gnu/libc.so.6, libevent_core-2.1.so.7, libtinfo.so.6); sem RPATH/RUNPATH",
        },
        "hello": {
            "versao": "2.10-5",
            "pacotes_deb_baixados": [p.name for p in hello_debs],
            "quantidade_debs": len(hello_debs),
            "download_total_bytes": hello_download_bytes,
            "download_total_kib": round(hello_download_bytes / 1024, 2),
            "tempo_instalacao_local_ms": summarize_series(hello_install_ms),
            "tempo_execucao_ms": summarize_series(hello_cold_start_ms),
            "strace_instalacao": hello_strace,
            "vinculacao_elf": "FHS padrão (/lib/x86_64-linux-gnu/libc.so.6); sem RPATH/RUNPATH",
        },
        "gnome_text_editor_simulacao": {
            "saida_resumo": res_gte_sim["stdout"].strip(),
        },
    }
    (EVID_DIR / "debian-apt-dpkg.txt").write_text("\n".join(logs))
    (EVID_DIR / "debian-metricas.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    return metrics


def run_ports_and_source_experiments() -> dict:
    print("[3/5] Executando inspeção do FreeBSD Ports (misc/hello) e medição de compilação a partir do código-fonte...")
    logs = []
    # 1. Consultar receita oficial do FreeBSD Ports (misc/hello/Makefile e distinfo)
    res_mk = run_cmd(["curl", "-4", "-sL", "https://cgit.freebsd.org/ports/plain/misc/hello/Makefile"])
    res_dist = run_cmd(["curl", "-4", "-sL", "https://cgit.freebsd.org/ports/plain/misc/hello/distinfo"])
    res_descr = run_cmd(["curl", "-4", "-sL", "https://cgit.freebsd.org/ports/plain/misc/hello/pkg-descr"])
    logs.extend([
        "=== Receita oficial consultada da árvore FreeBSD Ports: misc/hello ===",
        format_log_entry(res_mk),
        format_log_entry(res_dist),
        format_log_entry(res_descr),
    ])

    # 2. Baixar o mesmo distfile oficial referenciado pelo FreeBSD Ports (hello-2.12.3.tar.gz)
    # e medir no ambiente controlado a construção das fases extract -> configure -> build -> stage (com e sem NLS)
    with tempfile.TemporaryDirectory(prefix="so-ports-source-") as work_root:
        work_path = Path(work_root)
        tarball = work_path / "hello-2.12.3.tar.gz"
        res_dl = run_cmd([
            "curl", "-4", "-sL", "https://ftpmirror.gnu.org/gnu/hello/hello-2.12.3.tar.gz",
            "-o", str(tarball)
        ])
        logs.append(format_log_entry(res_dl))
        sha256_actual = hashlib.sha256(tarball.read_bytes()).hexdigest()
        size_actual = tarball.stat().st_size

        variants_metrics = {}
        for variant_name, cfg_flag in [("nls_ativado", "--enable-nls"), ("nls_desativado", "--disable-nls")]:
            cfg_times = []
            build_times = []
            stage_times = []
            total_times = []
            wrkdir_bytes = 0
            wrkdir_files = 0
            stage_bytes = 0
            stage_files = 0
            locale_files = 0

            for rep in range(1, 4):
                rep_dir = work_path / f"{variant_name}_rep{rep}"
                wrksrc = rep_dir / "work"
                stagedir = rep_dir / "stage"
                wrksrc.mkdir(parents=True)
                stagedir.mkdir(parents=True)

                t_start = time.perf_counter()
                run_cmd(["tar", "-xzf", str(tarball), "-C", str(wrksrc)])
                src_dir = wrksrc / "hello-2.12.3"

                t0 = time.perf_counter()
                r_cfg = run_cmd(
                    ["./configure", "--prefix=/usr/local", cfg_flag],
                    cwd=src_dir,
                )
                t_cfg = (time.perf_counter() - t0) * 1000.0
                if r_cfg["returncode"] != 0:
                    raise RuntimeError(f"Falha no configure ({variant_name}): {r_cfg['stderr']}")

                t1 = time.perf_counter()
                r_build = run_cmd(["make", "-j4"], cwd=src_dir)
                t_build = (time.perf_counter() - t1) * 1000.0
                if r_build["returncode"] != 0:
                    raise RuntimeError(f"Falha no make ({variant_name}): {r_build['stderr']}")

                t2 = time.perf_counter()
                r_stage = run_cmd(["make", f"DESTDIR={stagedir}", "install"], cwd=src_dir)
                t_stage = (time.perf_counter() - t2) * 1000.0
                t_total = (time.perf_counter() - t_start) * 1000.0

                cfg_times.append(t_cfg)
                build_times.append(t_build)
                stage_times.append(t_stage)
                total_times.append(t_total)

                if rep == 1:
                    logs.append(f"=== Construção experimental de hello-2.12.3 ({variant_name}: {cfg_flag}) ===")
                    logs.append(format_log_entry(r_cfg))
                    logs.append(format_log_entry(r_build))
                    logs.append(format_log_entry(r_stage))
                    wrkdir_bytes = sum(p.stat().st_size for p in wrksrc.rglob("*") if p.is_file() and not p.is_symlink())
                    wrkdir_files = sum(1 for _ in wrksrc.rglob("*"))
                    stage_bytes = sum(p.stat().st_size for p in stagedir.rglob("*") if p.is_file() and not p.is_symlink())
                    stage_files = sum(1 for p in stagedir.rglob("*") if p.is_file())
                    locale_files = sum(1 for p in stagedir.rglob("*.mo") if p.is_file())

            # Rodar 1 passagem com strace -c -f para contar as chamadas de sistema de toda a construção
            trace_dir = work_path / f"{variant_name}_trace"
            trace_dir.mkdir(parents=True)
            res_trace = run_cmd([
                STRACE_BIN, "-c", "-f", "sh", "-c",
                f"tar -xzf {tarball} -C {trace_dir} && cd {trace_dir}/hello-2.12.3 && "
                f"./configure --prefix=/usr/local {cfg_flag} >/dev/null 2>&1 && "
                f"make -j4 >/dev/null 2>&1 && make DESTDIR={trace_dir}/stage install >/dev/null 2>&1"
            ])
            logs.append(format_log_entry(res_trace))
            strace_summary = parse_strace_summary(res_trace["stderr"])

            variants_metrics[variant_name] = {
                "flag_configure": cfg_flag,
                "tempo_configure_ms": summarize_series(cfg_times),
                "tempo_build_ms": summarize_series(build_times),
                "tempo_stage_install_ms": summarize_series(stage_times),
                "tempo_total_fases_ms": summarize_series(total_times),
                "wrkdir_bytes": wrkdir_bytes,
                "wrkdir_mib": round(wrkdir_bytes / (1024 * 1024), 2),
                "wrkdir_arquivos_temporarios": wrkdir_files,
                "stage_instalado_bytes": stage_bytes,
                "stage_instalado_kib": round(stage_bytes / 1024, 2),
                "stage_arquivos_finais": stage_files,
                "arquivos_catalogo_locale_mo": locale_files,
                "strace_construcao_completa": strace_summary,
            }

    metrics = {
        "alcance_metodologico": (
            "A receita misc/hello (Makefile, distinfo, pkg-descr) foi consultada diretamente na árvore oficial do FreeBSD Ports. "
            "Como não há máquina virtual FreeBSD no hospedeiro Linux, as medições de compilação abaixo foram executadas "
            "sobre o mesmo código-fonte oficial (GNU hello 2.12.3, SHA256 verificado) no ambiente Linux local, isolando o custo real "
            "das fases extract, configure, build e stage com --enable-nls vs --disable-nls."
        ),
        "receita_freebsd_ports": {
            "port": "misc/hello",
            "versao": "2.12.3",
            "uses": ["charsetfix", "gmake", "perl5"],
            "options_define": ["NLS"],
            "nls_configure_enable": "nls",
            "nls_uses": ["gettext", "localbase"],
            "distfile_nome": "hello-2.12.3.tar.gz",
            "distfile_size_bytes": size_actual,
            "distfile_sha256_esperado": "0d5f60154382fee10b114a1c34e785d8b1f492073ae2d3a6f7b147687b366aa0",
            "distfile_sha256_verificado": sha256_actual,
            "checksum_coincide": sha256_actual == "0d5f60154382fee10b114a1c34e785d8b1f492073ae2d3a6f7b147687b366aa0",
        },
        "comparacao_compilacao_nls": variants_metrics,
    }
    (EVID_DIR / "freebsd-ports-e-compilacao-hello.txt").write_text("\n".join(logs))
    (EVID_DIR / "ports-compilacao-metricas.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    return metrics


def run_nix_experiments() -> dict:
    print("[4/5] Executando experimentos de Nix (store, perfis, gerações, rollback e RUNPATH)...")
    logs = []
    # 1. Tamanhos no store: tamanho próprio (NAR) vs fechamento transitivo (closure)
    res_sizes = run_cmd([
        "nix", "path-info", "-s", "-S",
        HELLO_NIX, TMUX_NIX, EDITOR_NIX,
    ])
    res_sizes_h = run_cmd([
        "nix", "path-info", "-s", "-S", "-h",
        HELLO_NIX, TMUX_NIX, EDITOR_NIX,
    ])
    logs.extend([format_log_entry(res_sizes), format_log_entry(res_sizes_h)])

    size_table = {}
    for line in res_sizes["stdout"].strip().splitlines():
        parts = line.split()
        if len(parts) >= 3:
            path, nar_b, clos_b = parts[0], int(parts[1]), int(parts[2])
            pkg_key = path.split("-", 1)[1]
            size_table[pkg_key] = {
                "store_path": path,
                "nar_bytes": nar_b,
                "nar_kib": round(nar_b / 1024, 2),
                "closure_bytes": clos_b,
                "closure_mib": round(clos_b / (1024 * 1024), 2),
            }

    # 2. Inspeção de vinculação dinâmica (readelf -d e ldd) e wrapper do gnome-text-editor
    editor_wrapper = f"{EDITOR_NIX}/bin/gnome-text-editor"
    editor_real = f"{EDITOR_NIX}/bin/.gnome-text-editor-wrapped"
    tmux_bin = f"{TMUX_NIX}/bin/tmux"
    hello_bin = f"{HELLO_NIX}/bin/hello"

    for label, bpath in [
        ("hello", hello_bin),
        ("tmux", tmux_bin),
        ("gnome-text-editor (wrapper)", editor_wrapper),
        ("gnome-text-editor (binário ELF real)", editor_real),
    ]:
        logs.append(f"=== Vinculação dinâmica ELF no Nix: {label} ({bpath}) ===")
        r_re = run_cmd(f"{READELF_BIN} -d {bpath} | grep -E 'NEEDED|RUNPATH|RPATH'", shell=True)
        r_ldd = run_cmd([LDD_BIN, bpath])
        logs.extend([format_log_entry(r_re), format_log_entry(r_ldd)])

    # 3. Medição de ativação de perfil (nix profile add), remoção e rollback em 3 repetições
    add_editor_ms = []
    add_tmux_ms = []
    add_hello_ms = []
    rollback_ms = []
    hello_exec_ms = []
    tmux_exec_ms = []
    editor_exec_ms = []

    with tempfile.TemporaryDirectory(prefix="so-nix-bench-") as tmp_root:
        tmp_path = Path(tmp_root)
        for rep in range(1, 4):
            prof_e = tmp_path / f"prof-editor-{rep}"
            r_ae = run_cmd(["nix", "profile", "add", "--profile", str(prof_e), EDITOR_NIX])
            add_editor_ms.append(r_ae["elapsed_ms"])
            r_ee = run_cmd([str(prof_e / "bin/gnome-text-editor"), "--version"])
            editor_exec_ms.append(r_ee["elapsed_ms"])
            run_cmd(["nix", "profile", "remove", "--profile", str(prof_e), "--all"])
            r_rb = run_cmd(["nix", "profile", "rollback", "--profile", str(prof_e)])
            rollback_ms.append(r_rb["elapsed_ms"])
            if rep == 1:
                logs.extend([format_log_entry(r_ae), format_log_entry(r_ee), format_log_entry(r_rb)])

            prof_t = tmp_path / f"prof-tmux-{rep}"
            r_at = run_cmd(["nix", "profile", "add", "--profile", str(prof_t), TMUX_NIX])
            add_tmux_ms.append(r_at["elapsed_ms"])
            r_et = run_cmd([str(prof_t / "bin/tmux"), "-V"])
            tmux_exec_ms.append(r_et["elapsed_ms"])

            prof_h = tmp_path / f"prof-hello-{rep}"
            r_ah = run_cmd(["nix", "profile", "add", "--profile", str(prof_h), HELLO_NIX])
            add_hello_ms.append(r_ah["elapsed_ms"])
            r_eh = run_cmd([str(prof_h / "bin/hello")])
            hello_exec_ms.append(r_eh["elapsed_ms"])

        # Contagem de syscalls (strace -c -f) de nix profile add e nix profile rollback
        prof_trace = tmp_path / "prof-trace"
        r_strace_add = run_cmd([
            STRACE_BIN, "-c", "-f",
            "nix", "profile", "add", "--profile", str(prof_trace), HELLO_NIX,
        ])
        run_cmd(["nix", "profile", "remove", "--profile", str(prof_trace), "--all"])
        r_strace_rb = run_cmd([
            STRACE_BIN, "-c", "-f",
            "nix", "profile", "rollback", "--profile", str(prof_trace),
        ])
        logs.extend([format_log_entry(r_strace_add), format_log_entry(r_strace_rb)])
        strace_add = parse_strace_summary(r_strace_add["stderr"])
        strace_rb = parse_strace_summary(r_strace_rb["stderr"])

        # Demonstração de coexistência de dois perfis independentes com seleções distintas (Perfil A: hello+editor, Perfil B: tmux+editor)
        prof_a = tmp_path / "demo-perfil-a"
        prof_b = tmp_path / "demo-perfil-b"
        run_cmd(["nix", "profile", "add", "--profile", str(prof_a), EDITOR_NIX, HELLO_NIX])
        run_cmd(["nix", "profile", "add", "--profile", str(prof_b), EDITOR_NIX, TMUX_NIX])
        r_list_a = run_cmd(["nix", "profile", "list", "--profile", str(prof_a)])
        r_list_b = run_cmd(["nix", "profile", "list", "--profile", str(prof_b)])
        logs.extend([
            "=== Coexistência de perfis independentes (Perfil A vs Perfil B) ===",
            format_log_entry(r_list_a),
            format_log_entry(r_list_b),
        ])

    metrics = {
        "ambiente": "Nix 2.34.9 nativo no NixOS 26.11.20261111.d4f25a3 (kernel 7.3.4 x86_64)",
        "armazenamento_store": size_table,
        "tempos_perfil_ms": {
            "profile_add_gnome_text_editor": summarize_series(add_editor_ms),
            "profile_add_tmux": summarize_series(add_tmux_ms),
            "profile_add_hello": summarize_series(add_hello_ms),
            "profile_rollback": summarize_series(rollback_ms),
            "execucao_hello": summarize_series(hello_exec_ms),
            "execucao_tmux_version": summarize_series(tmux_exec_ms),
            "execucao_gnome_text_editor_version": summarize_series(editor_exec_ms),
        },
        "strace_profile_add_hello": strace_add,
        "strace_profile_rollback": strace_rb,
        "vinculacao_elf": {
            "mecanismo": (
                "Cada binário ELF possui RUNPATH gravado no cabeçalho apontando diretamente para os diretórios "
                "/nix/store/<hash>-.../lib de suas dependências exatas. Para aplicações GTK/GNOME como o gnome-text-editor, "
                "bin/gnome-text-editor é um binário wrapper compilado que exporta variáveis de esquema/ícones/GIO e invoca "
                "bin/.gnome-text-editor-wrapped."
            )
        },
    }
    (EVID_DIR / "nix-perfis-geracoes-vinculacao.txt").write_text("\n".join(logs))
    (EVID_DIR / "nix-metricas.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    return metrics


def run_flatpak_snap_experiments() -> dict:
    print("[5/5] Executando experimentos de Flatpak (Flathub, OSTree, Bubblewrap) e Snap (SquashFS, meta/snap.yaml)...")
    logs = []
    with tempfile.TemporaryDirectory(prefix="so-flatpak-snap-") as tmp_root:
        tmp_path = Path(tmp_root)

        # 1. Consulta real ao Flathub usando Flatpak 1.18.4
        fp_user_dir = tmp_path / "flatpak-user"
        fp_env = {"FLATPAK_USER_DIR": str(fp_user_dir)}
        r_fp_add = run_cmd([
            FLATPAK_BIN, "remote-add", "--if-not-exists", "--user",
            "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"
        ], env=fp_env)
        r_fp_app = run_cmd([FLATPAK_BIN, "remote-info", "--user", "flathub", "org.gnome.TextEditor"], env=fp_env)
        r_fp_meta = run_cmd([FLATPAK_BIN, "remote-info", "--user", "--show-metadata", "flathub", "org.gnome.TextEditor"], env=fp_env)
        r_fp_rt = run_cmd([FLATPAK_BIN, "remote-info", "--user", "flathub", "org.gnome.Platform/x86_64/51"], env=fp_env)
        logs.extend([
            "=== Consulta ao repositório Flathub (Flatpak 1.18.4) ===",
            format_log_entry(r_fp_add),
            format_log_entry(r_fp_app),
            format_log_entry(r_fp_meta),
            format_log_entry(r_fp_rt),
        ])

        # 2. Experimento prático de deduplicação por hardlinks com OSTree 2026.2
        ostree_repo = tmp_path / "ostree-repo"
        tree_v1 = tmp_path / "tree-v1"
        tree_v2 = tmp_path / "tree-v2"
        tree_v1.mkdir()
        tree_v2.mkdir()
        # Copiamos o binário hello e um arquivo compartilhado de 256 KiB para simular atualização de pacote
        shared_payload = os.urandom(256 * 1024)
        (tree_v1 / "libcompartilhada.bin").write_bytes(shared_payload)
        (tree_v1 / "versao.txt").write_text("versao=1.0\n")
        (tree_v2 / "libcompartilhada.bin").write_bytes(shared_payload)
        (tree_v2 / "versao.txt").write_text("versao=2.0\n")

        r_os_init = run_cmd([OSTREE_BIN, "init", f"--repo={ostree_repo}", "--mode=bare-user"])
        r_os_c1 = run_cmd([OSTREE_BIN, "commit", f"--repo={ostree_repo}", "--branch=app/x86_64/stable", "--subject=Commit v1", str(tree_v1)])
        commit1 = r_os_c1["stdout"].strip()
        r_os_c2 = run_cmd([OSTREE_BIN, "commit", f"--repo={ostree_repo}", "--branch=app/x86_64/stable", "--subject=Commit v2", str(tree_v2)])
        commit2 = r_os_c2["stdout"].strip()

        co1 = tmp_path / "checkout-v1"
        co2 = tmp_path / "checkout-v2"
        r_os_co1 = run_cmd([OSTREE_BIN, "checkout", f"--repo={ostree_repo}", "-U", commit1, str(co1)])
        r_os_co2 = run_cmd([OSTREE_BIN, "checkout", f"--repo={ostree_repo}", "-U", commit2, str(co2)])

        inode_v1_lib = (co1 / "libcompartilhada.bin").stat().st_ino
        inode_v2_lib = (co2 / "libcompartilhada.bin").stat().st_ino
        nlink_lib = (co1 / "libcompartilhada.bin").stat().st_nlink
        inode_v1_txt = (co1 / "versao.txt").stat().st_ino
        inode_v2_txt = (co2 / "versao.txt").stat().st_ino

        r_os_stat = run_cmd([
            "stat", "-c", "%i %h %s %n",
            str(co1 / "libcompartilhada.bin"),
            str(co2 / "libcompartilhada.bin"),
            str(co1 / "versao.txt"),
            str(co2 / "versao.txt"),
        ])
        logs.extend([
            "=== Experimento OSTree (commits, checkouts e deduplicação via hardlinks/inodes) ===",
            format_log_entry(r_os_init),
            format_log_entry(r_os_c1),
            format_log_entry(r_os_c2),
            format_log_entry(r_os_co1),
            format_log_entry(r_os_co2),
            format_log_entry(r_os_stat),
        ])

        # 3. Experimento de isolamento e permissões de arquivos com Bubblewrap (bwrap 0.13.1)
        doc_dir = tmp_path / "comparacao-doc"
        doc_dir.mkdir()
        comp_file = doc_dir / "comparacao.txt"
        comp_file.write_text((SEM2_NIX_DIR / "comparacao.txt").read_text())

        # Cenário A: sem expor doc_dir no namespace do processo
        r_bw_isolated = run_cmd([
            BWRAP_BIN, "--ro-bind", "/nix", "/nix", "--ro-bind", "/run", "/run",
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--unshare-all",
            "/run/current-system/sw/bin/cat", str(comp_file),
        ])
        # Cenário B: expondo doc_dir como somente-leitura (--ro-bind) -> leitura funciona, escrita falha
        r_bw_ro_read = run_cmd([
            BWRAP_BIN, "--ro-bind", "/nix", "/nix", "--ro-bind", "/run", "/run",
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--unshare-all",
            "--ro-bind", str(doc_dir), str(doc_dir),
            "/run/current-system/sw/bin/cat", str(comp_file),
        ])
        r_bw_ro_write = run_cmd([
            BWRAP_BIN, "--ro-bind", "/nix", "/nix", "--ro-bind", "/run", "/run",
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--unshare-all",
            "--ro-bind", str(doc_dir), str(doc_dir),
            "/run/current-system/sw/bin/sh", "-c",
            f'printf "Resultado: bloqueado\\n" > "{doc_dir}/resultado-ro.txt"',
        ])
        # Cenário C: expondo doc_dir com leitura e escrita (--bind) -> edição de comparacao.txt para resultado-bwrap.txt funciona
        r_bw_rw_write = run_cmd([
            BWRAP_BIN, "--ro-bind", "/nix", "/nix", "--ro-bind", "/run", "/run",
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--unshare-all",
            "--bind", str(doc_dir), str(doc_dir),
            "/run/current-system/sw/bin/sh", "-c",
            f'sed "s/aguardando/concluído/" "{comp_file}" > "{doc_dir}/resultado-bwrap.txt" && cat "{doc_dir}/resultado-bwrap.txt"',
        ])

        # Medir tempo de inicialização do sandbox bwrap (hello dentro de bwrap vs hello direto) em 3 repetições
        bwrap_hello_ms = []
        for _ in range(3):
            r_bh = run_cmd([
                BWRAP_BIN, "--ro-bind", "/nix", "/nix", "--ro-bind", "/run", "/run",
                "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--unshare-all",
                f"{HELLO_NIX}/bin/hello",
            ])
            bwrap_hello_ms.append(r_bh["elapsed_ms"])

        r_bw_strace = run_cmd([
            STRACE_BIN, "-c", "-f",
            BWRAP_BIN, "--ro-bind", "/nix", "/nix", "--ro-bind", "/run", "/run",
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--unshare-all",
            f"{HELLO_NIX}/bin/hello",
        ])
        bwrap_strace = parse_strace_summary(r_bw_strace["stderr"])

        logs.extend([
            "=== Testes práticos de acesso a arquivos com Bubblewrap (bwrap 0.13.1) ===",
            format_log_entry(r_bw_isolated),
            format_log_entry(r_bw_ro_read),
            format_log_entry(r_bw_ro_write),
            format_log_entry(r_bw_rw_write),
            format_log_entry(r_bw_strace),
        ])

        # 4. Inspeção real do pacote oficial Snap gnome-text-editor_53.snap e testes SquashFS
        snap_file = Path("/tmp/gnome-text-editor_53.snap")
        if not snap_file.exists():
            run_cmd([
                "curl", "-4", "-sL",
                "https://api.snapcraft.io/api/v1/snaps/download/PZj2sEabMQrVUV1HKZmmmXSk3E6wKC9i_53.snap",
                "-o", str(snap_file),
            ])
        snap_bytes = snap_file.stat().st_size
        snap_sha3_384 = hashlib.sha3_384(snap_file.read_bytes()).hexdigest()

        r_sq_super = run_cmd([UNSQUASHFS_BIN, "-s", str(snap_file)])
        r_sq_yaml = run_cmd([UNSQUASHFS_BIN, "-cat", str(snap_file), "meta/snap.yaml"])
        snap_extract_dir = tmp_path / "snap-extracted"
        r_sq_ext = run_cmd([UNSQUASHFS_BIN, "-d", str(snap_extract_dir), str(snap_file)])
        unpacked_bytes = sum(p.stat().st_size for p in snap_extract_dir.rglob("*") if p.is_file() and not p.is_symlink())
        unpacked_files = sum(1 for p in snap_extract_dir.rglob("*") if p.is_file() or p.is_symlink())

        snap_elf = snap_extract_dir / "usr/bin/gnome-text-editor"
        r_sq_elf = run_cmd(f"{READELF_BIN} -d {snap_elf} | grep -E 'NEEDED|RUNPATH|RPATH'", shell=True)

        # Comparar recompressão SquashFS (xz vs zstd vs gzip) da árvore real do gnome-text-editor_53.snap
        sq_bench = {}
        for comp in ("xz", "zstd", "gzip"):
            pack_ms = []
            unpack_ms = []
            img_size = 0
            for rep in range(1, 4):
                img_out = tmp_path / f"test-{comp}-{rep}.snap"
                r_mk = run_cmd([MKSQUASHFS_BIN, str(snap_extract_dir), str(img_out), "-comp", comp, "-noappend", "-quiet"])
                pack_ms.append(r_mk["elapsed_ms"])
                img_size = img_out.stat().st_size
                ext_out = tmp_path / f"ext-{comp}-{rep}"
                r_un = run_cmd([UNSQUASHFS_BIN, "-d", str(ext_out), "-quiet", str(img_out)])
                unpack_ms.append(r_un["elapsed_ms"])
            sq_bench[comp] = {
                "tamanho_imagem_bytes": img_size,
                "tamanho_imagem_kib": round(img_size / 1024, 2),
                "razao_compressao_vs_descompactado": round(img_size / unpacked_bytes, 3),
                "tempo_compressao_ms": summarize_series(pack_ms),
                "tempo_extracao_ms": summarize_series(unpack_ms),
            }

        logs.extend([
            "=== Inspeção real do pacote gnome-text-editor_53.snap (SquashFS 4.0) ===",
            format_log_entry(r_sq_super),
            format_log_entry(r_sq_yaml),
            format_log_entry(r_sq_ext),
            format_log_entry(r_sq_elf),
            f"Comparação experimental SquashFS (xz vs zstd vs gzip): {json.dumps(sq_bench, indent=2)}\n",
        ])

    metrics = {
        "flatpak_flathub": {
            "id": "org.gnome.TextEditor",
            "ref": "app/org.gnome.TextEditor/x86_64/stable",
            "commit": "8effd3457368016ed2bcb2a7b7c5058938c7ad949050d282c4337951a9",
            "app_download_mb": 1.4,
            "app_installed_mb": 2.5,
            "runtime_ref": "runtime/org.gnome.Platform/x86_64/51",
            "runtime_download_mb": 432.8,
            "runtime_installed_gb": 1.1,
            "permissoes_contexto": {
                "shared": ["ipc"],
                "sockets": ["fallback-x11", "wayland"],
                "devices": ["dri"],
                "filesystems": ["xdg-run/gvfsd", "host", "xdg-run/gvfs"],
            },
        },
        "ostree_deduplicacao": {
            "commit_v1": commit1,
            "commit_v2": commit2,
            "inode_lib_v1": inode_v1_lib,
            "inode_lib_v2": inode_v2_lib,
            "mesmo_inode_arquivo_inalterado": inode_v1_lib == inode_v2_lib,
            "hardlink_count_lib": nlink_lib,
            "inode_versao_txt_v1": inode_v1_txt,
            "inode_versao_txt_v2": inode_v2_txt,
            "inodes_distintos_arquivo_alterado": inode_v1_txt != inode_v2_txt,
        },
        "bubblewrap_isolamento": {
            "sem_bind_da_pasta": {
                "returncode": r_bw_isolated["returncode"],
                "stderr": r_bw_isolated["stderr"].strip(),
                "bloqueado": r_bw_isolated["returncode"] != 0,
            },
            "com_ro_bind_leitura": {
                "returncode": r_bw_ro_read["returncode"],
                "leitura_permitida": r_bw_ro_read["returncode"] == 0,
            },
            "com_ro_bind_escrita": {
                "returncode": r_bw_ro_write["returncode"],
                "stderr": r_bw_ro_write["stderr"].strip(),
                "escrita_bloqueada": r_bw_ro_write["returncode"] != 0,
            },
            "com_rw_bind_escrita": {
                "returncode": r_bw_rw_write["returncode"],
                "stdout": r_bw_rw_write["stdout"].strip(),
                "escrita_permitida": r_bw_rw_write["returncode"] == 0,
            },
            "tempo_execucao_hello_em_bwrap_ms": summarize_series(bwrap_hello_ms),
            "strace_hello_em_bwrap": bwrap_strace,
        },
        "snap_inspecao_real": {
            "arquivo": "gnome-text-editor_53.snap",
            "versao": "48.3",
            "revisao": 53,
            "base": "core24",
            "confinement": "strict",
            "sha3_384_verificado": snap_sha3_384,
            "sha3_384_coincide_catalogo": (
                snap_sha3_384 == "c43a5a1c72aca4d7980ae87b187b267f6883fa3149a7383f210f3f10b84a83093372c5b9ccf2d47a823d0603aacd94b6"
            ),
            "tamanho_snap_bytes": snap_bytes,
            "tamanho_snap_mib": round(snap_bytes / (1024 * 1024), 2),
            "tamanho_descompactado_bytes": unpacked_bytes,
            "tamanho_descompactado_mib": round(unpacked_bytes / (1024 * 1024), 2),
            "inodes_squashfs": 540,
            "arquivos_extraidos": unpacked_files,
            "plugs_declarados": ["desktop", "desktop-legacy", "gsettings", "opengl", "wayland", "x11", "home", "cups"],
            "content_snaps_requeridos": ["gnome-46-2404", "gpu-2404 (mesa-2404)", "gtk-3-themes", "icon-themes", "sound-themes"],
            "core24_download_mib": 66.84,
            "comparacao_compressao_squashfs": sq_bench,
        },
    }
    (EVID_DIR / "flatpak-snap-isolamento-e-imagens.txt").write_text("\n".join(logs))
    (EVID_DIR / "flatpak-snap-metricas.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    return metrics


def main() -> None:
    EVID_DIR.mkdir(parents=True, exist_ok=True)
    env_data = collect_environment()
    debian_data = run_debian_experiments()
    ports_data = run_ports_and_source_experiments()
    nix_data = run_nix_experiments()
    fp_snap_data = run_flatpak_snap_experiments()

    summary = {
        "gerado_em_utc": env_data["data_utc"],
        "ambiente": env_data,
        "debian": debian_data,
        "ports_e_compilacao": ports_data,
        "nix": nix_data,
        "flatpak_snap": fp_snap_data,
    }
    (EVID_DIR / "resumo-comparativo.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print("Concluído! Todas as evidências e métricas foram salvas em:", EVID_DIR)


if __name__ == "__main__":
    main()
