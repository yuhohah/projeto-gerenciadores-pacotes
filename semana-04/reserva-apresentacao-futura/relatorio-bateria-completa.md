# Relatório parcial 2 — Comparações, demonstrações e medidas experimentais

**Etapa:** semana 4 — demonstrações consolidadas, metodologia experimental, medidas e análise comparativa.  
**Versão consolidada:** 18 de novembro de 2026.  
**Estado:** bateria experimental executada e registrada em [evidencias/](./evidencias/). Os testes cobrem Debian (`APT`/`dpkg` em container `debian:trixie-slim`), construção a partir do código-fonte baseada na receita oficial do FreeBSD Ports (`misc/hello` com e sem `NLS`), Nix (`store`, perfis, gerações, rollback e `RUNPATH`) e os mecanismos de distribuição e confinamento de Flatpak (`Flathub`, `OSTree`, `Bubblewrap`) e Snap (`SquashFS`, inspeção real de `gnome-text-editor_53.snap` e suporte de kernel).

## 1. Introdução e evolução desde o Relatório Parcial 1

No [Relatório Parcial 1](../semana-02/relatorio-parcial-01.md), o grupo consolidou a fundamentação teórica dos cinco representantes distribuídos em quatro famílias — **Debian (APT/dpkg)**, **FreeBSD Ports**, **Nix** e **Flatpak/Snap** — e definiu o plano de demonstrações e testes. Naquela etapa, apenas a validação inicial de perfis Nix pelo terminal e consultas documentais estavam disponíveis; faltavam a execução prática dos exemplos de Debian, a medição do custo de construção a partir de fontes com a opção `NLS`, a inspeção comparativa de vinculação dinâmica (`ELF`/`RUNPATH`), os testes práticos de deduplicação e permissões (`OSTree`/`Bubblewrap`) e a inspeção estrutural e de compressão das imagens `SquashFS` do Snap.

Esta segunda entrega cumpre dois papéis complementares do cronograma ([escopo e plano](../semana-01/escopo-e-plano.md)):

1. **Consolidar as demonstrações técnicas das quatro famílias** (previstas para a transição entre as semanas 3 e 4), com comandos reais, saídas verificadas, inspeção de binários ELF e rastreamento de chamadas de sistema (`strace`).
2. **Apresentar a metodologia experimental e as medidas comparativas** da Semana 4, separando rigorosamente as etapas de obtenção, compilação, instalação/extração, ativação de perfil e inicialização com ou sem isolamento.

## 2. Ambiente experimental e controle metodológico

Todos os experimentos locais foram executados em **18 de novembro de 2026** na mesma máquina física, garantindo mesmo processador, mesma memória e mesmo dispositivo de armazenamento para todas as medições ([ambiente-experimental.json](./evidencias/ambiente-experimental.json)):

- **Processador:** AMD Ryzen 5 2600 Six-Core Processor (`x86_64`, 6 núcleos físicos, 12 threads).
- **Memória e armazenamento:** 15 GiB de RAM principal; sistema de arquivos em SSD NVMe (`/dev/nvme0n1p6`).
- **Sistema hospedeiro:** NixOS `26.11.20261111.d4f25a3 (Zokor)`, kernel Linux `7.3.4`, revisão Nixpkgs `d4f25a3e562008648d45bcf2d70bcc7422cad84e`.
- **Ferramentas utilizadas nas medições:** `Nix 2.35.6`, `Docker 29.9.2`, `Flatpak 1.18.4`, `bubblewrap 0.13.1`, `libostree 2026.2`, `squashfs-tools 4.7.5` (`mksquashfs`/`unsquashfs`), `strace 7.2` e `GNU readelf 2.46`.
- **Mecanismos do kernel verificados no hospedeiro:**
  - Módulos de segurança ativos (`/sys/kernel/security/lsm`): `lockdown,capability,landlock,yama,bpf,ima`.
  - Controladores de grupos de controle (`/sys/fs/cgroup/cgroup.controllers`): `cpuset cpu io memory hugetlb pids rdma misc dmem` (hierarquia unificada `cgroup v2`).
  - Sessão gráfica: socket Wayland ativo em `/run/user/1000/wayland-1`.

### 2.1. Cuidados metodológicos e separação de variáveis

Para evitar comparações distorcidas entre operações de naturezas diferentes, o protocolo experimental ([protocolo-e-resultados.md](./protocolo-e-resultados.md)) adotou quatro regras:

1. **Isolamento da variação de rede:** os pacotes `.deb` do Debian, o arquivo de código-fonte `hello-2.12.3.tar.gz`, os caminhos do `/nix/store` e o pacote `gnome-text-editor_53.snap` foram baixados previamente para armazenamento local antes de cronometrar instalação, compilação, ativação de perfil ou descompressão.
2. **Repetições e estatística descritiva:** cada operação cronometrada foi executada **3 vezes** em diretórios ou containers limpos, registrando-se os valores individuais, a média, a mediana e o desvio-padrão ($\sigma$).
3. **Rastreamento de chamadas de sistema separado da medição de tempo:** como o `strace -c -f` intercepta a entrada e a saída de cada chamada ao kernel via `ptrace`, sua execução introduz sobrecarga. Por isso, o `strace` foi executado em passagem dedicada, separada das 3 repetições de tomada de tempo.
4. **Distinção explícita do alcance de cada ambiente:**
   - Os testes de **Debian** ocorreram em containers oficiais `debian:trixie-slim` (`Debian GNU/Linux 13.7`), que isolam a árvore de diretórios FHS e o banco de dados do `dpkg`, compartilhando o kernel Linux `7.3.4` do hospedeiro.
   - Na parte de **FreeBSD Ports**, a receita oficial de `misc/hello` (`Makefile`, `distinfo`, `pkg-descr`) foi consultada diretamente na árvore oficial do projeto FreeBSD. Como não há máquina virtual FreeBSD instalada neste hospedeiro, o custo das etapas de compilação (`extract`, `configure`, `build` e `stage/install` com `--enable-nls` e `--disable-nls`) foi medido no próprio hospedeiro sobre o **mesmo código-fonte oficial (`hello-2.12.3.tar.gz`, SHA-256 verificado)**. Os números medem o trabalho real do compilador, do linker e do gerador de catálogos `gettext` para o programa escolhido, sem afirmar que foram coletados sobre o kernel FreeBSD.

---

## 3. Resultados por família e relação com Sistemas Operacionais

### 3.1. Binários tradicionais mutáveis (FHS): Debian com APT e dpkg

No container oficial `debian:trixie-slim` (`APT 3.0.4`, `dpkg 1.22.22`), foram executados o piloto didático planejado com `tmux` (`3.5a-3`), o teste comparativo com `hello` (`2.10-5`) e a simulação de dependências da aplicação comum `gnome-text-editor` (`48.3-3`). Os registros completos estão em [debian-apt-dpkg.txt](./evidencias/debian-apt-dpkg.txt) e [debian-metricas.json](./evidencias/debian-metricas.json).

**Formato do pacote e banco de dados local.** A inspeção com `dpkg-deb -I` e `dpkg-deb -c` mostra que cada arquivo `.deb` é um arquivo `ar` contendo metadados de controle (`control`, `md5sums` e scripts de manutenção como `postinst`) e a árvore de dados que será extraída diretamente sobre a hierarquia global (`/usr/bin`, `/usr/share/doc`, `/usr/share/locale`). No pacote `tmux_3.5a-3_amd64.deb` (`490.296 bytes` comprimido, `Installed-Size: 1.209 KiB`), o arquivo de controle possui `1.464 bytes` e inclui um script `postinst` (`366 bytes`, `#!/bin/sh`). Após a instalação, o `dpkg` registra a lista de caminhos em `/var/lib/dpkg/info/tmux.list` e os hashes em `/var/lib/dpkg/info/tmux.md5sums`, protegendo a transação com travas de arquivo (`fcntl` sobre `/var/lib/dpkg/lock` e `lock-frontend`).

**Resolução de dependências conforme o estado inicial.** Na imagem enxuta `debian:trixie-slim`:
- `hello` (`2.10-5`) exige apenas `libc6` (já presente), resultando no download de **1 pacote `.deb` (`53.228 bytes` / `51,98 KiB`)** e `280 KiB` de espaço instalado.
- `tmux` (`3.5a-3`) exige `libc6`, `libsystemd0` e `libtinfo6` (já presentes) e mais **2 bibliotecas novas** (`libevent-core-2.1-7t64` com `132.868 B` e `libjemalloc2` com `274.324 B`), totalizando **3 pacotes `.deb` (`897.488 bytes` / `876,45 KiB`)** e `2.455 KiB` de espaço adicional.
- `gnome-text-editor` (`48.3-3`), embora tenha `Installed-Size: 2.722 KiB` para o pacote da aplicação em si, exige na mesma imagem base a instalação de **211 pacotes novos** (incluindo `libgtk-4-1`, `libadwaita-1-0`, `libgtksourceview-5-0`, `mesa-libgallium`, `libllvm19`, `systemd` e `dbus`).

**Medidas de instalação local e chamadas de sistema.** Com os arquivos `.deb` já em cache local (sem rede):
- Instalar `hello` levou em média **`37,33 ms`** (`[37, 38, 37] ms`, $\sigma = 0{,}58\text{ ms}$) e realizou **`2.478` chamadas de sistema** (`252` `openat`, `396` `read`, `60` `write`, `146` `rename`, `21` `fsync`, `44` `fcntl`, `11` `clone`, `21` `execve`).
- Instalar `tmux` e suas 2 dependências levou em média **`161,67 ms`** (`[161, 162, 162] ms`, $\sigma = 0{,}58\text{ ms}$) e realizou **`7.904` chamadas de sistema** (`642` `openat`, `984` `read`, `371` `write`, `77` `rename`, `81` `fsync`, `192` `fcntl`, `60` `clone`, `100` `execve`).
- O perfil de syscalls evidencia a mecânica de segurança do `dpkg` no sistema de arquivos virtual (VFS): os arquivos são extraídos com nomes temporários, sincronizados em disco (`fsync` / `sync_file_range`) e movidos atomicamente por arquivo via `rename()`, além de disparar processos filhos (`clone`/`execve`) para scripts `sh` de configuração.

### 3.2. Construção a partir de código-fonte: FreeBSD Ports (`misc/hello`) e efeito da opção `NLS`

A consulta direta à árvore oficial do FreeBSD Ports ([freebsd-ports-e-compilacao-hello.txt](./evidencias/freebsd-ports-e-compilacao-hello.txt) e [ports-compilacao-metricas.json](./evidencias/ports-compilacao-metricas.json)) confirmou os metadados atuais do port `misc/hello`:

- **Versão e origem:** `PORTNAME=hello`, `PORTVERSION=2.12.3`, `MASTER_SITES=GNU`.
- **Arquivo de código-fonte (`distinfo`):** `hello-2.12.3.tar.gz`, `SIZE = 1.189.208 bytes` (`1,13 MiB`), `SHA256 = 0d5f60154382fee10b114a1c34e785d8b1f492073ae2d3a6f7b147687b366aa0`.
- **Ferramentas e opções da receita (`Makefile`):** `USES=charsetfix gmake perl5`, `GNU_CONFIGURE=yes`, `OPTIONS_DEFINE=NLS`, `OPTIONS_SUB=yes`, `NLS_CONFIGURE_ENABLE=nls`, `NLS_USES=gettext localbase`.

Para medir de forma controlada o impacto que a compilação local e a opção `NLS` (Native Language Support) exercem sobre CPU, processos, chamadas de sistema e armazenamento, o mesmo tarball `hello-2.12.3.tar.gz` (com hash SHA-256 verificado) foi construído no ambiente de teste em duas configurações: com `--enable-nls` (padrão quando a opção `NLS` está ativa) e com `--disable-nls` (opção `NLS` desmarcada), em 3 repetições para cada variante.

| Métrica / Fase da construção (`hello-2.12.3`) | Com `NLS` (`--enable-nls`) | Sem `NLS` (`--disable-nls`) | Efeito observado da personalização |
| :--- | :---: | :---: | :--- |
| **Tamanho do `distfile` (`tar.gz`)** | 1.189.208 B (1.161,3 KiB) | 1.189.208 B (1.161,3 KiB) | Mesmo código-fonte de entrada |
| **Fase `configure` (média ± $\sigma$)** | 17.025,77 ± 169,55 ms | 16.998,43 ± 73,04 ms | Dominada por testes de cabeçalhos e compilador (`sh` + `gcc`) |
| **Fase `build` (`make -j4`, média ± $\sigma$)** | 2.025,83 ± 12,89 ms | 1.998,24 ± 21,69 ms | Compilação C e linkedição do binário `hello` |
| **Fase `stage/install` (média ± $\sigma$)** | **755,33 ± 14,31 ms** | **258,30 ± 3,47 ms** | Sem `NLS`, a fase de instalação é **2,92x mais rápida** |
| **Tempo total de construção (média ± $\sigma$)** | **19.840,40 ± 154,71 ms** | **19.288,05 ± 61,16 ms** | Economia de ~0,55 s ao omitir instalação de catálogos |
| **Área temporária `WRKDIR` (disco / arquivos)** | 10,17 MiB (810 arquivos) | 10,07 MiB (810 arquivos) | Área de trabalho exige **~25x a ~53x** o tamanho final instalado |
| **Resultado instalado `STAGE` (tamanho total)** | **400,80 KiB** (410.423 B) | **193,81 KiB** (198.460 B) | Desativar `NLS` reduz o espaço instalado em **51,6%** |
| **Arquivos finais instalados (`STAGE`)** | **50 arquivos** (46 `.mo`) | **4 arquivos** (0 `.mo`) | Sem `NLS`, restam apenas binário, manpages e info |
| **Total de chamadas de sistema (`strace -c -f`)** | **2.467.256 syscalls** | **2.382.742 syscalls** | Redução de **84.514 syscalls** (`openat`: 790k $\to$ 754k) |

**Interpretação para Sistemas Operacionais:** a etapa de configuração (`./configure`) responde por cerca de **86% do tempo total** e cria milhares de processos curtos (`4.261` `execve` e `4.918` `clone`/`clone3` com `NLS` ativo) para testar recursos do sistema operacional e da biblioteca C. Além disso, a área temporária de construção (`WRKDIR`, `~10,17 MiB`) ocupa mais de vinte vezes o espaço do software final instalado (`400,80 KiB`), explicando por que `make clean` é indispensável após construir um port.

### 3.3. Organização funcional e imutável: Nix (`store`, perfis, gerações e `RUNPATH`)

Os experimentos com Nix (`2.35.6`) avaliaram os três programas do estudo (`hello-2.12.3`, `tmux-3.8` e `gnome-text-editor-50.1`), registrando armazenamento, vinculação dinâmica, custo de manipulação de perfis e rollback ([nix-perfis-geracoes-vinculacao.txt](./evidencias/nix-perfis-geracoes-vinculacao.txt) e [nix-metricas.json](./evidencias/nix-metricas.json)).

**Tamanho próprio (NAR) vs. fechamento transitivo (`closure`).** A consulta com `nix path-info -s -S` demonstra quantitativamente a diferença entre o espaço exclusivo de um pacote e o grafo completo de suas dependências em `/nix/store`:

| Pacote no `/nix/store` | Caminho verificado | Tamanho próprio (NAR) | Fechamento transitivo (`closure`) | Proporção (Fechamento / NAR) |
| :--- | :--- | :---: | :---: | :---: |
| **GNU Hello `2.12.3`** | `/nix/store/sd779x86...-hello-2.12.3` | **273,04 KiB** (279.592 B) | **36,73 MiB** (38.515.520 B) | 137,7x (inclui `glibc-2.44-57`) |
| **tmux `3.8`** | `/nix/store/7v8w4qyz...-tmux-3.8` | **1.630,55 KiB** (1.669.680 B) | **58,12 MiB** (60.942.984 B) | 36,5x (inclui `ncurses`, `libevent`, `systemd-libs`) |
| **GNOME Text Editor `50.1`** | `/nix/store/94r4v2l4...-gnome-text-editor-50.1` | **2.794,88 KiB** (2.861.952 B) | **957,19 MiB** (1.003.687.616 B) | 350,7x (inclui pilha `GTK 4.22.4`, `libadwaita`, `mesa`) |

Como `glibc`, `glib`, `gtk4` e `libadwaita` ficam em caminhos únicos no `/nix/store` e são referenciados por múltiplos perfis e pacotes, o fechamento de `957,19 MiB` do editor **não representa crescimento exclusivo de disco a cada instalação**: na máquina de teste, obter o editor exigiu apenas `4` caminhos novos (`2,1 MiB` de download e `7,9 MiB` descompactados).

**Vinculação dinâmica isolada por `RUNPATH` e binários wrapper.** A inspeção dos cabeçalhos ELF com `readelf -d` e `ldd` mostra como o Nix evita conflitos de versão (*Dependency Hell*) sem usar containers nem alterar `/lib`:
- No Debian, `/usr/bin/tmux` não possui `RUNPATH` e carrega `/lib/x86_64-linux-gnu/libevent_core-2.1.so.7` e `libc.so.6`.
- No Nix, `/nix/store/7v8w4qyz...-tmux-3.8/bin/tmux` traz gravado em seu cabeçalho ELF o campo `RUNPATH` com os caminhos exatos de cada dependência:
  `/nix/store/5j2w6s0j...-systemd-minimal-libs-262/lib:/nix/store/vfnl45i7...-utf8proc-2.12.0/lib:/nix/store/adz753ps...-ncurses-6.6/lib:/nix/store/rlddw02a...-libevent-2.1.13/lib:/nix/store/p4kd0daj...-libutempter-1.2.3/lib:/nix/store/r3hvhzl5...-glibc-2.44-57/lib`.
- Para aplicações gráficas como o `gnome-text-editor-50.1`, a inspeção revelou a separação em dois executáveis: `bin/gnome-text-editor` é um binário *wrapper* leve (vinculado apenas à `glibc`) que configura variáveis de ambiente (`XDG_DATA_DIRS`, `GIO_EXTRA_MODULES`, `GDK_PIXBUF_MODULE_FILE`) e invoca o binário real `bin/.gnome-text-editor-wrapped`, cujo `RUNPATH` aponta para `gtk4-4.22.4`, `libadwaita-1.9.3`, `gtksourceview-5.20.0`, `libspelling-0.4.10` e demais bibliotecas do store.

**Desempenho de perfis e rollback atômico.** Com os pacotes presentes no `/nix/store`:
- Adicionar um pacote a um perfil novo (`nix profile add`) levou em média **`37,61 ms`** para `hello`, **`37,53 ms`** para `tmux` e **`37,66 ms`** para `gnome-text-editor`. O tempo é constante (~37,6 ms) mesmo quando o pacote tem fechamento de `957,19 MiB`, pois o Nix não copia nem extrai arquivos do pacote: apenas grava o manifesto da nova geração e cria links simbólicos (`3.617` syscalls totais, sendo `4` `symlink`, `2` `rename` e `0` `fsync`).
- O retorno à geração anterior (`nix profile rollback`) levou em média **`31,80 ms`** (`[31,73; 32,16; 31,51] ms`, $\sigma = 0{,}33\text{ ms}$), executando `3.525` syscalls e apenas **`1` chamada `symlink` e `1` `rename`** para trocar atomicamente a referência da geração ativa do perfil.
- Foram criados dois perfis simultâneos com composições distintas (`demo-perfil-a` com `gnome-text-editor 50.1 + hello 2.12.3` e `demo-perfil-b` com `gnome-text-editor 50.1 + tmux 3.8`), comprovando coexistência de ambientes independentes compartilhando o mesmo binário do editor no store.

### 3.4. Aplicações em sandbox e imagens imutáveis: Flatpak e Snap

Os experimentos da quarta família combinaram consultas reais aos repositórios oficiais, testes práticos de deduplicação no `OSTree` e de confinamento no `Bubblewrap`, e a inspeção direta do pacote oficial `gnome-text-editor_53.snap` ([flatpak-snap-isolamento-e-imagens.txt](./evidencias/flatpak-snap-isolamento-e-imagens.txt) e [flatpak-snap-metricas.json](./evidencias/flatpak-snap-metricas.json)).

**Custo de armazenamento: aplicação vs. runtime/base compartilhados.** A consulta ao Flathub (`flatpak remote-info`) e à Snap Store + inspeção do `.snap` evidencia a arquitetura em camadas dos dois formatos para o `GNOME Text Editor`:

| Componente / Métrica | Flatpak (`org.gnome.TextEditor`) | Snap (`gnome-text-editor`, rev 53) | Comparação arquitetural |
| :--- | :---: | :---: | :--- |
| **Versão disponibilizada (`amd64`/`x86_64`)** | 51.0 (commit `8effd345...`, 08/11/2026) | 48.3 (revisão 53, `latest/stable`) | Catálogos distribuem versões distintas |
| **Tamanho de download da aplicação** | **1,4 MB** | **1,07 MiB** (1.118.208 B) | Pacote da aplicação contém apenas o editor |
| **Tamanho descompactado / instalado (app)** | **2,5 MB** (árvore OSTree) | **2,98 MiB** (3.124.861 B; 338 arquivos) | No Snap, a imagem permanece comprimida em disco |
| **Base / Runtime obrigatório (download)** | `org.gnome.Platform/x86_64/51`: **432,8 MB** | `core24` (**66,84 MiB**) + `gnome-46-2404` (**616,03 MiB**) | Alto custo inicial no 1º aplicativo; compartilhado depois |
| **Política de arquivos declarada no pacote** | `filesystems=xdg-run/gvfsd;host;xdg-run/gvfs;` | `confinement: strict`; plug `home`; `GTK_USE_PORTAL=1` | Receita Flatpak abre `host`; Snap usa interface `home` |

**Verificação prática de deduplicação no OSTree (`libostree 2026.2`).** Para demonstrar na prática como o Flatpak evita duplicar arquivos idênticos entre commits ou runtimes, criamos um repositório OSTree local (`ostree init --mode=bare-user`) e registramos dois commits consecutivos (`v1`: `41b16d91...` e `v2`: `148886dd...`) contendo uma biblioteca simulada de `256 KiB` (`libcompartilhada.bin`, inalterada) e um arquivo de metadados (`versao.txt`, alterado entre `v1` e `v2`). Ao realizar o checkout das duas versões (`ostree checkout -U`) e inspecionar os metadados do sistema de arquivos com `stat`:
- `checkout-v1/libcompartilhada.bin` e `checkout-v2/libcompartilhada.bin` apresentaram **exatamente o mesmo número de inode (`10495777`)** e contagem de links físicos `st_nlink = 3` (repositório + checkout v1 + checkout v2), consumindo espaço físico de uma única cópia.
- `checkout-v1/versao.txt` e `checkout-v2/versao.txt` receberam **inodes distintos (`10495779` e `10495782`)**.

**Verificação prática de confinamento e permissões no Bubblewrap (`bwrap 0.13.1`).** Como o manifesto padrão do `org.gnome.TextEditor` no Flathub declara `filesystems=host`, executamos os três cenários de controle de acesso sobre a pasta do documento `comparacao.txt` usando diretamente o motor de isolamento do Flatpak (`bwrap --unshare-all`):
1. **Pasta ausente do namespace de montagem:** o comando `cat comparacao.txt` falhou imediatamente com `No such file or directory` (`código de saída 1`, `7,77 ms`), pois o caminho não existe na árvore raiz montada via `pivot_root`.
2. **Pasta exposta como somente leitura (`--ro-bind`):** a leitura de `comparacao.txt` teve sucesso (`código 0`, `7,71 ms`), mas a tentativa de gravar `resultado-ro.txt` foi bloqueada pelo kernel com `Read-only file system` (`código 1`, `9,34 ms`).
3. **Pasta exposta com leitura e escrita (`--bind`):** a transformação de `comparacao.txt` (`Resultado: aguardando` $\to$ `Resultado: concluído`) em `resultado-bwrap.txt` e sua releitura tiveram sucesso (`código 0`, `14,58 ms`).
- **Custo de inicialização do sandbox (`bwrap`):** executar o binário `hello` dentro de um novo conjunto de namespaces (`--unshare-all` com `--ro-bind` de `/nix` e `/run`, `/proc`, `/dev` e `/tmp`) levou em média **`7,78 ms`** ($\sigma = 0{,}05\text{ ms}$), contra **`3,28 ms`** na execução direta — uma sobrecarga de **`~4,50 ms`** correspondente a **`963` syscalls**, incluindo `1` `unshare`, `2` `clone`, `17` `mount`, `8` `mount_setattr`, `2` `pivot_root`, `2` `umount2` e `3` `capset`.

**Inspeção real do pacote Snap (`gnome-text-editor_53.snap`) e comparação de compressão SquashFS.** O arquivo oficial `gnome-text-editor_53.snap` (`1.118.208 bytes`, hash `SHA3-384` verificado com o catálogo da Snap Store) foi inspecionado com `unsquashfs -s`, extraído e analisado:
- O cabeçalho confirma uma imagem **SquashFS 4.0** comprimida com **`xz`**, blocos de `131.072 bytes` (`128 KiB`) e `540` inodes.
- O arquivo interno `meta/snap.yaml` (ausente na etapa puramente documental da Semana 2) comprova que a revisão 53 usa `base: core24`, `confinement: strict`, plugs `desktop`, `wayland`, `x11`, `home`, `gsettings`, `opengl` e `cups`, variável `GTK_USE_PORTAL: '1'` e cinco interfaces `content` (`gnome-46-2404`, `gpu-2404` fornecida por `mesa-2404`, `gtk-3-themes`, `icon-themes` e `sound-themes`).
- O binário ELF interno `usr/bin/gnome-text-editor` não utiliza `RUNPATH` fixo no estilo Nix; em vez disso, o `meta/snap.yaml` configura `LD_LIBRARY_PATH` apontando para `$SNAP/usr/lib/x86_64-linux-gnu` e para os diretórios montados pelos snaps de conteúdo (`$SNAP/gnome-platform`, `$SNAP/gpu-2404`).
- Para avaliar o impacto do algoritmo de compressão em imagens SquashFS, reempacotamos a árvore real extraída do `gnome-text-editor_53.snap` (`3.124.861 bytes` descompactados) com `mksquashfs` e medimos a extração com `unsquashfs` em 3 repetições para `xz`, `zstd` e `gzip`:

| Algoritmo SquashFS | Tamanho da imagem gerada | Razão (Comprimido / Original) | Tempo de compressão (média ± $\sigma$) | Tempo de extração (média ± $\sigma$) | Trade-off observado |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`xz`** (usado no `.snap` oficial) | **832,0 KiB** (851.968 B) | **0,273** (menor arquivo) | 145,60 ± 0,43 ms | 29,06 ± 3,49 ms | Maior economia de rede/disco; leitura mais custosa em CPU |
| **`zstd`** | **908,0 KiB** (929.792 B) | **0,298** (+9,1% vs. `xz`) | **104,73 ± 2,46 ms** | **16,60 ± 0,37 ms** | Extração **42,9% mais rápida** que `xz` com baixa perda de taxa |
| **`gzip`** | **1.036,0 KiB** (1.060.864 B) | **0,339** (+24,5% vs. `xz`) | **76,92 ± 3,13 ms** | 17,18 ± 0,28 ms | Compressão rápida, mas pacote ~25% maior que `xz` |

---

## 4. Síntese comparativa transversal (Sistemas Operacionais)

A tabela a seguir reúne os resultados verificados experimentalmente para o programa comum `hello` (comparando instalação binária FHS, compilação a partir do código-fonte com/sem `NLS`, perfil Nix e execução isolada com `Bubblewrap`) e para a aplicação gráfica `GNOME Text Editor`:

| Operação avaliada no mesmo hardware (`Ryzen 5 2600`, Linux `7.3.4`) | Tempo médio (± $\sigma$) | Total de syscalls (`strace -c -f`) | Syscalls críticas de SO observadas | Espaço em disco associado |
| :--- | :---: | :---: | :--- | :--- |
| **Debian (`dpkg -i hello_2.10-5_amd64.deb`, cache local)** | **37,33 ± 0,58 ms** | **2.478** | `252 openat`, `146 rename`, `21 fsync`, `44 fcntl` | `51,98 KiB` (`.deb`) $\to$ `280 KiB` instalado em `/usr` |
| **Debian (`dpkg -i tmux` + 2 deps `.deb`, cache local)** | **161,67 ± 0,58 ms** | **7.904** | `642 openat`, `77 rename`, `81 fsync`, `192 fcntl`, `100 execve` | `876,45 KiB` (`3 .deb`) $\to$ `2.455 KiB` instalado |
| **Compilação do fonte (`hello-2.12.3`, `--enable-nls`)** | **19.840,40 ± 154,71 ms** | **2.467.256** | `790.471 openat`, `4.261 execve`, `4.918 clone/clone3` | `10,17 MiB` temporários (`WRKDIR`) $\to$ `400,80 KiB` final (`50` arqs) |
| **Compilação do fonte (`hello-2.12.3`, `--disable-nls`)** | **19.288,05 ± 61,16 ms** | **2.382.742** | `753.795 openat`, `4.065 execve`, `4.544 clone/clone3` | `10,07 MiB` temporários (`WRKDIR`) $\to$ `193,81 KiB` final (`4` arqs) |
| **Nix (`nix profile add` com pacote já no `/nix/store`)** | **37,61 ± 0,77 ms** | **3.617** | `2.263 openat`, `4 symlink`, `2 rename`, `0 fsync` | `273,04 KiB` NAR próprio (`36,73 MiB` fechamento com `glibc`) |
| **Nix (`nix profile rollback` entre gerações)** | **31,80 ± 0,33 ms** | **3.525** | `1 symlink`, `1 rename`, `1 flock`, `0 fsync` | Troca atômica de ponteiro; componentes permanecem no store |
| **Execução direta de `hello` (Nix) vs. isolada em `bwrap`** | **3,28 ms** vs. **7,78 ms** | **~110** vs. **963** | No `bwrap`: `1 unshare`, `17 mount`, `2 pivot_root`, `3 capset` | Sem cópia adicional de arquivos (usa bind mounts somente-leitura) |

### Principais conclusões técnicas da etapa

1. **Extração mutável (FHS) vs. ativação por links simbólicos (Nix):** O `dpkg` modifica a árvore global `/usr` arquivo por arquivo, exigindo dezenas de chamadas `fsync` (`21` no `hello`, `81` no `tmux`) e `rename` (`146` no `hello`) para preservar consistência em caso de falha. Já o `nix profile add` sobre pacotes presentes no store leva o mesmo tempo (~`37,6 ms`) para um utilitário de `273 KiB` (`hello`) ou para um editor gráfico cujo fechamento soma `957,19 MiB` (`gnome-text-editor`), pois atua apenas sobre a árvore de links simbólicos do perfil.
2. **Custo quantitativo da construção a partir de fontes vs. ganho de personalização:** Construir `hello-2.12.3` a partir do fonte exigiu **~531 vezes mais tempo** (`19,84 s` vs. `37,33 ms`) e **~995 vezes mais chamadas de sistema** (`2,47 milhões` vs. `2.478`) do que instalar o pacote binário `.deb`, além de `10,17 MiB` de área temporária (`WRKDIR`). Em contrapartida, desativar a opção `NLS` (`--disable-nls`, equivalente à opção `NLS` do port `misc/hello` no FreeBSD) reduziu os arquivos instalados de `50` para `4` e o tamanho final de `400,80 KiB` para `193,81 KiB` (**-51,6%**).
3. **Resolução de bibliotecas dinâmicas (`ELF`):** Foram comprovadas três abordagens distintas no nível do vinculador dinâmico (`ld.so`):
   - **Debian:** busca no caminho padrão FHS (`/lib/x86_64-linux-gnu`), sem `RUNPATH` no binário — simples e econômico em disco, mas impede coexistência direta de versões incompatíveis da mesma biblioteca `.so` de mesmo SONAME.
   - **Nix:** grava `RUNPATH` com hashes criptográficos de `/nix/store/.../lib` diretamente em cada executável ELF (e usa binários *wrapper* para variáveis de sessão gráfica), permitindo que múltiplos perfis e versões coexistam sem conflito e sem exigir containers.
   - **Snap:** mantém o binário ELF sem `RUNPATH` de store, mas altera a visão do processo combinando montagem de imagem `SquashFS`, `layout` bind mounts e `LD_LIBRARY_PATH` apontando para snaps de conteúdo (`gnome-46-2404`, `mesa-2404`).
4. **Proteção e confinamento dependem da política do pacote e do suporte do kernel:**
   - No **Flatpak**, o teste com `Bubblewrap` provou que o isolamento por namespaces bloqueia caminhos omitidos (`No such file or directory`) e impede escrita em montagens `--ro-bind` (`Read-only file system`) com sobrecarga de inicialização de apenas `~4,50 ms` (`963` syscalls). Contudo, como o manifesto oficial do `org.gnome.TextEditor` no Flathub declara `filesystems=host`, a proteção padrão da pasta pessoal fica desativada se o usuário não aplicar restrição (`--nofilesystem=host:reset`).
   - No **Snap**, a inspeção do `gnome-text-editor_53.snap` confirmou `confinement: strict`, `GTK_USE_PORTAL: '1'` e uso da interface `home`. Entretanto, a checagem de `/sys/kernel/security/lsm` no hospedeiro (`lockdown,capability,landlock,yama,bpf,ima`, sem `apparmor`) demonstra concretamente por que o confinamento estrito do Snap depende do suporte de segurança do kernel hospedeiro.

## 5. Limites registrados e preparação para a Semana 5

Em conformidade com o rigor metodológico do projeto, ficam registrados os limites desta bateria experimental:

1. **Ambiente Debian em container:** as medidas de `APT`/`dpkg` foram coletadas em containers `debian:trixie-slim` sobre o kernel Linux `7.3.4` do hospedeiro, o que reproduz fielmente o comportamento de espaço de usuário, banco de dados `dpkg` e chamadas VFS, mas não avalia inicialização de serviços de boot nem kernel Debian separado.
2. **Construção de fontes em Linux vs. VM FreeBSD:** a receita `misc/hello` foi verificada na árvore oficial do FreeBSD Ports e o código-fonte idêntico (`hello-2.12.3.tar.gz`) foi compilado com e sem `NLS` no hospedeiro Linux; os tempos e contagens de syscalls medem o trabalho real da cadeia GNU (`configure`/`make`/`install`), e não uma execução sobre o kernel FreeBSD.
3. **Execução do daemon `snapd`:** o pacote oficial `gnome-text-editor_53.snap` foi baixado, verificado por hash `SHA3-384`, extraído e analisado (superblock `SquashFS`, `meta/snap.yaml`, binário ELF e recompressão `xz`/`zstd`/`gzip`), sem execução do serviço `snapd` no hospedeiro NixOS.

Na **Semana 5 (entrega final)**, o grupo unificará a fundamentação teórica (Semanas 1 e 2) com a mecânica de baixo nível e os resultados quantitativos consolidados nesta entrega (Semanas 3 e 4), apresentando a matriz final de decisão por perfil de uso e as conclusões do projeto.

## Referências e arquivos da entrega

- **Protocolo experimental e tabelas completas:** [protocolo-e-resultados.md](./protocolo-e-resultados.md).
- **Evidências brutas e script reprodutível:** [evidencias/executar_experimentos.py](./evidencias/executar_experimentos.py) e [evidencias/resumo-comparativo.json](./evidencias/resumo-comparativo.json).
- **Apresentação de slides e roteiro da Semana 4:** [slides/README.md](./slides/README.md) e [slides/roteiro-de-fala.md](./slides/roteiro-de-fala.md).
- **Fontes técnicas oficiais:** Debian Project ([Debian FAQ cap. 8](https://www.debian.org/doc/manuals/debian-faq/pkgtools.en.html), [dpkg(1)](https://manpages.debian.org/trixie/dpkg/dpkg.1.en.html), [deb(5)](https://manpages.debian.org/trixie/dpkg-dev/deb.5.en.html)); FreeBSD Project ([Handbook: Ports](https://docs.freebsd.org/en/books/handbook/ports/), [Porter's Handbook](https://docs.freebsd.org/en/books/porters-handbook/slow-porting/), [misc/hello Makefile](https://cgit.freebsd.org/ports/tree/misc/hello/Makefile)); Nix ([Nix Manual — Profiles](https://nix.dev/manual/nix/2.34/package-management/profiles.html), [Store Paths](https://nix.dev/manual/nix/2.34/store/store-path.html)); Flatpak ([Under the Hood](https://docs.flatpak.org/en/latest/under-the-hood.html), [Sandbox Permissions](https://docs.flatpak.org/en/latest/sandbox-permissions.html), [Bubblewrap](https://github.com/containers/bubblewrap)); Canonical ([Snap System Architecture](https://snapcraft.io/docs/reference/system-architecture/), [Snap Confinement](https://snapcraft.io/docs/explanation/security/snap-confinement/), [The Snap Format](https://snapcraft.io/docs/reference/development/yaml-schemas/the-snap-format/)).
