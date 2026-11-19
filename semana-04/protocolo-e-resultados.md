# Protocolo Experimental, Validade Metodológica e Resultados com Exemplo Único (`GNU hello`)

Este documento descreve **como os testes foram construídos e executados em um único hospedeiro `NixOS`**, analisa **a validade e os limites de cada técnica de medição** e apresenta as tabelas completas (com todas as 3 repetições individuais e contagens de chamadas de sistema via `strace -fc`) para o exemplo único de referência: **`GNU hello`**.

*(Nota: os resultados adicionais já coletados para outros pacotes estão arquivados em [`./reserva-apresentacao-futura/`](./reserva-apresentacao-futura/README.md) para uso na apresentação futura).*

---

## 1. Como os Testes Foram Realizados no NixOS e Análise de Validade

### 1.1. Hardware e Kernel Base (Comum a Todos os Testes)
- **Processador:** `AMD Ryzen 5 2600 Six-Core Processor` (`12` threads)
- **Memória e Armazenamento:** `15 GiB RAM` · `NVMe ext4` (`513 GiB` livres)
- **Sistema Operacional Hospedeiro:** `NixOS 26.11.20261111.d4f25a3 (Xantusia)`
- **Kernel:** `Linux 7.3.4` (`x86_64`) com `cgroup v2` e LSMs `lockdown,capability,landlock,yama,bpf,ima`

### 1.2. Como cada família foi executada no NixOS e por que o método é válido

| Família | Onde rodou? | Procedimento Exato Executado | Validade Científica e Limite Metodológico |
| :--- | :--- | :--- | :--- |
| **Nix (`Nix 2.35.6`)** | **Nativo no host NixOS** | Uso direto de `/nix/store/sd779x86bjaqxj2lzh2jsir4h0zjz6d1-hello-2.12.3`, `nix profile add --profile /tmp/...`, `nix profile rollback`, `readelf -d`, `ldd` e `strace -fc`. | **Validade 100% nativa:** nenhuma virtualização ou container; mede exatamente o comportamento real do Nix sobre `ext4`/NVMe. |
| **Flatpak (`OSTree 2026.2` + `Bubblewrap 0.13.1`)** | **Nativo no host NixOS** | Commit de duas versões da árvore do `hello` em repositório `OSTree` (`bare-user`), checagem de `inode` com `stat`, e execução do binário `hello` dentro do sandbox `bwrap --unshare-all` com 3 políticas de bind (`sem bind`, `--ro-bind`, `--bind`). | **Validade 100% nativa:** `ostree` e `bwrap` invocam diretamente as chamadas `linkat`, `unshare`, `mount` e `pivot_root` do kernel Linux `7.3.4`. |
| **Snap (`SquashFS 4.7.5` + verificação de LSM)** | **Nativo no host NixOS** | Empacotamento da árvore do `hello` (`246,67 KiB`) com `mksquashfs` e extração com `unsquashfs` usando `xz`, `zstd` e `gzip` (3 repetições cada), mais verificação de `/sys/kernel/security/lsm`. | **Validade alta para formato de imagem e requisito de kernel:** mede nativamente o formato `SquashFS 4.0` usado pelos `.snap` e comprova experimentalmente que o confinamento do Snap exige `AppArmor` no kernel hospedeiro. |
| **Debian (`APT 3.0.4` + `dpkg 1.22.22`)** | **Container Linux (`debian:trixie-slim`)** | Download prévio de `hello_2.10-5_amd64.deb`, seguido de 3 repetições de `dpkg -i` e `dpkg --purge hello`, inspeção `dpkg-deb -I/-c`, `readelf -d`, `ldd` e rastreamento com `strace -fc`. | **Validade exata para formato `.deb`, ELF e contagem de syscalls (`2.478`); validade condicionada para tempo de I/O:** o processo `dpkg` roda direto no kernel `7.3.4` (sem VM), mas o filesystem raiz do container usa `OverlayFS` sobre `ext4`. |
| **FreeBSD Ports (`misc/hello` `2.12.3`)** | **Receita oficial FreeBSD + compilação nativa no host** | Consulta direta do `Makefile` e `distinfo` oficiais do FreeBSD Ports (`cgit.freebsd.org/ports/plain/misc/hello/`) e compilação em 3 repetições do mesmo tarball oficial (`hello-2.12.3.tar.gz`, SHA-256 verificado) com `--enable-nls` e `--disable-nls`. | **Validade exata para o efeito da flag `NLS` sobre arquivos (`50` vs. `4`) e tamanho (`-51,6%`); validade condicionada para tempo e syscalls:** o build usa o mesmo código-fonte e flags do port, mas executa sobre kernel Linux (`GCC/glibc`) e não sobre kernel FreeBSD (`Clang/libc`). |

---

## 2. Tabelas Completas por Repetição (`GNU hello`)

### 2.1. Debian (`dpkg -i hello_2.10-5_amd64.deb`)
Arquivo de evidência: [`debian-metricas.json`](./evidencias/debian-metricas.json) e [`hello-unico-complemento.json`](./evidencias/hello-unico-complemento.json).

- **Tamanho do pacote `.deb`:** `52.616 bytes` (`51,38 KiB`)
- **Tamanho instalado declarado (`Installed-Size`):** `188 KiB`
- **Vinculação ELF (`/usr/bin/hello`):** `NEEDED: libc.so.6` (`/lib/x86_64-linux-gnu/libc.so.6`), sem `RPATH`/`RUNPATH`.

| Operação | Repetição 1 | Repetição 2 | Repetição 3 | Média ± Desvio-Padrão | Syscalls (`strace -fc`) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`dpkg -i hello_2.10-5_amd64.deb` (local)** | `37,00 ms` | `38,00 ms` | `37,00 ms` | **`37,33 ± 0,47 ms`** | **`2.478` chamadas** (`104` erros) |
| **Execução `/usr/bin/hello --version`** | `2,00 ms` | `2,00 ms` | `2,00 ms` | **`2,00 ± 0,00 ms`** | — |

---

### 2.2. FreeBSD Ports (`misc/hello`) e Compilação Controlada (`hello-2.12.3.tar.gz`)
Arquivo de evidência: [`ports-compilacao-metricas.json`](./evidencias/ports-compilacao-metricas.json).

- **Distfile oficial:** `hello-2.12.3.tar.gz` (`1.269.080 bytes` / `1.239,34 KiB`)
- **SHA-256 verificado:** `bfd006eb9fd7a1a8fd4c8ef4f6ef26b1b7f271894c51e6d2c1b021a7ec5d2929`

| Fase / Métrica (`hello 2.12.3`) | Variante | Rep. 1 | Rep. 2 | Rep. 3 | Média ± Desvio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. `./configure`** | Com `NLS` (`--enable-nls`) | `14.370,13 ms` | `14.037,51 ms` | `14.010,36 ms` | **`14.139,33 ± 163,68 ms`** |
| **1. `./configure`** | Sem `NLS` (`--disable-nls`) | `14.193,97 ms` | `13.854,75 ms` | `13.801,13 ms` | **`13.949,95 ± 174,89 ms`** |
| **2. `make -j4` (compilação)** | Com `NLS` (`--enable-nls`) | `4.812,67 ms` | `4.832,48 ms` | `4.814,69 ms` | **`4.819,95 ± 8,90 ms`** |
| **2. `make -j4` (compilação)** | Sem `NLS` (`--disable-nls`) | `4.889,22 ms` | `4.892,69 ms` | `4.882,57 ms` | **`4.888,16 ± 4,34 ms`** |
| **3. `make DESTDIR=... install` (stage)** | Com `NLS` (`--enable-nls`) | `665,33 ms` | `703,80 ms` | `694,54 ms` | **`687,89 ± 16,44 ms`** |
| **3. `make DESTDIR=... install` (stage)** | Sem `NLS` (`--disable-nls`) | `253,88 ms` | `262,88 ms` | `258,15 ms` | **`258,30 ± 3,66 ms` (`-62,5%`)** |
| **Tempo Total (`extract` + `configure` + `make` + `stage`)** | Com `NLS` (`--enable-nls`) | `20.097,70 ms` | `19.740,05 ms` | `19.683,44 ms` | **`19.840,40 ± 183,84 ms`** |
| **Tempo Total (`extract` + `configure` + `make` + `stage`)** | Sem `NLS` (`--disable-nls`) | `19.533,38 ms` | `19.193,14 ms` | `19.137,62 ms` | **`19.288,05 ± 175,85 ms`** |

#### Espaço em disco e chamadas de sistema na compilação do `hello 2.12.3`
| Indicador | Com `NLS` (`--enable-nls`) | Sem `NLS` (`--disable-nls`) | Variação |
| :--- | :--- | :--- | :--- |
| **Tamanho final instalado no `STAGEDIR`** | `410.422 bytes` (**`400,80 KiB`**) | `198.462 bytes` (**`193,81 KiB`**) | **`-211.960 bytes` (`-51,6%`)** |
| **Total de arquivos no `STAGEDIR`** | **`50` arquivos** (`46` catálogos `.mo`) | **`4` arquivos** (`0` catálogos `.mo`) | **`-46` arquivos (`-92,0%`)** |
| **Tamanho do diretório de trabalho (`WRKDIR`)** | `7.810.504 bytes` (`7,45 MiB`, `723` arq.) | `7.808.958 bytes` (`7,45 MiB`, `723` arq.) | `~19x` o tamanho instalado |
| **Total de chamadas de sistema (`strace -fc`)** | **`2.467.256` syscalls** | **`2.382.742` syscalls** | **`-84.514` syscalls** |

---

### 2.3. Nix (`Nix 2.35.6` — `/nix/store/sd779x86bjaqxj2lzh2jsir4h0zjz6d1-hello-2.12.3`)
Arquivo de evidência: [`nix-metricas.json`](./evidencias/nix-metricas.json) e [`hello-unico-complemento.json`](./evidencias/hello-unico-complemento.json).

- **Tamanho próprio (NAR):** `279.592 bytes` (**`273,04 KiB`**)
- **Tamanho do fechamento completo (Closure):** `38.516.712 bytes` (**`36,73 MiB`**, `5` paths no store: `hello-2.12.3`, `glibc-2.44-57`, `libidn2-2.3.8`, `libunistring-1.4.2`, `xgcc-15.2.0-libgcc`)
- **Vinculação ELF (`bin/hello`):**
  - `NEEDED`: `libc.so.6`
  - `RUNPATH`: `/nix/store/r3hvhzl5fxhrgn0rfy5g7rda17702pj4-glibc-2.44-57/lib`

| Operação no Nix (pacote `hello` já presente no store) | Rep. 1 | Rep. 2 | Rep. 3 | Média ± Desvio | Syscalls (`strace -fc`) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`nix profile add /nix/store/...-hello-2.12.3`** | `40,25 ms` | `41,78 ms` | `41,81 ms` | **`41,28 ± 0,89 ms`** | **`3.617` syscalls** |
| **`nix profile rollback` (reversão atômica do perfil `hello`)** | `35,29 ms` | `34,33 ms` | `34,48 ms` | **`34,70 ± 0,52 ms`** | **`3.525` syscalls** (`1 symlink`, `1 rename`, `1 flock`) |
| **Execução direta `/nix/store/...-hello-2.12.3/bin/hello`** | `3,15 ms` | `3,40 ms` | `3,28 ms` | **`3,28 ± 0,10 ms`** | — |

---

### 2.4. Mecanismos de Flatpak (`OSTree` + `Bubblewrap`) e Snap (`SquashFS`) com `GNU hello`
Arquivo de evidência: [`flatpak-snap-metricas.json`](./evidencias/flatpak-snap-metricas.json) e [`hello-unico-complemento.json`](./evidencias/hello-unico-complemento.json).

#### A. Deduplicação por hardlinks no `OSTree 2026.2` (árvore do `hello`)
- **Commit v1:** `74eec73eedcea8afe6558f073bf25f96f01a08c79e34cace0ba63394317b8fe5`
- **Commit v2 (apenas `share/man/man1/hello.1.gz` alterado):** `bced831c46d3ceaa95a1831e585e2d3d26b54121be813aeac09bfd0171548384`
- **Verificação de inodes (`stat`):**
  - `co-1/bin/hello`: **`inode = 10495848`**, `nlink = 3`
  - `co-2/bin/hello`: **`inode = 10495848`**, `nlink = 3` (**mesmo inode físico compartilhado entre as duas versões**)
  - `co-1/share/man/man1/hello.1.gz`: `inode = 10495853` vs. `co-2/share/man/man1/hello.1.gz`: `inode = 10495856` (novo inode apenas para o arquivo modificado)

#### B. Confinamento com `Bubblewrap 0.13.1` executando `hello`
| Operação | Rep. 1 | Rep. 2 | Rep. 3 | Média ± Desvio | Syscalls (`strace -fc`) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Execução direta de `hello` (sem sandbox)** | `3,15 ms` | `3,40 ms` | `3,28 ms` | **`3,28 ± 0,10 ms`** | — |
| **Execução de `hello` dentro do sandbox `bwrap --unshare-all`** | `8,38 ms` | `7,54 ms` | `7,41 ms` | **`7,78 ± 0,43 ms`** | **`963` syscalls** (`1 unshare`, `17 mount`, `2 pivot_root`) |
| **Sobrecarga líquida de criação dos namespaces (`bwrap`)** | — | — | — | **`+4,50 ms`** | — |

#### C. Compressão `SquashFS 4.7.5` da árvore do `hello` (`246,67 KiB` descompactado)
| Compressor | Tamanho da Imagem | Razão | Compressão (Rep. 1 / 2 / 3) | Média Compressão | Extração (Rep. 1 / 2 / 3) | Média Extração |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`xz`** | **`64,00 KiB`** (`65.536 B`) | `0,259` | `49,46` / `50,61` / `50,33 ms` | **`50,13 ± 0,60 ms`** | `10,03` / `10,05` / `10,33 ms` | **`10,14 ± 0,17 ms`** |
| **`zstd`** | **`68,00 KiB`** (`69.632 B`) | `0,276` | `39,19` / `34,40` / `39,55 ms` | **`37,71 ± 2,88 ms`** | `9,99` / `10,18` / `10,41 ms` | **`10,19 ± 0,21 ms`** |
| **`gzip`** | **`72,00 KiB`** (`73.728 B`) | `0,292` | `36,03` / `35,40` / `39,18 ms` | **`36,87 ± 2,03 ms`** | `10,83` / `10,50` / `9,93 ms` | **`10,42 ± 0,46 ms`** |

---

## 3. Perfil Comparativo de Chamadas de Sistema (`strace -fc`) para o `GNU hello`

| Operação Rastreada (`GNU hello`) | Total de Syscalls | Chamadas Dominantes e Significado em Sistemas Operacionais |
| :--- | :--- | :--- |
| **`dpkg -i hello_2.10-5_amd64.deb`** | **`2.478`** | `openat`, `write`, `fsync`, `rename`, `fcntl`: mutação direta do FHS com sincronização em disco e trava de `/var/lib/dpkg`. |
| **Compilação `hello 2.12.3` (`--enable-nls`)** | **`2.467.256`** | `790.471 openat`, `307.984 read`, `273.631 close`, `4.261 execve`: centenas de subprocessos de inspeção (`configure`) e compilação (`gcc`/`msgfmt`). |
| **Compilação `hello 2.12.3` (`--disable-nls`)** | **`2.382.742`** | **`84.514` chamadas a menos** que a build com `NLS`, eliminando o processamento e instalação dos 46 catálogos `.mo`. |
| **`nix profile add` (`hello`)** | **`3.617`** | Leitura de metadados SQLite do store (`pread64`, `fcntl`) e criação da árvore de links simbólicos do perfil (`symlinkat`, `rename`). |
| **`nix profile rollback` (`hello`)** | **`3.525`** | **`1 symlink`**, **`1 rename`**, **`1 flock`**: troca atômica do ponteiro de geração do perfil sem tocar nos arquivos de `/nix/store`. |
| **`bwrap --unshare-all .../bin/hello`** | **`963`** | **`1 unshare`**, **`17 mount`**, **`8 mount_setattr`**, **`2 pivot_root`**, **`1 execve`**: construção da árvore VFS isolada antes de iniciar o binário `hello`. |
