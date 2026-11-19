# Protocolo experimental e resultados detalhados — Semana 4

**Data da coleta:** 18 de novembro de 2026 (`15:12 UTC` / `12:12 BRT`).  
**Script de execução reprodutível:** [evidencias/executar_experimentos.py](./evidencias/executar_experimentos.py).  
**Resumo estruturado (JSON):** [evidencias/resumo-comparativo.json](./evidencias/resumo-comparativo.json).

Este documento detalha o protocolo experimental seguido na Semana 4, apresentando os valores individuais das três repetições de cada teste, as tabelas de chamadas de sistema (`strace -c -f`), a inspeção de vinculação dinâmica (`readelf -d` e `ldd`) e os comandos para reprodução.

---

## 1. Especificação do ambiente experimental

Registros brutos em [evidencias/ambiente-experimental.txt](./evidencias/ambiente-experimental.txt) e [evidencias/ambiente-experimental.json](./evidencias/ambiente-experimental.json):

- **CPU:** `AMD Ryzen 5 2600 Six-Core Processor` (`x86_64`, 6 núcleos físicos, 12 threads, NUMA node 0: CPUs 0–11).
- **Memória e disco:** 15 GiB de RAM (`16.668.938.240 bytes`); partição raiz em SSD NVMe (`/dev/nvme0n1p6`, 341 GiB totais, 106 GiB livres).
- **Sistema operacional hospedeiro:** `NixOS 26.11.20261111.d4f25a3 (Zokor)`, kernel Linux `7.3.4 #1-NixOS SMP PREEMPT_DYNAMIC`.
- **Revisão Nixpkgs do sistema:** `d4f25a3e562008648d45bcf2d70bcc7422cad84e`.
- **Módulos LSM ativos no kernel (`/sys/kernel/security/lsm`):** `lockdown,capability,landlock,yama,bpf,ima`.
- **Controladores cgroup v2 (`/sys/fs/cgroup/cgroup.controllers`):** `cpuset cpu io memory hugetlb pids rdma misc dmem`.
- **Versões das ferramentas verificadas:**
  - `nix (Nix) 2.35.6`
  - `Docker version 29.9.2, build v29.9.2`
  - `Flatpak 1.18.4`
  - `bubblewrap 0.13.1`
  - `libostree Version: '2026.2'`
  - `mksquashfs / unsquashfs version 4.7.5 (2026/03/01)`
  - `strace -- version 7.2`
  - `GNU readelf (GNU Binutils) 2.46`

---

## 2. Experimento 1 — Debian (`APT 3.0.4` / `dpkg 1.22.22`)

Registros completos em [evidencias/debian-apt-dpkg.txt](./evidencias/debian-apt-dpkg.txt) e [evidencias/debian-metricas.json](./evidencias/debian-metricas.json).  
**Ambiente:** container oficial `debian:trixie-slim` (`Debian GNU/Linux 13.7 (trixie)`), isolando a árvore de diretórios FHS e o banco de dados `/var/lib/dpkg`.

### 2.1. Download, metadados e estrutura `.deb`

Os pacotes `.deb` foram baixados previamente com `apt-get install --download-only -y tmux hello`:

| Pacote `.deb` baixado | Tamanho do arquivo `.deb` | `Installed-Size` declarado | Papel na instalação |
| :--- | :---: | :---: | :--- |
| `hello_2.10-5_amd64.deb` | 53.228 B (51,98 KiB) | 280 KiB | Utilitário `hello` (depende apenas de `libc6` já presente) |
| `tmux_3.5a-3_amd64.deb` | 490.296 B (478,80 KiB) | 1.209 KiB | Multiplexador de terminais `tmux` |
| `libevent-core-2.1-7t64_2.1.13-stable-1~deb13u1_amd64.deb` | 132.868 B (129,75 KiB) | 380 KiB | Dependência de eventos assíncronos do `tmux` |
| `libjemalloc2_5.3.0-3_amd64.deb` | 274.324 B (267,89 KiB) | 866 KiB | Alocador de memória exigido pelo `tmux` no Debian 13 |
| **Total do conjunto `tmux` (3 pacotes `.deb`)** | **897.488 B (876,45 KiB)** | **2.455 KiB** | Conjunto instalado pelo `dpkg -i` no piloto |

### 2.2. Tempos de instalação local (`dpkg -i`, sem rede) e execução

Cada repetição foi executada em um container `debian:trixie-slim` recém-criado com `--network=none` e os arquivos `.deb` pré-carregados em memória/disco local:

| Operação medida no Debian 13 (`trixie-slim`) | Repetição 1 | Repetição 2 | Repetição 3 | Média | Mediana | Desvio-padrão ($\sigma$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Instalação local `hello` (`1 .deb`)** | 37,00 ms | 38,00 ms | 37,00 ms | **37,33 ms** | 37,00 ms | 0,58 ms |
| **Instalação local `tmux` + 2 deps (`3 .deb`)** | 161,00 ms | 162,00 ms | 162,00 ms | **161,67 ms** | 162,00 ms | 0,58 ms |
| **Execução `/usr/bin/hello`** | 1,00 ms | 1,00 ms | 1,00 ms | **1,00 ms** | 1,00 ms | 0,00 ms |
| **Execução `/usr/bin/tmux -V`** | 4,00 ms | 4,00 ms | 3,00 ms | **3,67 ms** | 4,00 ms | 0,58 ms |

### 2.3. Perfil de chamadas de sistema (`strace -c -f`) no `dpkg -i`

| Chamada de sistema (syscall) | `dpkg -i hello` (1 pacote) | `dpkg -i tmux` + 2 deps (3 pacotes) | Função no nível do SO (VFS / Processos) |
| :--- | :---: | :---: | :--- |
| `read` | 396 | 984 | Leitura dos arquivos `.deb` e metadados de `/var/lib/dpkg` |
| `close` | 268 | 935 | Fechamento de descritores após extração e atualização de status |
| `openat` | 252 | 642 | Abertura de arquivos de controle, `.list`, `.md5sums` e destinos FHS |
| `newfstatat` / `fstat` | 277 / 157 | 570 / 493 | Verificação de existência e permissões de arquivos/diretórios |
| `write` | 60 | 371 | Escrita dos binários extraídos e atualização do banco de dados |
| `rename` | **146** | **77** | Substituição atômica por arquivo (`.dpkg-new` $\to$ caminho final) |
| `fsync` | **21** | **81** | Persistência explícita em disco dos arquivos e registros do `dpkg` |
| `fcntl` | **44** | **192** | Travas de concorrência (`F_SETLK`) sobre `/var/lib/dpkg/lock` e flags de FD |
| `clone` / `vfork` | 11 / 0 | 60 / 13 | Criação de processos filhos (`dpkg-deb`, `tar`, scripts `postinst`) |
| `execve` | 21 | 100 | Execução de binários auxiliares e scripts de manutenção |
| **Total de syscalls** | **2.478** (685 erros) | **7.904** (585 erros) | Cresce com o número de pacotes, arquivos e scripts `postinst` |

---

## 3. Experimento 2 — FreeBSD Ports (`misc/hello`) e compilação do código-fonte

Registros completos em [evidencias/freebsd-ports-e-compilacao-hello.txt](./evidencias/freebsd-ports-e-compilacao-hello.txt) e [evidencias/ports-compilacao-metricas.json](./evidencias/ports-compilacao-metricas.json).

### 3.1. Receita oficial verificada na árvore FreeBSD Ports

```makefile
PORTNAME=	hello
PORTVERSION=	2.12.3
CATEGORIES=	misc
MASTER_SITES=	GNU
LICENSE=	GPLv3+
USES=		charsetfix gmake perl5
USE_PERL5=	build
GNU_CONFIGURE=	yes
INFO=		hello
OPTIONS_DEFINE=	NLS
OPTIONS_SUB=	yes
NLS_CONFIGURE_ENABLE=	nls
NLS_USES=		gettext localbase
.include <bsd.port.mk>
```

### 3.2. Tempos das 3 repetições da construção de `hello-2.12.3.tar.gz` (`--enable-nls` vs. `--disable-nls`)

| Variante e fase da construção | Repetição 1 | Repetição 2 | Repetição 3 | Média | Mediana | Desvio-padrão ($\sigma$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Com `NLS` (`--enable-nls`) — `configure`** | 17.220,98 ms | 16.941,02 ms | 16.915,30 ms | **17.025,77 ms** | 16.941,02 ms | 169,55 ms |
| **Com `NLS` (`--enable-nls`) — `build` (`make -j4`)** | 2.018,28 ms | 2.018,49 ms | 2.040,71 ms | **2.025,83 ms** | 2.018,49 ms | 12,89 ms |
| **Com `NLS` (`--enable-nls`) — `stage/install`** | 744,56 ms | 771,57 ms | 749,84 ms | **755,33 ms** | 749,84 ms | 14,31 ms |
| **Com `NLS` (`--enable-nls`) — Total (`extract`..`stage`)** | 20.018,50 ms | 19.763,33 ms | 19.739,36 ms | **19.840,40 ms** | 19.763,33 ms | 154,71 ms |
| **Sem `NLS` (`--disable-nls`) — `configure`** | 17.071,67 ms | 16.998,01 ms | 16.925,59 ms | **16.998,43 ms** | 16.998,01 ms | 73,04 ms |
| **Sem `NLS` (`--disable-nls`) — `build` (`make -j4`)** | 1.975,74 ms | 2.019,00 ms | 1.999,99 ms | **1.998,24 ms** | 1.999,99 ms | 21,69 ms |
| **Sem `NLS` (`--disable-nls`) — `stage/install`** | 254,43 ms | 261,12 ms | 259,36 ms | **258,30 ms** | 259,36 ms | 3,47 ms |
| **Sem `NLS` (`--disable-nls`) — Total (`extract`..`stage`)** | 19.334,64 ms | 19.310,73 ms | 19.218,80 ms | **19.288,05 ms** | 19.310,73 ms | 61,16 ms |

---

## 4. Experimento 3 — Nix (`store`, perfis, gerações, rollback e `RUNPATH`)

Registros completos em [evidencias/nix-perfis-geracoes-vinculacao.txt](./evidencias/nix-perfis-geracoes-vinculacao.txt) e [evidencias/nix-metricas.json](./evidencias/nix-metricas.json).

### 4.1. Tempos das 3 repetições de operações de perfil e execução

| Operação no Nix (`2.35.6`, pacotes já no `/nix/store`) | Repetição 1 | Repetição 2 | Repetição 3 | Média | Mediana | Desvio-padrão ($\sigma$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `nix profile add` — `hello-2.12.3` (fechamento 36,73 MiB) | 38,36 ms | 37,63 ms | 36,83 ms | **37,61 ms** | 37,63 ms | 0,77 ms |
| `nix profile add` — `tmux-3.8` (fechamento 58,12 MiB) | 37,66 ms | 37,65 ms | 37,29 ms | **37,53 ms** | 37,65 ms | 0,21 ms |
| `nix profile add` — `gnome-text-editor-50.1` (fechamento 957,19 MiB) | 35,93 ms | 39,32 ms | 37,74 ms | **37,66 ms** | 37,74 ms | 1,70 ms |
| `nix profile rollback` (retorno da geração 2 para a 1) | 31,73 ms | 32,16 ms | 31,51 ms | **31,80 ms** | 31,73 ms | 0,33 ms |
| Execução `hello` | 4,04 ms | 2,86 ms | 2,93 ms | **3,28 ms** | 2,93 ms | 0,66 ms |
| Execução `tmux -V` | 2,94 ms | 2,84 ms | 2,96 ms | **2,91 ms** | 2,94 ms | 0,06 ms |
| Execução `gnome-text-editor --version` (via wrapper) | 47,46 ms | 53,15 ms | 46,20 ms | **48,94 ms** | 47,46 ms | 3,70 ms |

### 4.2. Comparação de cabeçalhos ELF (`readelf -d`) entre Debian, Nix e Snap

1. **Debian (`/usr/bin/tmux`):**
   - `NEEDED`: `libevent_core-2.1.so.7`, `libjemalloc.so.2`, `libsystemd.so.0`, `libtinfo.so.6`, `libm.so.6`, `libc.so.6`.
   - `RUNPATH` / `RPATH`: **ausente** (resolução global via `/etc/ld.so.cache` em `/lib/x86_64-linux-gnu/`).
2. **Nix (`/nix/store/7v8w4qyz...-tmux-3.8/bin/tmux`):**
   - `NEEDED`: `libsystemd.so.0`, `libutf8proc.so.3`, `libutempter.so.0`, `libncursesw.so.6`, `libevent_core-2.1.so.7`, `libm.so.6`, `libresolv.so.2`, `libc.so.6`.
   - `RUNPATH`: `/nix/store/5j2w6s0j...-systemd-minimal-libs-262/lib:/nix/store/vfnl45i7...-utf8proc-2.12.0/lib:/nix/store/adz753ps...-ncurses-6.6/lib:/nix/store/rlddw02a...-libevent-2.1.13/lib:/nix/store/p4kd0daj...-libutempter-1.2.3/lib:/nix/store/r3hvhzl5...-glibc-2.44-57/lib`.
3. **Nix (`/nix/store/94r4v2l4...-gnome-text-editor-50.1`):**
   - `bin/gnome-text-editor` (wrapper compilado): `NEEDED: [libc.so.6]`, `RUNPATH: [/nix/store/pqyiidz5...-glibc-2.44-57/lib]`.
   - `bin/.gnome-text-editor-wrapped` (binário ELF real): `NEEDED` para `libadwaita-1.so.0`, `libgtk-4.so.1`, `libgtksourceview-5.so.0`, `libspelling-1.so.2`, `libeditorconfig.so.0`, etc., e `RUNPATH` com os 14 diretórios `/nix/store/<hash>-.../lib` exatos.
4. **Snap (`usr/bin/gnome-text-editor` extraído de `gnome-text-editor_53.snap`):**
   - `NEEDED`: `libadwaita-1.so.0`, `libgtk-4.so.1`, `libgtksourceview-5.so.0`, `libspelling-1.so.2`, `libpango-1.0.so.0`, `libcairo.so.2`, `libglib-2.0.so.0`, `libeditorconfig.so.0`, `libc.so.6`.
   - `RUNPATH` / `RPATH`: **ausente**; a localização das bibliotecas é controlada por `LD_LIBRARY_PATH` e montagens `bind` definidas em `meta/snap.yaml` sobre os snaps de conteúdo `gnome-46-2404` e `core24`.

---

## 5. Experimento 4 — Flatpak (`OSTree` + `Bubblewrap`) e Snap (`SquashFS`)

Registros completos em [evidencias/flatpak-snap-isolamento-e-imagens.txt](./evidencias/flatpak-snap-isolamento-e-imagens.txt) e [evidencias/flatpak-snap-metricas.json](./evidencias/flatpak-snap-metricas.json).

### 5.1. Deduplicação por hardlinks no OSTree (`libostree 2026.2`)

Saída real de `stat -c "%i %h %s %n"` após dois commits (`41b16d91...` e `148886dd...`) e dois checkouts (`checkout-v1` e `checkout-v2`):

```text
10495777 3 262144 .../checkout-v1/libcompartilhada.bin
10495777 3 262144 .../checkout-v2/libcompartilhada.bin
10495779 2 11     .../checkout-v1/versao.txt
10495782 2 11     .../checkout-v2/versao.txt
```

- `libcompartilhada.bin` (`262.144 bytes`) manteve o **mesmo inode (`10495777`)** nos dois checkouts e no repositório (`3` hardlinks para o mesmo bloco de dados no sistema de arquivos).
- `versao.txt` (`11 bytes`), modificado entre `v1` e `v2`, recebeu **inodes distintos (`10495779` e `10495782`)**.

### 5.2. Testes de permissão de arquivos e sobrecarga de namespaces com Bubblewrap (`bwrap 0.13.1`)

| Cenário executado com `bwrap --unshare-all` | Comando executado dentro do sandbox | Código de saída | Saída / Erro observado |
| :--- | :--- | :---: | :--- |
| **1. Sem expor a pasta do documento** | `cat .../comparacao.txt` | `1` | `cat: .../comparacao.txt: No such file or directory` |
| **2. Pasta exposta como somente leitura (`--ro-bind`) — Leitura** | `cat .../comparacao.txt` | `0` | Conteúdo lido integralmente (`Resultado: aguardando`) |
| **3. Pasta exposta como somente leitura (`--ro-bind`) — Escrita** | `printf ... > .../resultado-ro.txt` | `1` | `sh: line 1: .../resultado-ro.txt: Read-only file system` |
| **4. Pasta exposta com leitura e escrita (`--bind`) — Edição** | `sed "s/aguardando/concluído/" ... > .../resultado-bwrap.txt` | `0` | Gravado e reaberto com `Resultado: concluído` |

- **Tempo de inicialização de `hello` dentro do `bwrap` (3 repetições):** `7,81 ms`, `7,72 ms`, `7,80 ms` (**média `7,78 ms`**, mediana `7,80 ms`, $\sigma = 0{,}05\text{ ms}$).
- **Chamadas de sistema do `bwrap` (`strace -c -f`):** `963` chamadas totais (`338` `openat`, `157` `newfstatat`, `92` `close`, `91` `prctl`, `44` `mmap`, `17` `mount`, `8` `mount_setattr`, `3` `capset`, `2` `clone`, `2` `pivot_root`, `2` `umount2`, `1` `unshare`).

### 5.3. Comparação de compressão SquashFS sobre o conteúdo real de `gnome-text-editor_53.snap`

Árvore de entrada extraída de `gnome-text-editor_53.snap`: **`3.124.861 bytes` (`2,98 MiB`)** em `338` arquivos (`540` inodes).

| Algoritmo | Tamanho da imagem | Razão | Compressão (Rep 1 / 2 / 3) | Média Compressão | Extração (Rep 1 / 2 / 3) | Média Extração |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`xz`** | 851.968 B (832,0 KiB) | 0,273 | 145,24 / 146,08 / 145,49 ms | **145,60 ms** | 26,18 / 28,07 / 32,94 ms | **29,06 ms** |
| **`zstd`** | 929.792 B (908,0 KiB) | 0,298 | 107,43 / 104,14 / 102,61 ms | **104,73 ms** | 17,00 / 16,54 / 16,26 ms | **16,60 ms** |
| **`gzip`** | 1.060.864 B (1.036,0 KiB) | 0,339 | 80,08 / 73,83 / 76,85 ms | **76,92 ms** | 17,15 / 17,47 / 16,91 ms | **17,18 ms** |

---

## 6. Como reproduzir toda a bateria experimental

Para reexecutar todos os experimentos e regenerar os logs e arquivos JSON de evidências nesta máquina:

```bash
cd /home/luan/Documents/SO/projeto-gerenciadores-pacotes/semana-04/evidencias
nix shell nixpkgs#gcc nixpkgs#gnumake nixpkgs#perl nixpkgs#gettext --command python3 executar_experimentos.py
```
