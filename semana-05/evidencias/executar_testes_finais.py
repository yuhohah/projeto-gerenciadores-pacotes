#!/usr/bin/env python3
"""Bateria automatizada de testes finais (Semana 5) — GNOME Text Editor, VLC e Blender.

Compara cinco representantes em quatro famílias de gerenciadores de pacotes sob a ótica
de Sistemas Operacionais a partir de um único hospedeiro NixOS:
  1. Debian (APT/dpkg) em container oficial debian:trixie-slim (Docker)
  2. FreeBSD Ports (inspeção estrutural oficial de Makefile/distinfo/OPTIONS + build opcional do fonte)
  3. Nix (store imutável, NAR vs. closure, deduplicação entre fechamentos, RUNPATH/wrappers,
     perfis, rollback atômico e execução das cargas reais)
  4. Flatpak (metadados/permissões reais no Flathub, deduplicação por hardlinks no OSTree e
     isolamento/sobrecarga de execução real no Bubblewrap)
  5. Snap (metadados oficiais via API v2 da Snap Store — strict vs. classic — inspeção de
     pacotes .snap reais, meta/snap.yaml, ELF, benchmark SquashFS xz/zstd/gzip e LSM do kernel)

Uso:
  python3 semana-05/evidencias/executar_testes_finais.py --dry-run
  python3 semana-05/evidencias/executar_testes_finais.py
  python3 semana-05/evidencias/executar_testes_finais.py --only env,nix,flatpak --reps 3
"""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import wave

EVID_DIR = Path(__file__).resolve().parent
DEFAULT_CACHE_DIR = Path("/tmp/so-semana05-cache")

ALL_STAGES = ("env", "debian", "ports", "nix", "flatpak", "snap")

# Alinhamento de versões pela Opção A (referência: Debian trixie-slim)
#   - gnome-text-editor : 48.3  (Debian 48.3-3 | Nix nixos-25.05 48.3 | Snap latest/stable 48.3 | Ports main 47.4*)
#   - vlc               : 3.0.24 (Debian 3.0.24 | Nix nixpkgs 3.0.24 | Snap latest/stable 3.0.24-rc1 | Ports main 3.0.24 | Flathub 3.0.24)
#   - blender           : 4.3.2 (Debian 4.3.2 | Nix 12be955b 4.3.2 | Snap 4.3/stable 4.3.1 | Ports 12fd1e26 4.2.0*)
#   (*) versão mais próxima existente na árvore histórica do FreeBSD Ports
NIXPKGS_REV_GTE_48_3 = "ac62194c3917d5f474c1a844b6fd6da2db95077d"   # nixos-25.05 (gnome-text-editor 48.3, cached)
NIXPKGS_REV_BLENDER_4_3_2 = "12be955b9e3e029f0c6274122b5fc040324f898a"  # nixpkgs blender 4.3.2 (cached)
FREEBSD_REV_BLENDER_4_2_0 = "12fd1e2633db4c76fa18fa17d983ebe79bb03ff7"  # último 4.x antes do salto para 5.0.1

APPS: dict[str, dict] = {
    "gnome-text-editor": {
        "titulo": "GNOME Text Editor",
        "categoria": "Editor gráfico GTK4/Libadwaita (porte leve-médio)",
        "versao_alvo_debian": "48.3",
        "debian_pkg": "gnome-text-editor",
        "debian_bin": "/usr/bin/gnome-text-editor",
        "freebsd_port": "editors/gnome-text-editor",
        "freebsd_ref_aligned": "main",
        "nix_attr": "gnome-text-editor",
        "nix_flake_aligned": f"github:NixOS/nixpkgs/{NIXPKGS_REV_GTE_48_3}#gnome-text-editor",
        "nix_bin_rel": "bin/gnome-text-editor",
        "flatpak_id": "org.gnome.TextEditor",
        "snap_name": "gnome-text-editor",
        "snap_channel_aligned": "latest/stable",
        "snap_bin_candidates": [
            "usr/bin/gnome-text-editor",
            "bin/gnome-text-editor",
        ],
        "snap_extra_bench_paths": [],
    },
    "vlc": {
        "titulo": "VLC Media Player",
        "categoria": "Multimídia e transcodificação (porte médio-pesado)",
        "versao_alvo_debian": "3.0.24",
        "debian_pkg": "vlc",
        "debian_bin": "/usr/bin/vlc",
        "freebsd_port": "multimedia/vlc",
        "freebsd_ref_aligned": "main",
        "nix_attr": "vlc",
        "nix_flake_aligned": "nixpkgs#vlc",
        "nix_bin_rel": "bin/vlc",
        "flatpak_id": "org.videolan.VLC",
        "snap_name": "vlc",
        "snap_channel_aligned": "latest/stable",
        "snap_bin_candidates": [
            "usr/bin/vlc",
            "bin/vlc",
        ],
        "snap_extra_bench_paths": ["usr/lib/vlc"],
    },
    "blender": {
        "titulo": "Blender",
        "categoria": "Modelagem e renderização 3D (porte muito pesado)",
        "versao_alvo_debian": "4.3.2",
        "debian_pkg": "blender",
        "debian_bin": "/usr/bin/blender",
        "freebsd_port": "graphics/blender",
        "freebsd_ref_aligned": FREEBSD_REV_BLENDER_4_2_0,
        "nix_attr": "blender",
        "nix_flake_aligned": f"github:NixOS/nixpkgs/{NIXPKGS_REV_BLENDER_4_3_2}#blender",
        "nix_bin_rel": "bin/blender",
        "flatpak_id": "org.blender.Blender",
        "snap_name": "blender",
        "snap_channel_aligned": "4.3/stable",
        "snap_bin_candidates": [
            "blender",
            "usr/bin/blender",
            "bin/blender",
        ],
        "snap_extra_bench_paths": [],
    },
}

# Script Python inline para renderização 3D determinística e 100% headless no Blender (Cycles CPU)
BLENDER_RENDER_EXPR = (
    "import bpy, sys; "
    "out = sys.argv[-1]; "
    "s = bpy.context.scene; "
    "s.render.engine = 'CYCLES'; "
    "s.cycles.device = 'CPU'; "
    "s.cycles.samples = 4; "
    "s.cycles.use_denoising = False; "
    "s.render.resolution_x = 320; "
    "s.render.resolution_y = 240; "
    "s.render.resolution_percentage = 100; "
    "s.render.threads_mode = 'FIXED'; "
    "s.render.threads = 4; "
    "s.render.image_settings.file_format = 'PNG'; "
    "s.render.filepath = out; "
    "bpy.ops.render.render(write_still=True)"
)


GNU_TIME_FMT = (
    '{"wall_s":%e,"user_s":%U,"sys_s":%S,"cpu_pct":"%P",'
    '"max_rss_kib":%M,"minor_faults":%R,"major_faults":%F,'
    '"vol_ctx":%w,"invol_ctx":%c}'
)


def parse_gnu_time_json(raw_text: str) -> dict | None:
    """Converte a linha JSON emitida pelo GNU time (-f GNU_TIME_FMT) em métricas estruturadas."""
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.startswith("{") and ln.endswith("}"):
            try:
                data = json.loads(ln)
            except json.JSONDecodeError:
                continue
            raw_pct = str(data.get("cpu_pct", "")).strip()
            cpu_pct: float | None = None
            if raw_pct.endswith("%"):
                try:
                    cpu_pct = float(raw_pct[:-1])
                except ValueError:
                    cpu_pct = None
            max_rss_kib = int(data.get("max_rss_kib", 0))
            user_s = float(data.get("user_s", 0.0))
            sys_s = float(data.get("sys_s", 0.0))
            return {
                "wall_s": float(data.get("wall_s", 0.0)),
                "cpu_user_s": user_s,
                "cpu_sys_s": sys_s,
                "cpu_total_s": round(user_s + sys_s, 4),
                "cpu_pct": cpu_pct,
                "max_rss_kib": max_rss_kib,
                "max_rss_mib": round(max_rss_kib / 1024.0, 2),
                "minor_faults": int(data.get("minor_faults", 0)),
                "major_faults": int(data.get("major_faults", 0)),
                "vol_ctx": int(data.get("vol_ctx", 0)),
                "invol_ctx": int(data.get("invol_ctx", 0)),
            }
    return None


def run_cmd(
    cmd: list[str] | str,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    shell: bool = False,
    timeout: int | None = None,
) -> dict:
    """Executa comando com cronômetro monotônico e captura stdout/stderr."""
    merged_env = os.environ.copy()
    merged_env["LC_ALL"] = "C.UTF-8"
    if env:
        merged_env.update(env)
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=merged_env,
            shell=shell,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc = 124
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = ((exc.stderr or "") if isinstance(exc.stderr, str) else "") + f"\n[TIMEOUT após {timeout}s]"
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "cmd": cmd if isinstance(cmd, str) else " ".join(cmd),
        "returncode": rc,
        "stdout": stdout,
        "stderr": stderr,
        "elapsed_ms": round(elapsed_ms, 2),
    }


def run_cmd_timed(
    time_bin: str | None,
    cmd: list[str],
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
) -> dict:
    """Executa comando instrumentado com GNU time para coletar RAM (Max RSS), CPU, page faults e ctx switches."""
    if not time_bin:
        res = run_cmd(cmd, cwd=cwd, env=env, timeout=timeout)
        res["rusage"] = None
        return res
    fd, out_file = tempfile.mkstemp(prefix="so-s5-time-", suffix=".json")
    os.close(fd)
    rusage_path = Path(out_file)
    try:
        res = run_cmd(
            [time_bin, "-f", GNU_TIME_FMT, "-o", str(rusage_path), *cmd],
            cwd=cwd,
            env=env,
            timeout=timeout,
        )
        res["cmd"] = " ".join(cmd)
        raw = rusage_path.read_text(errors="replace") if rusage_path.exists() else ""
        res["rusage"] = parse_gnu_time_json(raw)
        return res
    finally:
        if rusage_path.exists():
            rusage_path.unlink()


def format_log_entry(res: dict, max_chars: int = 12000) -> str:
    """Formata entrada de log preservando início e fim se muito longa."""
    def _clip(text: str) -> str:
        text = text.rstrip()
        if len(text) <= max_chars:
            return text
        half = max_chars // 2
        return text[:half] + f"\n... [truncado: {len(text)} chars totais] ...\n" + text[-half:]

    out = [f"$ {res['cmd']}"]
    if res["stdout"].strip():
        out.append(_clip(res["stdout"]))
    if res["stderr"].strip():
        out.append("[stderr]\n" + _clip(res["stderr"]))
    ru = res.get("rusage")
    ru_str = ""
    if isinstance(ru, dict):
        pct = f"{ru['cpu_pct']:.0f}%" if ru.get("cpu_pct") is not None else "n/a"
        ru_str = (
            f" | Max RSS: {ru['max_rss_mib']:.2f} MiB"
            f" | CPU user/sys: {ru['cpu_user_s']:.2f}s/{ru['cpu_sys_s']:.2f}s ({pct})"
            f" | Faults min/maj: {ru['minor_faults']}/{ru['major_faults']}"
        )
    out.append(f"[Código de saída: {res['returncode']} | Tempo: {res['elapsed_ms']:.2f} ms{ru_str}]\n")
    return "\n".join(out)


def summarize_series(values: list[float]) -> dict:
    """Resume uma série de medições (repetições, média, mediana, desvio-padrão)."""
    if not values:
        return {"repeticoes": [], "media": None, "mediana": None, "desvio_padrao": None}
    return {
        "repeticoes": [round(v, 2) for v in values],
        "media": round(statistics.mean(values), 2),
        "mediana": round(statistics.median(values), 2),
        "desvio_padrao": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
    }


def summarize_rusage_series(samples: list[dict | None]) -> dict:
    """Resume séries de RAM (Max RSS), CPU (user/sys/%), page faults e trocas de contexto."""
    valid = [s for s in samples if isinstance(s, dict)]
    if not valid:
        return {"amostras_validas": 0}
    cpu_pcts = [float(s["cpu_pct"]) for s in valid if s.get("cpu_pct") is not None]
    return {
        "amostras_validas": len(valid),
        "max_rss_kib": summarize_series([float(s["max_rss_kib"]) for s in valid]),
        "max_rss_mib": summarize_series([float(s["max_rss_mib"]) for s in valid]),
        "cpu_user_s": summarize_series([float(s["cpu_user_s"]) for s in valid]),
        "cpu_sys_s": summarize_series([float(s["cpu_sys_s"]) for s in valid]),
        "cpu_total_s": summarize_series([float(s["cpu_total_s"]) for s in valid]),
        "cpu_pct": summarize_series(cpu_pcts),
        "minor_faults": summarize_series([float(s["minor_faults"]) for s in valid]),
        "major_faults": summarize_series([float(s["major_faults"]) for s in valid]),
        "vol_ctx": summarize_series([float(s["vol_ctx"]) for s in valid]),
        "invol_ctx": summarize_series([float(s["invol_ctx"]) for s in valid]),
    }


def parse_strace_summary(stderr_text: str) -> dict:
    """Extrai total de chamadas, erros e mapa de syscalls da tabela `strace -c`."""
    lines = stderr_text.splitlines()
    syscalls: dict[str, dict[str, int]] = {}
    total_calls = 0
    total_errors = 0
    in_table = False
    for line in lines:
        if "------" in line:
            in_table = not in_table
            continue
        if in_table:
            parts = line.split()
            if len(parts) >= 5 and parts[3].isdigit():
                calls = int(parts[3])
                if len(parts) == 6 and parts[4].isdigit():
                    errors = int(parts[4])
                    name = parts[5]
                else:
                    errors = 0
                    name = parts[4]
                syscalls[name] = {"calls": calls, "errors": errors}
        elif line.strip().startswith("100.00"):
            parts = line.split()
            if len(parts) >= 5 and parts[3].isdigit():
                total_calls = int(parts[3])
                if len(parts) >= 6 and parts[4].isdigit():
                    total_errors = int(parts[4])
    return {
        "total_calls": total_calls,
        "total_errors": total_errors,
        "syscalls": syscalls,
    }


def parse_readelf_dynamic(text: str) -> dict:
    """Extrai NEEDED, RUNPATH e RPATH da saída de `readelf -d`."""
    needed: list[str] = []
    runpath: list[str] = []
    rpath: list[str] = []
    for line in text.splitlines():
        m_need = re.search(r"\(NEEDED\)\s+Shared library:\s+\[([^\]]+)\]", line)
        if m_need:
            needed.append(m_need.group(1))
        m_run = re.search(r"\(RUNPATH\)\s+Library runpath:\s+\[([^\]]+)\]", line)
        if m_run:
            runpath.extend([p for p in m_run.group(1).split(":") if p])
        m_rp = re.search(r"\(RPATH\)\s+Library rpath:\s+\[([^\]]+)\]", line)
        if m_rp:
            rpath.extend([p for p in m_rp.group(1).split(":") if p])
    return {
        "needed_count": len(needed),
        "needed": needed,
        "runpath_count": len(runpath),
        "runpath": runpath,
        "rpath": rpath,
    }


def generate_test_wav(dest: Path, duration_s: float = 2.0, freq_hz: float = 440.0, rate: int = 44100) -> dict:
    """Gera arquivo WAV senoidal determinístico para o workload real do VLC."""
    n_samples = int(duration_s * rate)
    amp = 16000
    dest.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dest), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        frames = bytearray()
        for i in range(n_samples):
            val = int(amp * math.sin(2.0 * math.pi * freq_hz * i / rate))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(bytes(frames))
    return {
        "arquivo": str(dest),
        "duracao_s": duration_s,
        "frequencia_hz": freq_hz,
        "sample_rate_hz": rate,
        "tamanho_bytes": dest.stat().st_size,
    }


def http_get_text(url: str, headers: dict[str, str] | None = None, timeout: int = 30) -> tuple[int, str]:
    """Efetua GET HTTP usando urllib com cabeçalhos opcionais."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, f"Erro HTTP: {exc}"


class ToolResolver:
    """Resolve ferramentas do hospedeiro (PATH -> /nix/store existente -> nix build)."""

    TOOL_SPECS = {
        "nix": ("nix", "nix", "bin/nix"),
        "docker": ("docker", "docker", "bin/docker"),
        "curl": ("curl", "curl", "bin/curl"),
        "ldd": ("ldd", "glibc", "bin/ldd"),
        "flatpak": ("flatpak", "flatpak", "bin/flatpak"),
        "bwrap": ("bubblewrap", "bubblewrap", "bin/bwrap"),
        "ostree": ("ostree", "ostree", "bin/ostree"),
        "mksquashfs": ("squashfsTools", "squashfs-tools", "bin/mksquashfs"),
        "unsquashfs": ("squashfsTools", "squashfs-tools", "bin/unsquashfs"),
        "strace": ("strace", "strace", "bin/strace"),
        "readelf": ("binutils-unwrapped", "binutils", "bin/readelf"),
        "time": ("time", "time", "bin/time"),
    }

    def __init__(self, allow_nix_build: bool = True) -> None:
        self.allow_nix_build = allow_nix_build
        self._cache: dict[str, str | None] = {}

    def _find_in_nix_store(self, store_hint: str, rel_bin: str) -> str | None:
        pattern = f"/nix/store/*-{store_hint}-[0-9]*/{rel_bin}"
        candidates = [
            p for p in glob.glob(pattern)
            if ".drv" not in p and os.path.isfile(p) and os.access(p, os.X_OK)
        ]
        if not candidates:
            pattern_loose = f"/nix/store/*-{store_hint}*/{rel_bin}"
            candidates = [
                p for p in glob.glob(pattern_loose)
                if ".drv" not in p and "-wrapper-" not in p and os.path.isfile(p) and os.access(p, os.X_OK)
            ]
        if candidates:
            # Preferir o caminho com mtime mais recente no store
            candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return candidates[0]
        return None

    def get(self, name: str, required: bool = False) -> str | None:
        if name in self._cache:
            val = self._cache[name]
            if required and not val:
                raise RuntimeError(f"Ferramenta obrigatória indisponível: {name}")
            return val

        # 1. PATH (resolvendo symlinks para /nix/store/... para compatibilidade com mounts no Docker)
        in_path = shutil.which(name)
        if in_path:
            resolved = os.path.realpath(in_path)
            self._cache[name] = resolved
            return resolved

        # 2. /nix/store já presente
        spec = self.TOOL_SPECS.get(name)
        if spec:
            nix_attr, store_hint, rel_bin = spec
            found = self._find_in_nix_store(store_hint, rel_bin)
            if found:
                self._cache[name] = found
                return found

            # 3. Realização sob demanda via nix build (apenas fora do --dry-run)
            if self.allow_nix_build and shutil.which("nix"):
                res = run_cmd([
                    "nix", "build", f"nixpkgs#{nix_attr}",
                    "--no-link", "--print-out-paths",
                ])
                if res["returncode"] == 0:
                    for out_path in res["stdout"].strip().splitlines():
                        candidate = Path(out_path.strip()) / rel_bin
                        if candidate.is_file() and os.access(candidate, os.X_OK):
                            self._cache[name] = str(candidate)
                            return str(candidate)

        self._cache[name] = None
        if required:
            raise RuntimeError(f"Ferramenta obrigatória indisponível: {name}")
        return None

    def snapshot(self) -> dict[str, str | None]:
        return {k: self.get(k, required=False) for k in self.TOOL_SPECS}


# =============================================================================
# 1. AMBIENTE EXPERIMENTAL
# =============================================================================

def collect_environment(tools: ToolResolver) -> dict:
    print("[1/6] Coletando informações do ambiente experimental...")
    uname = run_cmd(["uname", "-a"])
    nixos_ver = run_cmd(["nixos-version", "--json"])
    lscpu = run_cmd("lscpu | grep -E 'Architecture|Model name|CPU\\(s\\):|Thread|Core'", shell=True)
    mem = run_cmd(["free", "-b"])
    df = run_cmd(["df", "-B1", "/"])
    lsm = Path("/sys/kernel/security/lsm").read_text().strip() if Path("/sys/kernel/security/lsm").exists() else "indisponível"
    cgroups = (
        Path("/sys/fs/cgroup/cgroup.controllers").read_text().strip()
        if Path("/sys/fs/cgroup/cgroup.controllers").exists()
        else "indisponível"
    )

    resolved = tools.snapshot()
    versions: dict[str, str] = {}
    version_cmds = {
        "nix": (resolved.get("nix"), ["--version"]),
        "docker": (resolved.get("docker"), ["--version"]),
        "flatpak": (resolved.get("flatpak"), ["--version"]),
        "bubblewrap": (resolved.get("bwrap"), ["--version"]),
        "ostree": (resolved.get("ostree"), ["--version"]),
        "squashfs_tools": (resolved.get("mksquashfs"), ["-version"]),
        "strace": (resolved.get("strace"), ["--version"]),
        "readelf": (resolved.get("readelf"), ["--version"]),
        "gnu_time": (resolved.get("time"), ["--version"]),
    }
    for label, (bin_path, flags) in version_cmds.items():
        if bin_path:
            r = run_cmd([bin_path, *flags])
            lines = [ln.strip() for ln in r["stdout"].splitlines() if ln.strip()]
            versions[label] = " | ".join(lines[:2]) if label == "ostree" else (lines[0] if lines else "desconhecida")
        else:
            versions[label] = "indisponível"

    nixos_json = {}
    if nixos_ver["returncode"] == 0 and nixos_ver["stdout"].strip():
        try:
            nixos_json = json.loads(nixos_ver["stdout"])
        except json.JSONDecodeError:
            nixos_json = {"raw": nixos_ver["stdout"].strip()}

    env_data = {
        "data_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data_local": datetime.datetime.now().astimezone().isoformat(),
        "uname": uname["stdout"].strip(),
        "nixos": nixos_json,
        "lscpu": lscpu["stdout"].strip(),
        "lsm_ativos": lsm,
        "apparmor_ativo_no_kernel": "apparmor" in lsm.split(","),
        "cgroup_v2_controllers": cgroups,
        "caminhos_ferramentas": resolved,
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
        "Versões das ferramentas:\n" + json.dumps(versions, indent=2, ensure_ascii=False) + "\n",
    ])
    (EVID_DIR / "ambiente-experimental.txt").write_text(log_txt)
    return env_data


# =============================================================================
# 2. DEBIAN (APT/dpkg) EM CONTAINER debian:trixie-slim
# =============================================================================

def _prepare_debian_workload(app_key: str, app_bin: str, time_bin: str, rep_work: Path) -> str:
    """Prepara arquivos auxiliares em rep_work e retorna snippet bash instrumentado com GNU time."""
    if app_key == "gnome-text-editor":
        return f'"{time_bin}" -f \'{GNU_TIME_FMT}\' -o /tmp/work/time-workload.json "{app_bin}" --version >/dev/null'
    if app_key == "vlc":
        # VLC recusa executar como root; usamos um script auxiliar rodado como usuário 'nobody'
        vlc_script = rep_work / "run-vlc.sh"
        vlc_script.write_text(
            "#!/bin/sh\n"
            f'"{time_bin}" -f \'{GNU_TIME_FMT}\' -o /tmp/work/time-workload.json '
            f'"{app_bin}" -I dummy --no-video --aout=dummy --play-and-exit /tmp/work/in.wav '
            '--sout \'#transcode{acodec=vorb,ab=128,channels=1,samplerate=44100}:'
            'std{access=file,mux=ogg,dst=/tmp/work/out.ogg}\' vlc://quit >/dev/null 2>&1\n'
            'if [ ! -s /tmp/work/out.ogg ]; then\n'
            f'  "{time_bin}" -f \'{GNU_TIME_FMT}\' -o /tmp/work/time-workload.json '
            f'"{app_bin}" -I dummy --no-video --aout=dummy --play-and-exit /tmp/work/in.wav '
            '--sout \'#transcode{acodec=s16l,channels=1,samplerate=44100}:'
            'std{access=file,mux=wav,dst=/tmp/work/out.wav}\' vlc://quit >/dev/null 2>&1\n'
            'fi\n'
            'test -s /tmp/work/out.ogg || test -s /tmp/work/out.wav\n'
        )
        os.chmod(vlc_script, 0o755)
        return "chmod 777 /tmp/work && rm -f /tmp/work/out.ogg /tmp/work/out.wav && su -s /bin/sh nobody -c /tmp/work/run-vlc.sh"
    if app_key == "blender":
        escaped = BLENDER_RENDER_EXPR.replace("'", "'\"'\"'")
        return (
            "rm -f /tmp/work/render.png && "
            f'"{time_bin}" -f \'{GNU_TIME_FMT}\' -o /tmp/work/time-workload.json '
            f'"{app_bin}" --background --factory-startup --python-expr \'{escaped}\' -- /tmp/work/render.png >/dev/null 2>&1 && '
            "test -s /tmp/work/render.png"
        )
    raise ValueError(f"App desconhecido: {app_key}")


def run_debian_experiments(
    tools: ToolResolver,
    selected_apps: list[str],
    reps: int,
    cache_dir: Path,
) -> dict:
    print("[2/6] Executando experimentos de Debian (APT/dpkg) em container debian:trixie-slim...")
    docker_bin = tools.get("docker", required=True)
    strace_bin = tools.get("strace", required=True)
    readelf_bin = tools.get("readelf", required=True)
    time_bin = tools.get("time", required=True)
    logs: list[str] = []
    app_results: dict[str, dict] = {}

    deb_cache_root = cache_dir / "debian"
    lists_cache = deb_cache_root / "apt-lists"
    lists_cache.mkdir(parents=True, exist_ok=True)

    # Preparar índices APT uma única vez
    r_lists = run_cmd([
        docker_bin, "run", "--rm",
        "-v", f"{lists_cache}:/lists",
        "debian:trixie-slim", "bash", "-c",
        "set -e; cat /etc/os-release; apt-get --version | head -n 1; dpkg --version | head -n 1; "
        "apt-get update -qq; cp -a /var/lib/apt/lists/. /lists/",
    ])
    logs.append("=== Preparação da imagem base e índices APT (debian:trixie-slim) ===")
    logs.append(format_log_entry(r_lists))

    with tempfile.TemporaryDirectory(prefix="so-s5-debian-work-") as work_root:
        work_path = Path(work_root)
        wav_path = work_path / "in.wav"
        generate_test_wav(wav_path)

        for app_key in selected_apps:
            cfg = APPS[app_key]
            pkg = cfg["debian_pkg"]
            bin_path = cfg["debian_bin"]
            print(f"  -> Debian: {cfg['titulo']} ({pkg})...")

            pkg_cache = deb_cache_root / f"archives-{app_key}"
            pkg_cache.mkdir(parents=True, exist_ok=True)

            # 1. Consulta de metadados, simulação e download offline de toda a árvore de dependências
            dl_script = f"""
set -e
cp -a /lists/. /var/lib/apt/lists/
apt-cache show {pkg} | grep -E '^(Package|Version|Installed-Size|Depends|Recommends):' | head -n 15
echo "--- apt-get install -s --no-install-recommends {pkg} ---"
apt-get install -s --no-install-recommends {pkg} | tail -n 10
apt-get install --download-only --no-install-recommends -y -o Dir::Cache::Archives=/archives {pkg}
"""
            r_dl = run_cmd([
                docker_bin, "run", "--rm",
                "-v", f"{lists_cache}:/lists:ro",
                "-v", f"{pkg_cache}:/archives",
                "debian:trixie-slim", "bash", "-c", dl_script,
            ])
            logs.append(f"=== Debian: download prévio e metadados de {pkg} ===")
            logs.append(format_log_entry(r_dl))

            debs = sorted(pkg_cache.glob("*.deb"))
            download_bytes = sum(p.stat().st_size for p in debs)
            ver_match = re.search(r"^Version:\s*(\S+)", r_dl["stdout"], re.MULTILINE)
            inst_match = re.search(r"^Installed-Size:\s*(\d+)", r_dl["stdout"], re.MULTILINE)

            # 2. N repetições de instalação local offline (--network=none) + execução da carga real (com GNU time)
            install_ms: list[float] = []
            workload_ms: list[float] = []
            install_rusage: list[dict | None] = []
            workload_rusage: list[dict | None] = []

            for rep in range(1, reps + 1):
                rep_work = work_path / f"{app_key}-rep{rep}"
                rep_work.mkdir(parents=True, exist_ok=True)
                shutil.copy2(wav_path, rep_work / "in.wav")
                os.chmod(rep_work, 0o777)
                workload_cmd = _prepare_debian_workload(app_key, bin_path, time_bin, rep_work)

                bench_script = f"""
set -e
export DEBIAN_FRONTEND=noninteractive
cp -a /lists/. /var/lib/apt/lists/
t0=$(date +%s%N)
"{time_bin}" -f '{GNU_TIME_FMT}' -o /tmp/work/time-install.json \
  apt-get install -y --no-download --no-install-recommends -o Dir::Cache::Archives=/archives {pkg} >/dev/null
t1=$(date +%s%N)
echo $(( (t1 - t0) / 1000000 ))
t2=$(date +%s%N)
{workload_cmd}
t3=$(date +%s%N)
echo $(( (t3 - t2) / 1000000 ))
"""
                r_rep = run_cmd([
                    docker_bin, "run", "--rm", "--network=none",
                    "-v", f"{lists_cache}:/lists:ro",
                    "-v", f"{pkg_cache}:/archives:ro",
                    "-v", f"{rep_work}:/tmp/work",
                    "-v", "/nix/store:/nix/store:ro",
                    "debian:trixie-slim", "bash", "-c", bench_script,
                ])
                if r_rep["returncode"] == 0:
                    nums = [float(x) for x in r_rep["stdout"].strip().splitlines()[-2:]]
                    install_ms.append(nums[0])
                    workload_ms.append(nums[1])
                ti_file = rep_work / "time-install.json"
                tw_file = rep_work / "time-workload.json"
                install_rusage.append(parse_gnu_time_json(ti_file.read_text()) if ti_file.exists() else None)
                workload_rusage.append(parse_gnu_time_json(tw_file.read_text()) if tw_file.exists() else None)
                if rep == 1:
                    logs.append(f"=== Debian: repetição 1 (instalação offline + carga real + GNU time) de {pkg} ===")
                    logs.append(format_log_entry(r_rep))
                    if install_rusage[-1]:
                        logs.append("GNU time (instalação): " + json.dumps(install_rusage[-1], ensure_ascii=False) + "\n")
                    if workload_rusage[-1]:
                        logs.append("GNU time (carga real): " + json.dumps(workload_rusage[-1], ensure_ascii=False) + "\n")

            # Verificar saída produzida na repetição 1 (quando houver arquivo gerado)
            rep1_work = work_path / f"{app_key}-rep1"
            workload_artifact: dict[str, object] = {"verificado": bool(workload_ms)}
            if app_key == "vlc":
                out_ogg = rep1_work / "out.ogg"
                out_wav = rep1_work / "out.wav"
                if out_ogg.exists() and out_ogg.stat().st_size > 0:
                    workload_artifact.update({
                        "formato": "ogg/vorbis",
                        "tamanho_bytes": out_ogg.stat().st_size,
                        "magic_ok": out_ogg.read_bytes()[:4] == b"OggS",
                    })
                elif out_wav.exists() and out_wav.stat().st_size > 0:
                    workload_artifact.update({
                        "formato": "wav/pcm",
                        "tamanho_bytes": out_wav.stat().st_size,
                        "magic_ok": out_wav.read_bytes()[:4] == b"RIFF",
                    })
            elif app_key == "blender":
                out_png = rep1_work / "render.png"
                if out_png.exists() and out_png.stat().st_size > 0:
                    workload_artifact.update({
                        "formato": "png",
                        "tamanho_bytes": out_png.stat().st_size,
                        "magic_ok": out_png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n",
                    })

            # 3. strace -c -f da instalação + delta de disco instalado + ELF/FHS + strace da carga real
            trace_work = work_path / f"{app_key}-trace"
            trace_work.mkdir(parents=True, exist_ok=True)
            shutil.copy2(wav_path, trace_work / "in.wav")
            os.chmod(trace_work, 0o777)

            if app_key == "gnome-text-editor":
                trace_wl_cmd = f'{strace_bin} -c -f -o /tmp/work/strace-workload.txt "{bin_path}" --version >/dev/null 2>&1 || true'
            elif app_key == "vlc":
                trace_wl_cmd = (
                    f'{strace_bin} -c -f -u nobody -o /tmp/work/strace-workload.txt '
                    f'"{bin_path}" -I dummy --no-video --aout=dummy --play-and-exit /tmp/work/in.wav '
                    '\'--sout\' \'#transcode{acodec=vorb,ab=128,channels=1,samplerate=44100}:std{access=file,mux=ogg,dst=/tmp/work/out.ogg}\' '
                    'vlc://quit >/dev/null 2>&1 || true'
                )
            else:
                escaped_tr = BLENDER_RENDER_EXPR.replace("'", "'\"'\"'")
                trace_wl_cmd = (
                    f'{strace_bin} -c -f -o /tmp/work/strace-workload.txt '
                    f'"{bin_path}" --background --factory-startup --python-expr \'{escaped_tr}\' -- /tmp/work/render.png >/dev/null 2>&1 || true'
                )

            inspect_script = f"""
set -e
export DEBIAN_FRONTEND=noninteractive
cp -a /lists/. /var/lib/apt/lists/
kib_before=$(dpkg-query -W -f='${{Installed-Size}}\\n' | awk '{{s+=$1}} END {{print s+0}}')
usr_before=$(du -sb /usr | awk '{{print $1}}')
{strace_bin} -c -f apt-get install -y --no-download --no-install-recommends -o Dir::Cache::Archives=/archives {pkg} >/dev/null
kib_after=$(dpkg-query -W -f='${{Installed-Size}}\\n' | awk '{{s+=$1}} END {{print s+0}}')
usr_after=$(du -sb /usr | awk '{{print $1}}')
echo "=== INSTALLED_DELTA_KIB ==="
echo $(( kib_after - kib_before ))
echo "=== USR_DELTA_BYTES ==="
echo $(( usr_after - usr_before ))
echo "=== DPKG_COUNT ==="
dpkg -L {pkg} | wc -l
echo "=== READELF ==="
{readelf_bin} -d {bin_path} | grep -E "NEEDED|RUNPATH|RPATH" || true
echo "=== LDD_COUNT ==="
ldd {bin_path} | wc -l
echo "=== VERSION ==="
"{bin_path}" --version 2>&1 | head -n 3 || true
{trace_wl_cmd}
"""
            r_trace = run_cmd([
                docker_bin, "run", "--rm", "--network=none", "--cap-add=SYS_PTRACE",
                "-v", f"{lists_cache}:/lists:ro",
                "-v", f"{pkg_cache}:/archives:ro",
                "-v", f"{trace_work}:/tmp/work",
                "-v", "/nix/store:/nix/store:ro",
                "debian:trixie-slim", "bash", "-c", inspect_script,
            ])
            logs.append(f"=== Debian: strace da instalação + carga real + ELF/FHS de {pkg} ===")
            logs.append(format_log_entry(r_trace))

            strace_summary = parse_strace_summary(r_trace["stderr"])
            swl_file = trace_work / "strace-workload.txt"
            strace_wl_raw = swl_file.read_text(errors="replace") if swl_file.exists() else ""
            if strace_wl_raw:
                logs.append(f"=== Debian: strace -c -f da carga real ({pkg}) ===\n{strace_wl_raw}\n")
            strace_wl_summary = parse_strace_summary(strace_wl_raw)

            stdout_sections = r_trace["stdout"]
            elf_info = parse_readelf_dynamic(stdout_sections)

            m_dpkg_cnt = re.search(r"=== DPKG_COUNT ===\s+(\d+)", stdout_sections)
            m_ldd_cnt = re.search(r"=== LDD_COUNT ===\s+(\d+)", stdout_sections)
            m_inst_delta = re.search(r"=== INSTALLED_DELTA_KIB ===\s+(\d+)", stdout_sections)
            m_usr_delta = re.search(r"=== USR_DELTA_BYTES ===\s+(\d+)", stdout_sections)
            inst_delta_kib = int(m_inst_delta.group(1)) if m_inst_delta else None
            usr_delta_bytes = int(m_usr_delta.group(1)) if m_usr_delta else None

            app_results[app_key] = {
                "pacote": pkg,
                "versao": ver_match.group(1) if ver_match else "desconhecida",
                "installed_size_pacote_principal_kib": int(inst_match.group(1)) if inst_match else None,
                "installed_size_arvore_total_kib": inst_delta_kib,
                "installed_size_arvore_total_mib": round(inst_delta_kib / 1024.0, 2) if inst_delta_kib is not None else None,
                "delta_usr_bytes": usr_delta_bytes,
                "delta_usr_mib": round(usr_delta_bytes / (1024 * 1024), 2) if usr_delta_bytes is not None else None,
                "quantidade_debs_arvore": len(debs),
                "download_total_bytes": download_bytes,
                "download_total_mib": round(download_bytes / (1024 * 1024), 2),
                "arquivos_dpkg_L_pacote_principal": int(m_dpkg_cnt.group(1)) if m_dpkg_cnt else None,
                "bibliotecas_ldd_total": int(m_ldd_cnt.group(1)) if m_ldd_cnt else None,
                "elf": elf_info,
                "tempo_instalacao_offline_ms": summarize_series(install_ms),
                "recursos_instalacao_offline": summarize_rusage_series(install_rusage),
                "tempo_carga_real_ms": summarize_series(workload_ms),
                "recursos_carga_real": summarize_rusage_series(workload_rusage),
                "carga_real_artefato": workload_artifact,
                "strace_instalacao": strace_summary,
                "strace_carga_real": strace_wl_summary,
            }

    metrics = {
        "ambiente": "Container Docker debian:trixie-slim (instalações limpas com --network=none e cache local de .deb)",
        "aplicacoes": app_results,
    }
    (EVID_DIR / "debian-testes-finais.txt").write_text("\n".join(logs))
    (EVID_DIR / "debian-testes-finais.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    return metrics


# =============================================================================
# 3. FREEBSD PORTS (INSPEÇÃO ESTRUTURAL REAL + BUILD OPCIONAL DO FONTE)
# =============================================================================

def parse_freebsd_makefile(makefile_text: str) -> dict:
    """Extrai metadados estruturais de um Makefile oficial do FreeBSD Ports."""
    # Juntar continuações de linha terminadas por '\'
    logical_lines: list[str] = []
    buf = ""
    for raw in makefile_text.splitlines():
        stripped = raw.rstrip()
        if stripped.startswith("#"):
            continue
        if stripped.endswith("\\"):
            buf += stripped[:-1].strip() + " "
        else:
            buf += stripped
            if buf.strip():
                logical_lines.append(buf.strip())
            buf = ""
    if buf.strip():
        logical_lines.append(buf.strip())

    vars_map: dict[str, list[str]] = {}
    for line in logical_lines:
        m = re.match(r"^([A-Z0-9_]+)\s*(\+?=|\?=|:=)\s*(.*)$", line)
        if m:
            key, op, val = m.group(1), m.group(2), m.group(3).strip()
            tokens = val.split()
            if op == "+=" and key in vars_map:
                vars_map[key].extend(tokens)
            else:
                vars_map[key] = tokens

    def _get_list(key: str) -> list[str]:
        return vars_map.get(key, [])

    def _get_scalar(key: str) -> str | None:
        vals = vars_map.get(key, [])
        return " ".join(vals) if vals else None

    options_define = _get_list("OPTIONS_DEFINE")
    options_default = _get_list("OPTIONS_DEFAULT")
    # Também contabilizar grupos/rádios de opções comuns em VLC e Blender
    options_extra: list[str] = []
    for k, v in vars_map.items():
        if k.startswith(("OPTIONS_GROUP_", "OPTIONS_RADIO_", "OPTIONS_SINGLE_", "OPTIONS_MULTI_")):
            options_extra.extend(v)
    all_options = sorted(set(options_define + options_extra))

    return {
        "portname": _get_scalar("PORTNAME"),
        "portversion": _get_scalar("PORTVERSION") or _get_scalar("DISTVERSION"),
        "categories": _get_list("CATEGORIES"),
        "license": _get_list("LICENSE"),
        "uses": _get_list("USES"),
        "build_depends_count": len(_get_list("BUILD_DEPENDS")),
        "build_depends": _get_list("BUILD_DEPENDS"),
        "lib_depends_count": len(_get_list("LIB_DEPENDS")),
        "lib_depends": _get_list("LIB_DEPENDS"),
        "run_depends_count": len(_get_list("RUN_DEPENDS")),
        "run_depends": _get_list("RUN_DEPENDS"),
        "options_define_count": len(options_define),
        "options_total_count": len(all_options),
        "options_default_count": len(options_default),
        "options_define": options_define,
        "options_default": options_default,
        "options_todas_unicas": all_options,
    }


def parse_freebsd_distinfo(distinfo_text: str) -> list[dict]:
    """Extrai arquivos, hashes SHA256 e tamanhos de um distinfo do FreeBSD Ports."""
    entries: dict[str, dict] = {}
    for line in distinfo_text.splitlines():
        m_sha = re.match(r"^SHA256\s*\(([^)]+)\)\s*=\s*([0-9a-fA-F]+)", line.strip())
        if m_sha:
            fname, sha = m_sha.group(1), m_sha.group(2)
            entries.setdefault(fname, {"arquivo": fname})["sha256"] = sha
        m_sz = re.match(r"^SIZE\s*\(([^)]+)\)\s*=\s*(\d+)", line.strip())
        if m_sz:
            fname, sz = m_sz.group(1), int(m_sz.group(2))
            entries.setdefault(fname, {"arquivo": fname}).update({
                "size_bytes": sz,
                "size_mib": round(sz / (1024 * 1024), 2),
            })
    return list(entries.values())


def _fetch_freebsd_port_file(port_path: str, filename: str, ref: str) -> tuple[int, str, str]:
    """Busca arquivo de um port no espelho oficial GitHub do FreeBSD Ports (sem 429) com fallback para cgit."""
    gh_url = f"https://raw.githubusercontent.com/freebsd/freebsd-ports/{ref}/{port_path}/{filename}"
    st, txt = http_get_text(gh_url)
    if st == 200:
        return st, txt, gh_url
    cgit_suffix = f"?id={ref}" if ref != "main" else ""
    cgit_url = f"https://cgit.freebsd.org/ports/plain/{port_path}/{filename}{cgit_suffix}"
    st2, txt2 = http_get_text(cgit_url)
    return st2, txt2, cgit_url


def run_ports_experiments(
    tools: ToolResolver,
    selected_apps: list[str],
    reps: int,
    build_source: bool,
    align_versions: str = "debian",
) -> dict:
    print(f"[3/6] Executando inspeção oficial da árvore FreeBSD Ports (alinhamento={align_versions})...")
    logs: list[str] = []
    ports_data: dict[str, dict] = {}

    for app_key in selected_apps:
        cfg = APPS[app_key]
        port_path = cfg["freebsd_port"]
        ref = cfg["freebsd_ref_aligned"] if align_versions == "debian" else "main"
        print(f"  -> FreeBSD Ports: {port_path} (ref={ref[:12]})...")

        st_mk, mk_text, url_mk = _fetch_freebsd_port_file(port_path, "Makefile", ref)
        st_di, di_text, url_di = _fetch_freebsd_port_file(port_path, "distinfo", ref)
        st_de, de_text, url_de = _fetch_freebsd_port_file(port_path, "pkg-descr", ref)

        logs.append(f"=== Receita oficial FreeBSD Ports: {port_path} (ref={ref}) ===")
        logs.append(f"[GET {url_mk} -> HTTP {st_mk} | {len(mk_text)} bytes]\n{mk_text[:4000]}\n")

        # Se o Makefile incluir arquivos auxiliares de opções (ex.: graphics/blender/Makefile.options), incluí-los no parser
        combined_mk = mk_text
        http_status: dict[str, int] = {"Makefile": st_mk, "distinfo": st_di, "pkg-descr": st_de}
        included_opts_files: list[str] = []
        if st_mk == 200:
            for inc_name in re.findall(r'\.include\s+"(?:\$\{\.CURDIR\}/)?(Makefile\.[A-Za-z0-9_.-]+)"', mk_text):
                st_inc, inc_text, url_inc = _fetch_freebsd_port_file(port_path, inc_name, ref)
                http_status[inc_name] = st_inc
                logs.append(f"[GET {url_inc} -> HTTP {st_inc} | {len(inc_text)} bytes]\n{inc_text[:4000]}\n")
                if st_inc == 200:
                    combined_mk = combined_mk + "\n" + inc_text
                    included_opts_files.append(inc_name)

        logs.append(f"[GET {url_di} -> HTTP {st_di} | {len(di_text)} bytes]\n{di_text}\n")
        logs.append(f"[GET {url_de} -> HTTP {st_de}]\n{de_text}\n")

        parsed_mk = parse_freebsd_makefile(combined_mk) if st_mk == 200 else {"erro_http": st_mk}
        parsed_di = parse_freebsd_distinfo(di_text) if st_di == 200 else []
        dist_total_bytes = sum(item.get("size_bytes", 0) for item in parsed_di)

        ports_data[app_key] = {
            "port": port_path,
            "ref_git": ref,
            "url_makefile": url_mk,
            "arquivos_incluidos_parseados": included_opts_files,
            "http_status": http_status,
            "makefile": parsed_mk,
            "distinfo": parsed_di,
            "distfiles_total_bytes": dist_total_bytes,
            "distfiles_total_mib": round(dist_total_bytes / (1024 * 1024), 2),
        }

    # Build opcional do código-fonte do menor aplicativo (gnome-text-editor via Meson/Ninja)
    source_build_report: dict[str, object] = {
        "executado": False,
        "motivo": (
            "Modo padrão faz inspeção estrutural completa dos 3 ports (Makefile, distinfo, "
            "dependências e opções de compilação). Use --build-source para tentar compilar "
            "localmente o tarball oficial do gnome-text-editor com Meson/Ninja."
        ),
    }
    if build_source and "gnome-text-editor" in ports_data:
        print("  -> FreeBSD Ports (--build-source): tentando compilação controlada do gnome-text-editor...")
        gte_di = ports_data["gnome-text-editor"].get("distinfo", [])
        meson_bin = shutil.which("meson")
        ninja_bin = shutil.which("ninja")
        if not meson_bin or not ninja_bin:
            source_build_report = {
                "executado": False,
                "motivo": (
                    "meson e/ou ninja não encontrados no PATH do ambiente atual. "
                    "Para compilar localmente, execute dentro de um nix-shell com meson, ninja, pkg-config "
                    "e dependências GTK4/libadwaita/gtksourceview5/libspelling."
                ),
            }
        elif gte_di:
            dist_entry = gte_di[0]
            fname = Path(dist_entry["arquivo"]).name
            ver = ports_data["gnome-text-editor"]["makefile"].get("portversion", "")
            major = ver.split(".")[0] if ver else ""
            dl_url = f"https://download.gnome.org/sources/gnome-text-editor/{major}/{fname}"
            with tempfile.TemporaryDirectory(prefix="so-s5-src-gte-") as tmp_src:
                tpath = Path(tmp_src)
                tarball = tpath / fname
                r_dl = run_cmd([tools.get("curl", required=True), "-4", "-fsSL", dl_url, "-o", str(tarball)])
                logs.append(format_log_entry(r_dl))
                if r_dl["returncode"] == 0 and tarball.exists():
                    sha_actual = hashlib.sha256(tarball.read_bytes()).hexdigest()
                    time_bin = tools.get("time", required=False)
                    setup_ms, build_ms, stage_ms = [], [], []
                    build_rusage: list[dict | None] = []
                    last_err = ""
                    wrk_bytes = 0
                    stg_bytes = 0
                    for rep in range(1, reps + 1):
                        rdir = tpath / f"rep{rep}"
                        rdir.mkdir()
                        run_cmd(["tar", "-xf", str(tarball), "-C", str(rdir)])
                        src_dirs = [p for p in rdir.iterdir() if p.is_dir()]
                        if not src_dirs:
                            last_err = "Diretório de código-fonte não encontrado após extração."
                            break
                        sdir = src_dirs[0]
                        bdir = rdir / "build"
                        stdir = rdir / "stage"
                        r_setup = run_cmd([meson_bin, "setup", str(bdir), "--prefix=/usr/local"], cwd=sdir)
                        if rep == 1:
                            logs.append(format_log_entry(r_setup))
                        if r_setup["returncode"] != 0:
                            last_err = r_setup["stderr"].strip() or r_setup["stdout"].strip()
                            break
                        r_bld = run_cmd_timed(time_bin, [ninja_bin, "-C", str(bdir), "-j4"])
                        if rep == 1:
                            logs.append(format_log_entry(r_bld))
                        if r_bld["returncode"] != 0:
                            last_err = r_bld["stderr"].strip() or r_bld["stdout"].strip()
                            break
                        r_stg = run_cmd(
                            [ninja_bin, "-C", str(bdir), "install"],
                            env={"DESTDIR": str(stdir)},
                        )
                        if rep == 1:
                            logs.append(format_log_entry(r_stg))
                            wrk_bytes = sum(p.stat().st_size for p in bdir.rglob("*") if p.is_file() and not p.is_symlink())
                            stg_bytes = sum(p.stat().st_size for p in stdir.rglob("*") if p.is_file() and not p.is_symlink())
                        setup_ms.append(r_setup["elapsed_ms"])
                        build_ms.append(r_bld["elapsed_ms"])
                        build_rusage.append(r_bld.get("rusage"))
                        stage_ms.append(r_stg["elapsed_ms"])

                    source_build_report = {
                        "executado": bool(build_ms),
                        "tarball": fname,
                        "url": dl_url,
                        "sha256_esperado": dist_entry.get("sha256"),
                        "sha256_verificado": sha_actual,
                        "checksum_coincide": sha_actual == dist_entry.get("sha256"),
                        "tempo_meson_setup_ms": summarize_series(setup_ms),
                        "tempo_ninja_build_ms": summarize_series(build_ms),
                        "recursos_ninja_build": summarize_rusage_series(build_rusage),
                        "tempo_stage_install_ms": summarize_series(stage_ms),
                        "wrkdir_bytes": wrk_bytes,
                        "stagedir_bytes": stg_bytes,
                        "erro_se_falhou": last_err[:1500] if last_err else None,
                    }

    metrics = {
        "alinhamento_versoes": align_versions,
        "alcance_metodologico": (
            "As receitas oficiais (Makefile, distinfo e pkg-descr) de editors/gnome-text-editor, "
            "multimedia/vlc e graphics/blender foram consultadas diretamente na árvore oficial do FreeBSD Ports. "
            "Como o hospedeiro é NixOS Linux (sem VM FreeBSD) e a compilação integral de VLC/Blender exige "
            "extensa pilha de bibliotecas de desenvolvimento e longo tempo de CPU, a comparação combina a "
            "auditoria estrutural real dos 3 ports com o baseline de compilação GNU hello da Semana 4 "
            "e compilação opcional do gnome-text-editor (--build-source)."
        ),
        "ports": ports_data,
        "build_fonte_opcional": source_build_report,
    }
    (EVID_DIR / "freebsd-ports-testes-finais.txt").write_text("\n".join(logs))
    (EVID_DIR / "freebsd-ports-testes-finais.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    return metrics


# =============================================================================
# 4. NIX (STORE, CLOSURE, DEDUPLICAÇÃO, ELF, PERFIS, ROLLBACK E CARGAS REAIS)
# =============================================================================

def _run_timed_with_optional_inner_prefix(
    cmd_args: list[str],
    prefix: list[str],
    time_bin: str | None,
    work_dir: Path,
    time_inside_prefix: bool,
    timeout: int | None = None,
) -> dict:
    """Executa comando com GNU time fora ou dentro do prefixo (essencial para bwrap --unshare-pid)."""
    if time_bin and time_inside_prefix and prefix:
        rusage_file = work_dir / "time-rusage.json"
        if rusage_file.exists():
            rusage_file.unlink()
        full_cmd = [*prefix, time_bin, "-f", GNU_TIME_FMT, "-o", str(rusage_file), *cmd_args]
        res = run_cmd(full_cmd, timeout=timeout)
        res["cmd"] = " ".join([*prefix, *cmd_args])
        raw = rusage_file.read_text(errors="replace") if rusage_file.exists() else ""
        res["rusage"] = parse_gnu_time_json(raw)
        if rusage_file.exists():
            rusage_file.unlink()
        return res
    return run_cmd_timed(time_bin, [*prefix, *cmd_args], timeout=timeout)


def _run_native_workload(
    app_key: str,
    bin_path: str,
    work_dir: Path,
    prefix_cmd: list[str] | None = None,
    time_bin: str | None = None,
    time_inside_prefix: bool = False,
) -> tuple[dict, dict]:
    """Executa carga de trabalho real de forma nativa (ou prefixada por bwrap/strace), opcionalmente com GNU time."""
    prefix = prefix_cmd or []
    work_dir.mkdir(parents=True, exist_ok=True)
    if app_key == "gnome-text-editor":
        res = _run_timed_with_optional_inner_prefix(
            [bin_path, "--version"], prefix, time_bin, work_dir, time_inside_prefix
        )
        return res, {"verificado": res["returncode"] == 0, "saida": res["stdout"].strip()}

    if app_key == "vlc":
        in_wav = work_dir / "in.wav"
        if not in_wav.exists():
            generate_test_wav(in_wav)
        out_ogg = work_dir / "out.ogg"
        if out_ogg.exists():
            out_ogg.unlink()
        app_cmd = [
            bin_path, "-I", "dummy", "--no-video", "--aout=dummy", "--play-and-exit",
            str(in_wav),
            "--sout", f"#transcode{{acodec=vorb,ab=128,channels=1,samplerate=44100}}:std{{access=file,mux=ogg,dst={out_ogg}}}",
            "vlc://quit",
        ]
        res = _run_timed_with_optional_inner_prefix(
            app_cmd, prefix, time_bin, work_dir, time_inside_prefix, timeout=120
        )
        if out_ogg.exists() and out_ogg.stat().st_size > 0:
            magic_ok = out_ogg.read_bytes()[:4] == b"OggS"
            return res, {
                "verificado": res["returncode"] == 0 and magic_ok,
                "formato": "ogg/vorbis",
                "tamanho_bytes": out_ogg.stat().st_size,
                "magic_ok": magic_ok,
            }
        # Fallback universal para WAV caso codec vorbis não esteja habilitado
        out_wav = work_dir / "out.wav"
        if out_wav.exists():
            out_wav.unlink()
        app_cmd_fb = [
            bin_path, "-I", "dummy", "--no-video", "--aout=dummy", "--play-and-exit",
            str(in_wav),
            "--sout", f"#transcode{{acodec=s16l,channels=1,samplerate=44100}}:std{{access=file,mux=wav,dst={out_wav}}}",
            "vlc://quit",
        ]
        res_fb = _run_timed_with_optional_inner_prefix(
            app_cmd_fb, prefix, time_bin, work_dir, time_inside_prefix, timeout=120
        )
        ok_wav = out_wav.exists() and out_wav.stat().st_size > 0 and out_wav.read_bytes()[:4] == b"RIFF"
        return res_fb, {
            "verificado": res_fb["returncode"] == 0 and ok_wav,
            "formato": "wav/pcm (fallback)",
            "tamanho_bytes": out_wav.stat().st_size if out_wav.exists() else 0,
            "magic_ok": ok_wav,
        }

    if app_key == "blender":
        out_png = work_dir / "render.png"
        if out_png.exists():
            out_png.unlink()
        app_cmd = [
            bin_path, "--background", "--factory-startup",
            "--python-expr", BLENDER_RENDER_EXPR,
            "--", str(out_png),
        ]
        res = _run_timed_with_optional_inner_prefix(
            app_cmd, prefix, time_bin, work_dir, time_inside_prefix, timeout=300
        )
        ok_png = out_png.exists() and out_png.stat().st_size > 0 and out_png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        return res, {
            "verificado": res["returncode"] == 0 and ok_png,
            "formato": "png (Cycles CPU 320x240, 4 samples)",
            "tamanho_bytes": out_png.stat().st_size if out_png.exists() else 0,
            "magic_ok": ok_png,
        }

    raise ValueError(f"App desconhecido: {app_key}")


def _find_wrapped_binary(store_path: Path, bin_rel: str) -> Path | None:
    """Detecta binário .<nome>-wrapped gerado por wrapProgram/makeBinaryWrapper no Nix."""
    bin_path = store_path / bin_rel
    wrapped = bin_path.parent / f".{bin_path.name}-wrapped"
    if wrapped.is_file():
        return wrapped
    return None


def _get_nix_flake_ref(app_key: str, align_versions: str) -> str:
    cfg = APPS[app_key]
    if align_versions == "debian":
        return cfg["nix_flake_aligned"]
    return f"nixpkgs#{cfg['nix_attr']}"


def _resolve_nix_app_store_path(
    nix_bin: str,
    app_key: str,
    flake_ref: str,
) -> tuple[str | None, dict]:
    """Realiza pacote Nix e seleciona a saída multi-output que realmente contém o executável (evita -man/-doc)."""
    cfg = APPS[app_key]
    r_bld = run_cmd([nix_bin, "build", f"{flake_ref}.out", "--no-link", "--print-out-paths"])
    if r_bld["returncode"] != 0 or not r_bld["stdout"].strip():
        r_bld = run_cmd([nix_bin, "build", flake_ref, "--no-link", "--print-out-paths"])
    if r_bld["returncode"] != 0 or not r_bld["stdout"].strip():
        return None, r_bld
    candidates = [ln.strip() for ln in r_bld["stdout"].splitlines() if ln.strip()]
    for cand in candidates:
        if (Path(cand) / cfg["nix_bin_rel"]).exists():
            return cand, r_bld
    for cand in candidates:
        if not cand.endswith(("-man", "-doc", "-dev", "-info")):
            return cand, r_bld
    return candidates[0], r_bld


def _extract_nix_store_version(store_path: str, attr_name: str) -> str:
    base = Path(store_path).name
    # Formato: <32-char-hash>-<pname>-<version>
    parts = base.split("-", 1)
    name_ver = parts[1] if len(parts) == 2 else base
    prefix = f"{attr_name}-"
    if name_ver.startswith(prefix):
        return name_ver[len(prefix):]
    return name_ver


def run_nix_experiments(
    tools: ToolResolver,
    selected_apps: list[str],
    reps: int,
    align_versions: str = "debian",
) -> tuple[dict, dict[str, str]]:
    """Executa experimentos Nix e retorna (métricas, mapa app_key -> store_path)."""
    print(f"[4/6] Executando experimentos de Nix (alinhamento={align_versions})...")
    nix_bin = tools.get("nix", required=True)
    readelf_bin = tools.get("readelf", required=True)
    ldd_bin = tools.get("ldd", required=True)
    strace_bin = tools.get("strace", required=True)
    time_bin = tools.get("time", required=True)

    logs: list[str] = []
    store_paths: dict[str, str] = {}
    flake_refs: dict[str, str] = {}
    closures_sets: dict[str, set[str]] = {}
    app_results: dict[str, dict] = {}

    for app_key in selected_apps:
        cfg = APPS[app_key]
        flake_ref = _get_nix_flake_ref(app_key, align_versions)
        flake_refs[app_key] = flake_ref
        print(f"  -> Nix: realizando {flake_ref} no /nix/store...")
        sp, r_bld = _resolve_nix_app_store_path(nix_bin, app_key, flake_ref)
        logs.append(f"=== Nix: realização de {flake_ref} ===")
        logs.append(format_log_entry(r_bld))
        if not sp:
            app_results[app_key] = {"erro": r_bld["stderr"].strip() or "falha ao realizar pacote no Nix"}
            continue
        store_paths[app_key] = sp

    with tempfile.TemporaryDirectory(prefix="so-s5-nix-") as tmp_root:
        tmp_path = Path(tmp_root)

        for app_key in selected_apps:
            if app_key not in store_paths:
                continue
            cfg = APPS[app_key]
            sp = Path(store_paths[app_key])
            bin_path = sp / cfg["nix_bin_rel"]
            wrapped_path = _find_wrapped_binary(sp, cfg["nix_bin_rel"])
            print(f"  -> Nix: medindo métricas, perfis, rollback e carga real de {cfg['titulo']} ({sp.name})...")

            # 1. Tamanhos no store (NAR vs closure) e lista de paths do fechamento
            r_pi = run_cmd([nix_bin, "path-info", "-s", "-S", str(sp)])
            r_rec = run_cmd([nix_bin, "path-info", "-r", str(sp)])
            logs.extend([format_log_entry(r_pi), format_log_entry(r_rec)])

            nar_bytes, closure_bytes = 0, 0
            parts = r_pi["stdout"].strip().split()
            if len(parts) >= 3:
                nar_bytes, closure_bytes = int(parts[1]), int(parts[2])
            rec_paths = [ln.strip() for ln in r_rec["stdout"].splitlines() if ln.strip()]
            closures_sets[app_key] = set(rec_paths)

            # 2. Inspeção ELF (wrapper + binário real)
            elf_target = wrapped_path if wrapped_path else bin_path
            r_re_main = run_cmd(f'{readelf_bin} -d "{bin_path}" | grep -E "NEEDED|RUNPATH|RPATH" || true', shell=True)
            r_re_real = (
                run_cmd(f'{readelf_bin} -d "{elf_target}" | grep -E "NEEDED|RUNPATH|RPATH" || true', shell=True)
                if elf_target != bin_path
                else r_re_main
            )
            r_ldd = run_cmd([ldd_bin, str(elf_target)])
            logs.append(f"=== Nix ELF: {app_key} (bin={bin_path}, real={elf_target}) ===")
            logs.extend([format_log_entry(r_re_main), format_log_entry(r_re_real), format_log_entry(r_ldd)])
            ldd_lines = [ln for ln in r_ldd["stdout"].splitlines() if "=>" in ln or "/nix/store/" in ln]

            # 3. N repetições de profile add, carga real, remove e rollback (instrumentadas com GNU time)
            add_ms: list[float] = []
            add_rusage: list[dict | None] = []
            rollback_ms: list[float] = []
            rollback_rusage: list[dict | None] = []
            workload_ms: list[float] = []
            workload_rusage: list[dict | None] = []
            last_artifact: dict = {}

            for rep in range(1, reps + 1):
                prof = tmp_path / f"prof-{app_key}-{rep}"
                r_add = run_cmd_timed(time_bin, [nix_bin, "profile", "add", "--profile", str(prof), str(sp)])
                add_ms.append(r_add["elapsed_ms"])
                add_rusage.append(r_add.get("rusage"))

                wdir = tmp_path / f"work-{app_key}-{rep}"
                prof_bin = str(prof / cfg["nix_bin_rel"])
                r_wl, art = _run_native_workload(app_key, prof_bin, wdir, time_bin=time_bin)
                workload_ms.append(r_wl["elapsed_ms"])
                workload_rusage.append(r_wl.get("rusage"))
                last_artifact = art

                run_cmd([nix_bin, "profile", "remove", "--profile", str(prof), "--all"])
                r_rb = run_cmd_timed(time_bin, [nix_bin, "profile", "rollback", "--profile", str(prof)])
                rollback_ms.append(r_rb["elapsed_ms"])
                rollback_rusage.append(r_rb.get("rusage"))

                if rep == 1:
                    logs.extend([format_log_entry(r_add), format_log_entry(r_wl), format_log_entry(r_rb)])

            # 4. strace -c -f de profile add, rollback e carga real
            prof_tr = tmp_path / f"prof-trace-{app_key}"
            r_st_add = run_cmd([strace_bin, "-c", "-f", nix_bin, "profile", "add", "--profile", str(prof_tr), str(sp)])
            run_cmd([nix_bin, "profile", "remove", "--profile", str(prof_tr), "--all"])
            r_st_rb = run_cmd([strace_bin, "-c", "-f", nix_bin, "profile", "rollback", "--profile", str(prof_tr)])
            r_st_wl, _ = _run_native_workload(
                app_key,
                str(prof_tr / cfg["nix_bin_rel"]),
                tmp_path / f"work-trace-{app_key}",
                prefix_cmd=[strace_bin, "-c", "-f"],
            )
            logs.extend([format_log_entry(r_st_add), format_log_entry(r_st_rb), format_log_entry(r_st_wl)])

            app_results[app_key] = {
                "flake_ref": flake_refs.get(app_key),
                "versao": _extract_nix_store_version(str(sp), cfg["nix_attr"]),
                "store_path": str(sp),
                "possui_wrapper": wrapped_path is not None,
                "binario_principal": str(bin_path),
                "binario_elf_real": str(elf_target),
                "nar_bytes": nar_bytes,
                "nar_mib": round(nar_bytes / (1024 * 1024), 2),
                "closure_bytes": closure_bytes,
                "closure_mib": round(closure_bytes / (1024 * 1024), 2),
                "closure_paths_count": len(rec_paths),
                "bibliotecas_ldd_count": len(ldd_lines),
                "elf_wrapper": parse_readelf_dynamic(r_re_main["stdout"]),
                "elf_real": parse_readelf_dynamic(r_re_real["stdout"]),
                "tempo_profile_add_ms": summarize_series(add_ms),
                "recursos_profile_add": summarize_rusage_series(add_rusage),
                "tempo_profile_rollback_ms": summarize_series(rollback_ms),
                "recursos_profile_rollback": summarize_rusage_series(rollback_rusage),
                "tempo_carga_real_ms": summarize_series(workload_ms),
                "recursos_carga_real": summarize_rusage_series(workload_rusage),
                "carga_real_artefato": last_artifact,
                "strace_profile_add": parse_strace_summary(r_st_add["stderr"]),
                "strace_profile_rollback": parse_strace_summary(r_st_rb["stderr"]),
                "strace_carga_real": parse_strace_summary(r_st_wl["stderr"]),
            }

        # 5. Deduplicação entre fechamentos e teste de coexistência + preservação de documento externo
        union_paths: set[str] = set()
        for s in closures_sets.values():
            union_paths |= s
        sum_individual_paths = sum(len(s) for s in closures_sets.values())
        common_all = set.intersection(*closures_sets.values()) if len(closures_sets) >= 2 else set()

        # Quando alinhado ao Debian, os apps vêm de revisões históricas distintas do nixpkgs;
        # medimos também a deduplicação realista numa mesma revisão única do nixpkgs (já em cache local).
        same_rev_dedup: dict[str, object] | None = None
        if align_versions == "debian" and len(selected_apps) >= 2:
            same_rev_sets: dict[str, set[str]] = {}
            for ak in selected_apps:
                sp_cur, _ = _resolve_nix_app_store_path(nix_bin, ak, f"nixpkgs#{APPS[ak]['nix_attr']}")
                if sp_cur:
                    r_sr = run_cmd([nix_bin, "path-info", "-r", sp_cur])
                    if r_sr["returncode"] == 0:
                        same_rev_sets[ak] = {ln.strip() for ln in r_sr["stdout"].splitlines() if ln.strip()}
            if len(same_rev_sets) >= 2:
                sr_union: set[str] = set()
                for s in same_rev_sets.values():
                    sr_union |= s
                sr_sum = sum(len(s) for s in same_rev_sets.values())
                sr_common = set.intersection(*same_rev_sets.values())
                same_rev_dedup = {
                    "apps_avaliados": list(same_rev_sets.keys()),
                    "soma_paths_individuais": sr_sum,
                    "paths_unicos_uniao": len(sr_union),
                    "paths_reaproveitados_entre_apps": sr_sum - len(sr_union),
                    "paths_comuns_a_todos_apps": len(sr_common),
                }

        coexistence: dict[str, object] = {}
        if len(store_paths) >= 2:
            keys = list(store_paths.keys())
            prof_a = tmp_path / "coex-perfil-a"
            prof_b = tmp_path / "coex-perfil-b"
            user_doc = tmp_path / "documento-usuario.txt"
            user_doc.write_text("estado=inicial\n")

            run_cmd([nix_bin, "profile", "add", "--profile", str(prof_a), store_paths[keys[0]]])
            run_cmd([nix_bin, "profile", "add", "--profile", str(prof_b), store_paths[keys[0]], store_paths[keys[1]]])
            user_doc.write_text("estado=editado-pelo-usuario\n")
            run_cmd([nix_bin, "profile", "remove", "--profile", str(prof_a), "--all"])
            r_rb_a = run_cmd([nix_bin, "profile", "rollback", "--profile", str(prof_a)])
            r_la = run_cmd([nix_bin, "profile", "list", "--profile", str(prof_a)])
            r_lb = run_cmd([nix_bin, "profile", "list", "--profile", str(prof_b)])
            logs.extend([
                "=== Nix: coexistência de perfis e preservação de arquivo externo após rollback ===",
                format_log_entry(r_rb_a),
                format_log_entry(r_la),
                format_log_entry(r_lb),
            ])
            coexistence = {
                "perfil_a_restaurado_por_rollback": (prof_a / APPS[keys[0]]["nix_bin_rel"]).exists(),
                "perfil_b_preservado": (prof_b / APPS[keys[1]]["nix_bin_rel"]).exists(),
                "conteudo_documento_usuario_apos_rollback": user_doc.read_text().strip(),
                "dados_usuario_preservados": user_doc.read_text().strip() == "estado=editado-pelo-usuario",
            }

    metrics = {
        "ambiente": "Nix nativo no hospedeiro NixOS",
        "alinhamento_versoes": align_versions,
        "aplicacoes": app_results,
        "deduplicacao_fechamentos": {
            "soma_paths_individuais": sum_individual_paths,
            "paths_unicos_uniao": len(union_paths),
            "paths_reaproveitados_entre_apps": sum_individual_paths - len(union_paths),
            "paths_comuns_a_todos_apps": len(common_all),
        },
        "deduplicacao_fechamentos_mesma_revisao": same_rev_dedup,
        "coexistencia_e_rollback_dados_externos": coexistence,
    }
    (EVID_DIR / "nix-testes-finais.txt").write_text("\n".join(logs))
    (EVID_DIR / "nix-testes-finais.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    return metrics, store_paths


# =============================================================================
# 5. FLATPAK (FLATHUB METADADOS, OSTREE DEDUPLICAÇÃO E BUBBLEWRAP SANDBOX)
# =============================================================================

def parse_flatpak_remote_info(text: str) -> dict:
    """Extrai campos principais da saída de `flatpak remote-info`."""
    data: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            key = k.strip().lower().replace(" ", "_")
            if key in {"id", "ref", "arch", "branch", "download_size", "installed_size", "runtime", "sdk", "commit", "date"}:
                data[key] = v.strip().replace("\xa0", " ")
    return data


def parse_flatpak_metadata(text: str) -> dict:
    """Extrai seções [Context], [Session Bus Policy] e [Extension ...] do metadata Flatpak."""
    section = ""
    context: dict[str, list[str]] = {}
    session_bus: dict[str, str] = {}
    extensions: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            if section.startswith("Extension "):
                extensions.append(section.split(" ", 1)[1])
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            if section == "Context":
                context[k.strip()] = [x for x in v.strip().split(";") if x]
            elif section == "Session Bus Policy":
                session_bus[k.strip()] = v.strip()
    return {
        "context": context,
        "session_bus_policy": session_bus,
        "extensions": extensions,
    }


def run_flatpak_experiments(
    tools: ToolResolver,
    selected_apps: list[str],
    reps: int,
    nix_store_paths: dict[str, str],
    align_versions: str = "debian",
) -> dict:
    print(f"[5/6] Executando experimentos de Flatpak (Flathub, OSTree e Bubblewrap | alinhamento={align_versions})...")
    flatpak_bin = tools.get("flatpak", required=True)
    ostree_bin = tools.get("ostree", required=True)
    bwrap_bin = tools.get("bwrap", required=True)
    strace_bin = tools.get("strace", required=True)
    time_bin = tools.get("time", required=True)

    logs: list[str] = []
    flathub_apps: dict[str, dict] = {}
    flathub_runtimes: dict[str, dict] = {}
    bwrap_workloads: dict[str, dict] = {}

    with tempfile.TemporaryDirectory(prefix="so-s5-flatpak-") as tmp_root:
        tmp_path = Path(tmp_root)

        # 1. Auditoria real no Flathub
        fp_user_dir = tmp_path / "flatpak-user"
        fp_env = {"FLATPAK_USER_DIR": str(fp_user_dir)}
        r_add = run_cmd([
            flatpak_bin, "remote-add", "--if-not-exists", "--user",
            "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo",
        ], env=fp_env)
        logs.append("=== Flatpak: configuração do remote Flathub ===")
        logs.append(format_log_entry(r_add))

        seen_runtimes: set[str] = set()
        for app_key in selected_apps:
            cfg = APPS[app_key]
            app_id = cfg["flatpak_id"]
            print(f"  -> Flatpak (Flathub): consultando {app_id}...")
            r_info = run_cmd([flatpak_bin, "remote-info", "--user", "flathub", app_id], env=fp_env)
            r_meta = run_cmd([flatpak_bin, "remote-info", "--user", "--show-metadata", "flathub", app_id], env=fp_env)
            logs.append(f"=== Flathub: {app_id} ===")
            logs.extend([format_log_entry(r_info), format_log_entry(r_meta)])

            info = parse_flatpak_remote_info(r_info["stdout"])
            meta = parse_flatpak_metadata(r_meta["stdout"])
            flathub_apps[app_key] = {"info": info, "metadata": meta}

            rt_ref = info.get("runtime")
            if rt_ref and rt_ref not in seen_runtimes:
                seen_runtimes.add(rt_ref)
                r_rt = run_cmd([flatpak_bin, "remote-info", "--user", "flathub", rt_ref], env=fp_env)
                logs.append(format_log_entry(r_rt))
                flathub_runtimes[rt_ref] = parse_flatpak_remote_info(r_rt["stdout"])

        # 2. Deduplicação física por hardlinks/inodes no OSTree (bare-user) com binários reais
        print("  -> Flatpak (OSTree): medindo deduplicação por hardlinks/inodes...")
        ostree_repo = tmp_path / "ostree-repo"
        tree_v1 = tmp_path / "ostree-v1"
        tree_v2 = tmp_path / "ostree-v2"
        tree_v1.mkdir()
        tree_v2.mkdir()

        sample_files: list[str] = []
        for app_key in selected_apps:
            sp_str = nix_store_paths.get(app_key)
            if sp_str:
                sp = Path(sp_str)
                b_real = _find_wrapped_binary(sp, APPS[app_key]["nix_bin_rel"]) or (sp / APPS[app_key]["nix_bin_rel"])
                if b_real.is_file():
                    dest_name = f"{app_key}.bin"
                    shutil.copy2(b_real, tree_v1 / dest_name)
                    shutil.copy2(b_real, tree_v2 / dest_name)
                    sample_files.append(dest_name)
        if not sample_files:
            payload = os.urandom(512 * 1024)
            (tree_v1 / "payload.bin").write_bytes(payload)
            (tree_v2 / "payload.bin").write_bytes(payload)
            sample_files.append("payload.bin")

        (tree_v1 / "release-meta.txt").write_text("release=1.0\n")
        (tree_v2 / "release-meta.txt").write_text("release=2.0\n")

        r_oi = run_cmd([ostree_bin, "init", f"--repo={ostree_repo}", "--mode=bare-user"])
        r_oc1 = run_cmd([ostree_bin, "commit", f"--repo={ostree_repo}", "--branch=so/final/stable", "--subject=v1", str(tree_v1)])
        r_oc2 = run_cmd([ostree_bin, "commit", f"--repo={ostree_repo}", "--branch=so/final/stable", "--subject=v2", str(tree_v2)])
        c1, c2 = r_oc1["stdout"].strip(), r_oc2["stdout"].strip()
        co1, co2 = tmp_path / "co-v1", tmp_path / "co-v2"
        r_co1 = run_cmd([ostree_bin, "checkout", f"--repo={ostree_repo}", "-U", c1, str(co1)])
        r_co2 = run_cmd([ostree_bin, "checkout", f"--repo={ostree_repo}", "-U", c2, str(co2)])
        logs.extend([
            "=== OSTree: deduplicação física (inodes/hardlinks) ===",
            format_log_entry(r_oi), format_log_entry(r_oc1), format_log_entry(r_oc2),
            format_log_entry(r_co1), format_log_entry(r_co2),
        ])

        inode_checks: dict[str, dict] = {}
        for fname in sample_files:
            st1, st2 = (co1 / fname).stat(), (co2 / fname).stat()
            inode_checks[fname] = {
                "tamanho_bytes": st1.st_size,
                "inode_v1": st1.st_ino,
                "inode_v2": st2.st_ino,
                "nlink": st1.st_nlink,
                "mesmo_inode": st1.st_ino == st2.st_ino,
            }
        st_m1, st_m2 = (co1 / "release-meta.txt").stat(), (co2 / "release-meta.txt").stat()
        ostree_metrics = {
            "commit_v1": c1,
            "commit_v2": c2,
            "arquivos_inalterados": inode_checks,
            "arquivo_alterado": {
                "nome": "release-meta.txt",
                "inode_v1": st_m1.st_ino,
                "inode_v2": st_m2.st_ino,
                "inodes_distintos": st_m1.st_ino != st_m2.st_ino,
            },
        }

        # 3. Isolamento de arquivos (sem bind / --ro-bind / --bind) no Bubblewrap
        print("  -> Flatpak (Bubblewrap): testando isolamento de arquivos e cargas reais em sandbox...")
        doc_dir = tmp_path / "doc-sandbox"
        doc_dir.mkdir()
        doc_file = doc_dir / "comparacao-final.txt"
        doc_file.write_text("Teste de isolamento Bubblewrap: aguardando\n")

        bwrap_base = [
            bwrap_bin,
            "--ro-bind", "/nix", "/nix",
            "--ro-bind", "/run", "/run",
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp",
            "--unshare-all",
        ]
        r_iso = run_cmd([*bwrap_base, "/run/current-system/sw/bin/cat", str(doc_file)])
        r_ro_r = run_cmd([*bwrap_base, "--ro-bind", str(doc_dir), str(doc_dir), "/run/current-system/sw/bin/cat", str(doc_file)])
        r_ro_w = run_cmd([
            *bwrap_base, "--ro-bind", str(doc_dir), str(doc_dir),
            "/run/current-system/sw/bin/sh", "-c", f'echo bloqueado > "{doc_dir}/ro-out.txt"',
        ])
        r_rw_w = run_cmd([
            *bwrap_base, "--bind", str(doc_dir), str(doc_dir),
            "/run/current-system/sw/bin/sh", "-c",
            f'sed "s/aguardando/concluido/" "{doc_file}" > "{doc_dir}/rw-out.txt" && cat "{doc_dir}/rw-out.txt"',
        ])
        logs.extend([
            "=== Bubblewrap: política de acesso a arquivos (sem bind / RO / RW) ===",
            format_log_entry(r_iso), format_log_entry(r_ro_r),
            format_log_entry(r_ro_w), format_log_entry(r_rw_w),
        ])

        # 4. Execução das cargas de trabalho reais dentro de bwrap --unshare-all (GNU time DENTRO do namespace PID!)
        for app_key in selected_apps:
            sp_str = nix_store_paths.get(app_key)
            if not sp_str:
                nix_bin = tools.get("nix", required=False)
                if nix_bin:
                    flake_ref = _get_nix_flake_ref(app_key, align_versions)
                    sp_str, _ = _resolve_nix_app_store_path(nix_bin, app_key, flake_ref)
            if not sp_str:
                bwrap_workloads[app_key] = {"executado": False, "motivo": "binário Nix indisponível para execução no bwrap"}
                continue

            bin_path = str(Path(sp_str) / APPS[app_key]["nix_bin_rel"])
            bw_times: list[float] = []
            bw_rusage: list[dict | None] = []
            last_art: dict = {}
            for rep in range(1, reps + 1):
                wdir = tmp_path / f"bwrap-{app_key}-{rep}"
                wdir.mkdir(parents=True, exist_ok=True)
                prefix = [*bwrap_base, "--bind", str(wdir), str(wdir)]
                r_bw, art = _run_native_workload(
                    app_key, bin_path, wdir, prefix_cmd=prefix, time_bin=time_bin, time_inside_prefix=True
                )
                bw_times.append(r_bw["elapsed_ms"])
                bw_rusage.append(r_bw.get("rusage"))
                last_art = art
                if rep == 1:
                    logs.append(f"=== Bubblewrap: carga real de {app_key} (repetição 1) ===")
                    logs.append(format_log_entry(r_bw))

            # strace -c -f do sandbox + workload
            wdir_tr = tmp_path / f"bwrap-trace-{app_key}"
            wdir_tr.mkdir(parents=True, exist_ok=True)
            prefix_tr = [strace_bin, "-c", "-f", *bwrap_base, "--bind", str(wdir_tr), str(wdir_tr)]
            r_bw_tr, _ = _run_native_workload(app_key, bin_path, wdir_tr, prefix_cmd=prefix_tr)
            logs.append(format_log_entry(r_bw_tr))

            bwrap_workloads[app_key] = {
                "executado": True,
                "versao_binario_bwrap": _extract_nix_store_version(sp_str, APPS[app_key]["nix_attr"]),
                "tempo_bwrap_ms": summarize_series(bw_times),
                "recursos_bwrap_carga_real": summarize_rusage_series(bw_rusage),
                "carga_real_artefato": last_art,
                "strace_bwrap": parse_strace_summary(r_bw_tr["stderr"]),
            }

    metrics = {
        "alinhamento_versoes": align_versions,
        "flathub_aplicacoes": flathub_apps,
        "flathub_runtimes": flathub_runtimes,
        "ostree_deduplicacao": ostree_metrics,
        "bubblewrap_politica_arquivos": {
            "sem_bind_bloqueado": r_iso["returncode"] != 0,
            "ro_bind_leitura_ok": r_ro_r["returncode"] == 0,
            "ro_bind_escrita_bloqueada": r_ro_w["returncode"] != 0,
            "rw_bind_escrita_ok": r_rw_w["returncode"] == 0,
        },
        "bubblewrap_cargas_reais": bwrap_workloads,
    }
    (EVID_DIR / "flatpak-testes-finais.txt").write_text("\n".join(logs))
    (EVID_DIR / "flatpak-testes-finais.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    return metrics


# =============================================================================
# 6. SNAP (SNAP STORE API v2, CONFINAMENTO STRICT vs CLASSIC, SQUASHFS E LSM)
# =============================================================================

def parse_unsquashfs_superblock(text: str) -> dict:
    """Extrai métricas do superbloco SquashFS da saída de `unsquashfs -s`."""
    info: dict[str, object] = {}
    for pat, key, cast in [
        (r"Compression\s+(\S+)", "compressor_original", str),
        (r"Block size\s+(\d+)", "block_size_bytes", int),
        (r"Number of inodes\s+(\d+)", "inodes_squashfs", int),
        (r"Number of fragments\s+(\d+)", "fragments", int),
        (r"Filesystem size\s+([\d.]+)\s+bytes", "filesystem_size_bytes", float),
    ]:
        m = re.search(pat, text)
        if m:
            info[key] = cast(m.group(1))
    return info


def run_snap_experiments(
    tools: ToolResolver,
    selected_apps: list[str],
    reps: int,
    cache_dir: Path,
    skip_snap_download: bool,
    full_squashfs_bench: bool,
    align_versions: str = "debian",
) -> dict:
    print(f"[6/6] Executando experimentos de Snap (alinhamento={align_versions})...")
    curl_bin = tools.get("curl", required=True)
    mksquashfs_bin = tools.get("mksquashfs", required=not skip_snap_download)
    unsquashfs_bin = tools.get("unsquashfs", required=not skip_snap_download)
    readelf_bin = tools.get("readelf", required=not skip_snap_download)
    time_bin = tools.get("time", required=not skip_snap_download)

    logs: list[str] = []
    snaps_results: dict[str, dict] = {}
    snap_cache = cache_dir / "snaps"
    snap_cache.mkdir(parents=True, exist_ok=True)

    lsm = Path("/sys/kernel/security/lsm").read_text().strip() if Path("/sys/kernel/security/lsm").exists() else "indisponível"

    for app_key in selected_apps:
        cfg = APPS[app_key]
        snap_name = cfg["snap_name"]
        target_channel = cfg["snap_channel_aligned"] if align_versions == "debian" else "latest/stable"
        print(f"  -> Snap: consultando Snap Store API v2 para '{snap_name}' (canal alvo={target_channel})...")
        api_url = f"https://api.snapcraft.io/v2/snaps/info/{snap_name}"
        status, body = http_get_text(api_url, headers={"Snap-Device-Series": "16", "Accept": "application/json"})
        logs.append(f"=== Snap Store API v2: {snap_name} (HTTP {status} | canal alvo={target_channel}) ===")

        if status != 200:
            logs.append(body[:1000] + "\n")
            snaps_results[app_key] = {"snap": snap_name, "erro_http": status}
            continue

        payload = json.loads(body)
        snap_meta = payload.get("snap", {})
        channel_map = payload.get("channel-map", [])

        # Selecionar o canal alvo (ex.: 4.3/stable no Blender alinhado ou latest/stable) para amd64
        selected_amd64 = None
        tracks_summary: list[dict] = []
        for entry in channel_map:
            ch = entry.get("channel", {})
            if ch.get("architecture") != "amd64":
                continue
            ch_name = ch.get("name", "")
            ch_full = f"{ch.get('track', 'latest')}/{ch.get('risk', '')}"
            if ch.get("risk") == "stable":
                tracks_summary.append({
                    "channel": ch_name,
                    "version": entry.get("version"),
                    "revision": entry.get("revision"),
                    "confinement": entry.get("confinement"),
                    "base": entry.get("base"),
                    "download_mib": round(entry.get("download", {}).get("size", 0) / (1024 * 1024), 2),
                })
            if ch_name == target_channel or ch_full == target_channel or (target_channel == "latest/stable" and ch_name == "stable"):
                selected_amd64 = entry

        if not selected_amd64 and tracks_summary:
            # Fallback para primeiro canal stable amd64
            for entry in channel_map:
                ch = entry.get("channel", {})
                if ch.get("architecture") == "amd64" and ch.get("risk") == "stable":
                    selected_amd64 = entry
                    break

        logs.append(json.dumps({
            "publisher": snap_meta.get("publisher", {}),
            "canal_alvo": target_channel,
            "stable_amd64": selected_amd64,
            "stable_tracks_amd64": tracks_summary,
        }, indent=2, ensure_ascii=False) + "\n")

        entry_res: dict[str, object] = {
            "snap": snap_name,
            "canal_selecionado": (selected_amd64.get("channel", {}).get("name") if selected_amd64 else target_channel),
            "publisher": snap_meta.get("publisher", {}).get("display-name"),
            "publisher_validation": snap_meta.get("publisher", {}).get("validation"),
            "canais_stable_amd64": tracks_summary,
        }

        if not selected_amd64:
            snaps_results[app_key] = entry_res
            continue

        dl_info = selected_amd64.get("download", {})
        dl_url = dl_info.get("url")
        dl_size = dl_info.get("size", 0)
        expected_sha3 = dl_info.get("sha3-384")
        rev = selected_amd64.get("revision")

        entry_res.update({
            "versao": selected_amd64.get("version"),
            "revisao": rev,
            "confinement": selected_amd64.get("confinement"),
            "base": selected_amd64.get("base"),
            "download_bytes": dl_size,
            "download_mib": round(dl_size / (1024 * 1024), 2),
            "sha3_384_esperado": expected_sha3,
        })

        if skip_snap_download or not dl_url:
            entry_res["inspecao_local"] = {
                "executado": False,
                "motivo": "Download ignorado via --skip-snap-download" if skip_snap_download else "URL ausente",
            }
            snaps_results[app_key] = entry_res
            continue

        snap_file = snap_cache / f"{snap_name}_{rev}.snap"
        if not snap_file.exists() or (dl_size and snap_file.stat().st_size != dl_size):
            print(f"    Baixando {snap_file.name} ({entry_res['download_mib']} MiB)...")
            r_dl = run_cmd([curl_bin, "-4", "-fsSL", dl_url, "-o", str(snap_file)])
            logs.append(format_log_entry(r_dl))

        if not snap_file.exists():
            entry_res["inspecao_local"] = {"executado": False, "motivo": "Falha ao baixar arquivo .snap"}
            snaps_results[app_key] = entry_res
            continue

        # Hash SHA3-384 incremental para não estourar RAM em snaps grandes (ex.: Blender)
        h = hashlib.sha3_384()
        with snap_file.open("rb") as fh:
            for chunk in iter(lambda: fh.read(4 * 1024 * 1024), b""):
                h.update(chunk)
        sha3_actual = h.hexdigest()

        r_super = run_cmd([unsquashfs_bin, "-s", str(snap_file)])
        r_yaml = run_cmd([unsquashfs_bin, "-cat", str(snap_file), "meta/snap.yaml"])
        logs.append(f"=== Snap inspeção local: {snap_file.name} ===")
        logs.extend([format_log_entry(r_super), format_log_entry(r_yaml)])

        # Preencher confinement e base a partir de meta/snap.yaml quando a API v2 omitir esses campos
        if r_yaml["returncode"] == 0:
            m_conf = re.search(r"^confinement:\s*(\S+)", r_yaml["stdout"], re.MULTILINE)
            m_base = re.search(r"^base:\s*(\S+)", r_yaml["stdout"], re.MULTILINE)
            if m_conf and not entry_res.get("confinement"):
                entry_res["confinement"] = m_conf.group(1)
            if m_base and not entry_res.get("base"):
                entry_res["base"] = m_base.group(1)

        with tempfile.TemporaryDirectory(prefix=f"so-s5-snap-{app_key}-") as tmp_snap:
            ts_path = Path(tmp_snap)
            ext_dir = ts_path / "extracted"

            # Para snaps até 120 MiB ou quando --full-squashfs-bench é passado, extrai árvore inteira;
            # para snaps gigantes (> 120 MiB), extrai meta + binário principal (+ subárvore de libs configurada).
            is_large_snap = snap_file.stat().st_size > 120 * 1024 * 1024 and not full_squashfs_bench
            if not is_large_snap:
                r_ext = run_cmd([unsquashfs_bin, "-d", str(ext_dir), "-quiet", str(snap_file)])
                logs.append(format_log_entry(r_ext))
                bench_target = ext_dir
                bench_scope = "arvore_completa"
            else:
                ext_dir.mkdir(parents=True, exist_ok=True)
                extra_paths = cfg.get("snap_extra_bench_paths", [])
                run_cmd([
                    unsquashfs_bin, "-d", str(ext_dir), "-quiet", str(snap_file),
                    "meta", *cfg["snap_bin_candidates"], *extra_paths,
                ])
                bench_target = ext_dir
                extra_lbl = f" + {','.join(extra_paths)}" if extra_paths else ""
                bench_scope = f"subarvore_meta_e_binario_principal{extra_lbl} (snap > 120 MiB; use --full-squashfs-bench para árvore completa)"

            unpacked_bytes = sum(p.stat().st_size for p in bench_target.rglob("*") if p.is_file() and not p.is_symlink())
            unpacked_files = sum(1 for p in bench_target.rglob("*") if p.is_file() or p.is_symlink())

            # Inspeção ELF do binário principal extraído
            elf_info = None
            found_bin = None
            for cand in cfg["snap_bin_candidates"]:
                p_cand = ext_dir / cand
                if p_cand.is_file():
                    found_bin = p_cand
                    r_elf = run_cmd(f'{readelf_bin} -d "{p_cand}" | grep -E "NEEDED|RUNPATH|RPATH" || true', shell=True)
                    logs.append(format_log_entry(r_elf))
                    elf_info = parse_readelf_dynamic(r_elf["stdout"])
                    break

            # Benchmark SquashFS (xz vs zstd vs gzip) instrumentado com GNU time (RAM e CPU)
            sq_bench: dict[str, dict] = {}
            if unpacked_bytes > 0:
                for comp in ("xz", "zstd", "gzip"):
                    pack_ms, unpack_ms = [], []
                    pack_rusage: list[dict | None] = []
                    unpack_rusage: list[dict | None] = []
                    img_size = 0
                    for rep in range(1, reps + 1):
                        img_out = ts_path / f"bench-{comp}-{rep}.snap"
                        r_mk = run_cmd_timed(time_bin, [mksquashfs_bin, str(bench_target), str(img_out), "-comp", comp, "-noappend", "-quiet"])
                        pack_ms.append(r_mk["elapsed_ms"])
                        pack_rusage.append(r_mk.get("rusage"))
                        img_size = img_out.stat().st_size if img_out.exists() else 0
                        out_dir = ts_path / f"un-{comp}-{rep}"
                        r_un = run_cmd_timed(time_bin, [unsquashfs_bin, "-d", str(out_dir), "-quiet", str(img_out)])
                        unpack_ms.append(r_un["elapsed_ms"])
                        unpack_rusage.append(r_un.get("rusage"))
                    sq_bench[comp] = {
                        "tamanho_imagem_bytes": img_size,
                        "tamanho_imagem_mib": round(img_size / (1024 * 1024), 2),
                        "razao_compressao": round(img_size / unpacked_bytes, 3),
                        "tempo_compressao_ms": summarize_series(pack_ms),
                        "recursos_compressao": summarize_rusage_series(pack_rusage),
                        "tempo_extracao_ms": summarize_series(unpack_ms),
                        "recursos_extracao": summarize_rusage_series(unpack_rusage),
                    }

            entry_res["inspecao_local"] = {
                "executado": True,
                "arquivo_cache": str(snap_file),
                "tamanho_snap_bytes": snap_file.stat().st_size,
                "sha3_384_verificado": sha3_actual,
                "sha3_384_coincide": sha3_actual == expected_sha3,
                "superbloco_squashfs": parse_unsquashfs_superblock(r_super["stdout"]),
                "binario_inspecionado": str(found_bin.relative_to(ext_dir)) if found_bin else None,
                "elf": elf_info,
                "escopo_benchmark_squashfs": bench_scope,
                "amostra_descompactada_bytes": unpacked_bytes,
                "amostra_descompactada_mib": round(unpacked_bytes / (1024 * 1024), 2),
                "amostra_arquivos": unpacked_files,
                "comparacao_squashfs": sq_bench,
            }

        snaps_results[app_key] = entry_res

    metrics = {
        "alinhamento_versoes": align_versions,
        "kernel_lsm_ativos": lsm,
        "apparmor_ativo_no_kernel": "apparmor" in lsm.split(","),
        "observacao_confinamento": (
            "Mesmo quando o metadado declara confinement=strict (gnome-text-editor, vlc), o confinamento "
            "efetivo do Snap depende do módulo LSM AppArmor ativo no kernel; já o Blender declara "
            "confinement=classic, abrindo mão do confinamento estrito mesmo em kernels com AppArmor."
        ),
        "aplicacoes": snaps_results,
    }
    (EVID_DIR / "snap-testes-finais.txt").write_text("\n".join(logs))
    (EVID_DIR / "snap-testes-finais.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    return metrics


# =============================================================================
# CLI E ORQUESTRAÇÃO
# =============================================================================

def parse_csv_choices(raw: str, valid: tuple[str, ...], flag_name: str) -> list[str]:
    items = [x.strip() for x in raw.split(",") if x.strip()]
    if not items or "all" in items:
        return list(valid)
    unknown = [x for x in items if x not in valid]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"Valor inválido em {flag_name}: {unknown}. Opções válidas: all, {', '.join(valid)}"
        )
    # Preservar ordem sem duplicatas
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Executa a bateria final de testes (Semana 5) com GNOME Text Editor, VLC e Blender."
    )
    parser.add_argument(
        "--only",
        default="all",
        help=f"Etapas a executar separadas por vírgula (padrão: all). Opções: all,{','.join(ALL_STAGES)}",
    )
    parser.add_argument(
        "--apps",
        default="all",
        help=f"Aplicações a testar separadas por vírgula (padrão: all). Opções: all,{','.join(APPS.keys())}",
    )
    parser.add_argument(
        "--reps",
        type=int,
        default=3,
        help="Número de repetições por medição temporizada (padrão: 3).",
    )
    parser.add_argument(
        "--align-versions",
        choices=("debian", "latest"),
        default="debian",
        help=(
            "Estratégia de alinhamento de versões entre gerenciadores (padrão: debian). "
            "'debian' fixa Nix, FreeBSD Ports e canais Snap nas versões do Debian trixie "
            "(GNOME Text Editor 48.3, VLC 3.0.24, Blender 4.3.x); 'latest' usa o estado mais recente de cada repositório."
        ),
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help=f"Diretório de cache para .deb e .snap (padrão: {DEFAULT_CACHE_DIR}).",
    )
    parser.add_argument(
        "--build-source",
        action="store_true",
        help="Na etapa FreeBSD Ports, tenta também compilar localmente o tarball oficial do gnome-text-editor (Meson/Ninja).",
    )
    parser.add_argument(
        "--skip-snap-download",
        action="store_true",
        help="Na etapa Snap, consulta apenas a API v2 da Snap Store sem baixar os arquivos .snap.",
    )
    parser.add_argument(
        "--full-squashfs-bench",
        action="store_true",
        help="Recompacta árvore inteira no benchmark SquashFS mesmo para snaps > 120 MiB (mais lento).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verifica ferramentas disponíveis e exibe o plano de execução sem rodar os experimentos.",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    stages = parse_csv_choices(args.only, ALL_STAGES, "--only")
    selected_apps = parse_csv_choices(args.apps, tuple(APPS.keys()), "--apps")
    if args.reps < 1:
        parser.error("--reps deve ser >= 1")

    tools = ToolResolver(allow_nix_build=not args.dry_run)

    if args.dry_run:
        print("=== MODO DRY-RUN (nenhum experimento será executado) ===")
        print("Etapas selecionadas :", ", ".join(stages))
        print("Aplicações          :", ", ".join(selected_apps))
        print("Repetições          :", args.reps)
        print("Alinhamento versões :", args.align_versions)
        print("Cache dir           :", args.cache_dir)
        print("Build fonte (Ports) :", args.build_source)
        print("Skip Snap download  :", args.skip_snap_download)
        print("Full SquashFS bench :", args.full_squashfs_bench)
        print("\nFerramentas detectadas no host (PATH ou /nix/store existente):")
        for tool_name, tool_path in tools.snapshot().items():
            status = tool_path if tool_path else "NÃO ENCONTRADA (será resolvida via nix build na execução real)"
            print(f"  - {tool_name:11s}: {status}")
        print("\nIdentificadores e referências das aplicações selecionadas:")
        for app_key in selected_apps:
            c = APPS[app_key]
            ports_ref = c["freebsd_ref_aligned"] if args.align_versions == "debian" else "main"
            nix_ref = _get_nix_flake_ref(app_key, args.align_versions)
            snap_ch = c["snap_channel_aligned"] if args.align_versions == "debian" else "latest/stable"
            print(
                f"  - {c['titulo']} (alvo Debian {c['versao_alvo_debian']}):\n"
                f"      Debian  : {c['debian_pkg']} (debian:trixie-slim)\n"
                f"      Ports   : {c['freebsd_port']} @ {ports_ref[:12]}\n"
                f"      Nix     : {nix_ref}\n"
                f"      Flatpak : {c['flatpak_id']} (Flathub stable; bwrap executa binário Nix alinhado)\n"
                f"      Snap    : {c['snap_name']} [{snap_ch}]"
            )
        return 0

    EVID_DIR.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, object] = {
        "gerado_em_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "parametros": {
            "etapas": stages,
            "aplicacoes": selected_apps,
            "repeticoes": args.reps,
            "align_versions": args.align_versions,
            "build_source": args.build_source,
            "skip_snap_download": args.skip_snap_download,
            "full_squashfs_bench": args.full_squashfs_bench,
        },
    }

    nix_store_paths: dict[str, str] = {}

    if "env" in stages:
        summary["ambiente"] = collect_environment(tools)
    if "debian" in stages:
        summary["debian"] = run_debian_experiments(tools, selected_apps, args.reps, args.cache_dir)
    if "ports" in stages:
        summary["freebsd_ports"] = run_ports_experiments(
            tools, selected_apps, args.reps, args.build_source, align_versions=args.align_versions
        )
    if "nix" in stages:
        nix_metrics, nix_store_paths = run_nix_experiments(
            tools, selected_apps, args.reps, align_versions=args.align_versions
        )
        summary["nix"] = nix_metrics
    if "flatpak" in stages:
        summary["flatpak"] = run_flatpak_experiments(
            tools, selected_apps, args.reps, nix_store_paths, align_versions=args.align_versions
        )
    if "snap" in stages:
        summary["snap"] = run_snap_experiments(
            tools,
            selected_apps,
            args.reps,
            args.cache_dir,
            args.skip_snap_download,
            args.full_squashfs_bench,
            align_versions=args.align_versions,
        )

    out_summary = EVID_DIR / "resumo-testes-finais.json"
    out_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(f"\nConcluído! Evidências e resumo consolidado salvos em: {EVID_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
