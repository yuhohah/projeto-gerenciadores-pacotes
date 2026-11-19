#!/usr/bin/env python3
"""Demonstração visual em terminal (para gravação de vídeo) usando apenas o GNU hello.

Executa os testes comparativos diretamente no terminal atual (sem abrir novas janelas
ou aplicativos gráficos), imprimindo cada comando e sua saída real em tempo real.

Uso:
  python3 demo_video_hello.py           # executa tudo continuamente
  python3 demo_video_hello.py --pause   # pausa entre blocos (Enter para avançar)
  python3 demo_video_hello.py --skip-build  # pula a compilação (~40s) se quiser vídeo curto
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

# Caminhos nativos no host NixOS
HELLO_NIX = "/nix/store/sd779x86bjaqxj2lzh2jsir4h0zjz6d1-hello-2.12.3"
BWRAP_BIN = "/nix/store/m50dfhnbbqpvj79i444kcdd2zsfwr4hk-bubblewrap-0.13.1/bin/bwrap"
OSTREE_BIN = "/nix/store/57a720jdismlqv2a708hi7kmb7rins36-ostree-2026.2/bin/ostree"
SQUASHFS_DIR = "/nix/store/cgj65l0kswbz928pq40ybf4jb34yndbi-squashfs-tools-4.7.5/bin"
MKSQUASHFS_BIN = f"{SQUASHFS_DIR}/mksquashfs"
UNSQUASHFS_BIN = f"{SQUASHFS_DIR}/unsquashfs"
STRACE_BIN = "/nix/store/78jn0lxqjgz4ahjzvvh4rvan7p607xph-strace-7.2/bin/strace"
READELF_BIN = "/nix/store/45qppvrgigcmyjina7a6p82f2pf5kzmr-binutils-2.46/bin/readelf"
TOOLCHAIN_PATH = ":".join([
    "/nix/store/ii6p6kc1brz3vycqg88q4zb4xd2dmqwp-gcc-wrapper-16.2.0/bin",
    "/nix/store/71c91xjkcj07khl9imgmgji5wzrxwy65-gnumake-4.4.1/bin",
    "/nix/store/gfkkr23q11kvyz6xxyxz3qbsp1msxdcv-gettext-1.0/bin",
    os.environ.get("PATH", ""),
])

BOLD = "\033[1m"
CYAN = "\033[36m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


def banner(title: str) -> None:
    print(f"\n{BOLD}{BLUE}{'=' * 76}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 76}{RESET}\n", flush=True)


def run_live(display_cmd: str, cmd: list[str] | str, cwd: Path | None = None, shell: bool = False, check: bool = True, spinner: bool = False) -> tuple[int, float]:
    print(f"{BOLD}{CYAN}$ {display_cmd}{RESET}", flush=True)
    env = os.environ.copy()
    env["LC_ALL"] = "C.UTF-8"
    env["PATH"] = TOOLCHAIN_PATH
    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=str(cwd) if cwd else None, shell=shell, env=env)
    is_tty = sys.stdout.isatty() and spinner
    shown_spinner = False
    frames = "|/-\\"
    idx = 0
    while True:
        try:
            proc.wait(timeout=0.1)
            break
        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - t0
            if is_tty and elapsed >= 0.4:
                shown_spinner = True
                sys.stdout.write(f"\r{DIM}  [{frames[idx % 4]}] executando... {elapsed:5.1f} s{RESET}")
                sys.stdout.flush()
                idx += 1
    if shown_spinner:
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
    ms = (time.perf_counter() - t0) * 1000.0
    color = GREEN if proc.returncode == 0 else YELLOW
    print(f"{DIM}{color}-> saída: {proc.returncode} | tempo: {ms:.2f} ms{RESET}\n", flush=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"Comando falhou ({proc.returncode}): {display_cmd}")
    return proc.returncode, ms


def maybe_pause(pause: bool, msg: str = "Pressione Enter para o próximo bloco...") -> None:
    if pause:
        input(f"{DIM}[{msg}]{RESET} ")
        if sys.stdout.isatty():
            sys.stdout.write("\033[A\r\033[K")
            sys.stdout.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo visual do GNU hello para gravação de vídeo.")
    parser.add_argument("--pause", action="store_true", help="Aguarda Enter entre cada seção")
    parser.add_argument("--skip-build", action="store_true", help="Pula a compilação do tarball GNU hello")
    args = parser.parse_args()

    cache_dir = Path("/tmp/demo-so-hello-cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="demo-hello-", dir="/tmp") as tmp_root:
        work = Path(tmp_root)

        # ------------------------------------------------------------------
        banner("0. AMBIENTE HOSPEDEIRO (NixOS + Kernel Linux + LSMs)")
        run_live("uname -srm", ["uname", "-srm"])
        run_live("cat /sys/kernel/security/lsm", "cat /sys/kernel/security/lsm; echo", shell=True)
        print(f"{DIM}Nota: Nix, OSTree, Bubblewrap e SquashFS rodam nativos no host; apenas o Debian usa container FHS.{RESET}\n")
        maybe_pause(args.pause)

        # ------------------------------------------------------------------
        banner("1. DEBIAN (APT/dpkg em container debian:trixie-slim — mesmo kernel)")
        deb_cache = cache_dir / "debs"
        deb_cache.mkdir(exist_ok=True)
        if not list(deb_cache.glob("hello_*.deb")):
            run_live(
                "docker run --rm -v cache:/cache debian:trixie-slim bash -c 'apt-get update -qq && apt-get install --download-only -y hello && cp /var/cache/apt/archives/hello_*.deb /cache/'",
                [
                    "docker", "run", "--rm", "-v", f"{deb_cache}:/cache",
                    "debian:trixie-slim", "bash", "-c",
                    "apt-get update -qq >/dev/null && apt-get install --download-only -y hello >/dev/null && cp /var/cache/apt/archives/hello_*.deb /cache/ && ls -lh /cache/hello_*.deb",
                ],
            )
        else:
            run_live("ls -lh /tmp/demo-so-hello-cache/debs/hello_*.deb", f"ls -lh {deb_cache}/hello_*.deb", shell=True)

        debian_demo = f"""
set -e
echo "=== Instalacao local (sem rede) com dpkg -i ==="
t0=$(date +%s%N); dpkg -i /cache/hello_*.deb >/dev/null; t1=$(date +%s%N)
echo "Tempo dpkg -i: $(( (t1 - t0) / 1000000 )) ms"
echo ""
echo "=== Arquivos espalhados no FHS (amostra) ==="
dpkg -L hello | head -n 12
echo ""
echo "=== Cabecalho ELF e bibliotecas de /usr/bin/hello ==="
{READELF_BIN} -d /usr/bin/hello | grep -E "NEEDED|RUNPATH|RPATH" || true
ldd /usr/bin/hello
echo ""
echo "=== Execucao direta ==="
/usr/bin/hello
echo ""
echo "=== Perfil de syscalls da instalacao (strace -c -f dpkg -i) ==="
{STRACE_BIN} -c -f dpkg -i /cache/hello_*.deb 2>&1 >/dev/null | tail -n 12
"""
        run_live(
            "docker run --rm --network=none --cap-add=SYS_PTRACE debian:trixie-slim <teste dpkg + readelf + strace>",
            [
                "docker", "run", "--rm", "--network=none", "--cap-add=SYS_PTRACE",
                "-v", f"{deb_cache}:/cache:ro",
                "-v", "/nix/store:/nix/store:ro",
                "debian:trixie-slim", "bash", "-c", debian_demo,
            ],
        )
        maybe_pause(args.pause)

        # ------------------------------------------------------------------
        banner("2. FREEBSD PORTS (receita misc/hello) + COMPILACAO COM vs. SEM NLS")
        run_live(
            "curl -sL https://cgit.freebsd.org/ports/plain/misc/hello/Makefile | grep -E 'PORTNAME|PORTVERSION|OPTIONS_DEFINE|NLS_'",
            "curl -4 -sL https://cgit.freebsd.org/ports/plain/misc/hello/Makefile | grep -E 'PORTNAME|PORTVERSION|OPTIONS_DEFINE|NLS_'",
            shell=True,
        )
        if not args.skip_build:
            tarball = cache_dir / "hello-2.12.3.tar.gz"
            if not tarball.exists():
                run_live(
                    "curl -4 -sL https://ftpmirror.gnu.org/gnu/hello/hello-2.12.3.tar.gz -o hello-2.12.3.tar.gz",
                    ["curl", "-4", "-sL", "https://ftpmirror.gnu.org/gnu/hello/hello-2.12.3.tar.gz", "-o", str(tarball)],
                )
            for label, flag in [("COM NLS (--enable-nls)", "--enable-nls"), ("SEM NLS (--disable-nls)", "--disable-nls")]:
                print(f"{BOLD}{YELLOW}--- Compilando hello-2.12.3 {label} ---{RESET}", flush=True)
                bdir = work / f"build-{flag.lstrip('-')}"
                sdir = work / f"stage-{flag.lstrip('-')}"
                bdir.mkdir(); sdir.mkdir()
                run_live(
                    f"tar -xzf hello-2.12.3.tar.gz && ./configure {flag} && make -j4 && make DESTDIR=stage install",
                    f"tar -xzf {tarball} -C {bdir} && cd {bdir}/hello-2.12.3 && "
                    f"./configure --prefix=/usr/local {flag} >/dev/null && "
                    f"make -j4 >/dev/null && make DESTDIR={sdir} install >/dev/null",
                    shell=True,
                    spinner=True,
                )
                files = [p for p in sdir.rglob("*") if p.is_file()]
                total_b = sum(p.stat().st_size for p in files)
                print(f"Arquivos instalados: {len(files)} | Tamanho real: {total_b / 1024:.1f} KiB ({total_b} B)\n", flush=True)
        else:
            print(f"{DIM}(Compilação pulada via --skip-build){RESET}\n")
        maybe_pause(args.pause)

        # ------------------------------------------------------------------
        banner("3. NIX (Store imutavel, RUNPATH no ELF e rollback atomico)")
        run_live(f"nix path-info -s -S -h {HELLO_NIX}", ["nix", "path-info", "-s", "-S", "-h", HELLO_NIX])
        run_live(
            f"readelf -d {HELLO_NIX}/bin/hello | grep -E 'NEEDED|RUNPATH'",
            f"{READELF_BIN} -d {HELLO_NIX}/bin/hello | grep -E 'NEEDED|RUNPATH'",
            shell=True,
        )
        prof = work / "perfil-hello"
        run_live(f"nix profile add --profile {prof} {HELLO_NIX}", ["nix", "profile", "add", "--profile", str(prof), HELLO_NIX])
        run_live(f"{prof}/bin/hello", [str(prof / "bin/hello")])
        run_live(f"nix profile remove --profile {prof} --all", ["nix", "profile", "remove", "--profile", str(prof), "--all"])
        run_live(
            f"strace -qq -c -f -e trace=symlink,symlinkat,rename,renameat,renameat2,flock nix profile rollback --profile {prof}",
            [STRACE_BIN, "-qq", "-c", "-f", "-e", "trace=symlink,symlinkat,rename,renameat,renameat2,flock", "nix", "profile", "rollback", "--profile", str(prof)],
        )
        run_live(f"{prof}/bin/hello (apos rollback)", [str(prof / "bin/hello")])
        maybe_pause(args.pause)

        # ------------------------------------------------------------------
        banner("4. FLATPAK (OSTree + Bubblewrap) E SNAP (SquashFS) NO GNU hello")
        # OSTree hardlinks
        repo = work / "ostree-repo"
        t1 = work / "hello-v1"
        t2 = work / "hello-v2"
        shutil.copytree(HELLO_NIX, t1)
        shutil.copytree(HELLO_NIX, t2)
        (t2 / "share/man/man1/hello.1.gz").chmod(0o644)
        (t2 / "share/man/man1/hello.1.gz").write_bytes((t1 / "share/man/man1/hello.1.gz").read_bytes() + b"\x00")
        c1 = work / "co-v1"
        c2 = work / "co-v2"
        run_live(
            "ostree init/commit v1 & v2 (alterando apenas o manual) + stat nos inodes",
            f"{OSTREE_BIN} init --repo={repo} --mode=bare-user && "
            f"REV1=$({OSTREE_BIN} commit --repo={repo} --branch=app/org.gnu.Hello/x86_64/stable {t1}) && "
            f"REV2=$({OSTREE_BIN} commit --repo={repo} --branch=app/org.gnu.Hello/x86_64/stable {t2}) && "
            f"{OSTREE_BIN} checkout --repo={repo} -U $REV1 {c1} && "
            f"{OSTREE_BIN} checkout --repo={repo} -U $REV2 {c2} && "
            f"stat -c 'inode=%i hardlinks=%h arquivo=%n' {c1}/bin/hello {c2}/bin/hello {c1}/share/man/man1/hello.1.gz {c2}/share/man/man1/hello.1.gz",
            shell=True,
        )

        # Bubblewrap sandbox + permissoes
        pasta_teste = work / "pasta-usuario"
        pasta_teste.mkdir()
        (pasta_teste / "segredo.txt").write_text("conteudo privado do usuario\n")
        run_live(
            f"bwrap --unshare-all ... {HELLO_NIX}/bin/hello",
            [BWRAP_BIN, "--ro-bind", "/nix", "/nix", "--ro-bind", "/run", "/run", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--unshare-all", f"{HELLO_NIX}/bin/hello"],
        )
        run_live(
            "bwrap SEM bind da pasta do usuario (tentando ler segredo.txt)",
            [BWRAP_BIN, "--ro-bind", "/nix", "/nix", "--ro-bind", "/run", "/run", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--unshare-all", "/run/current-system/sw/bin/cat", str(pasta_teste / "segredo.txt")],
            check=False,
        )
        run_live(
            "bwrap COM --ro-bind (leitura OK, tentativa de escrita bloqueada)",
            [BWRAP_BIN, "--ro-bind", "/nix", "/nix", "--ro-bind", "/run", "/run", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--unshare-all", "--ro-bind", str(pasta_teste), str(pasta_teste), "/run/current-system/sw/bin/sh", "-c", f"cat {pasta_teste}/segredo.txt && echo teste > {pasta_teste}/novo.txt"],
            check=False,
        )

        # SquashFS (Snap)
        snap_xz = work / "hello-xz.snap"
        snap_zstd = work / "hello-zstd.snap"
        run_live(
            "mksquashfs (xz vs zstd) na arvore do GNU hello",
            f"{MKSQUASHFS_BIN} {HELLO_NIX} {snap_xz} -comp xz -noappend -no-progress -quiet && "
            f"{MKSQUASHFS_BIN} {HELLO_NIX} {snap_zstd} -comp zstd -noappend -no-progress -quiet && "
            f"ls -lh {snap_xz} {snap_zstd}",
            shell=True,
        )

    banner("FIM DA DEMONSTRACAO (GNU hello)")


if __name__ == "__main__":
    main()
