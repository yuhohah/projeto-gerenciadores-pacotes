# Relatório Parcial 2 — Metodologia Experimental, Validade no NixOS e Comparação Controlada com `GNU hello`

**Projeto:** Gerenciadores de pacotes em sistemas Unix/Linux (Debian `APT/dpkg`, FreeBSD `Ports`, `Nix`, `Flatpak` e `Snap`)  
**Etapa:** Semana 4 — Relatório Parcial 2 (metodologia experimental, análise de validade e resultados comparativos sobre exemplo único controlado)  
**Data:** 18 de novembro de 2026  

---

## 1. Objetivo e Escolha do Exemplo Único Controlado (`GNU hello`)

Na Semana 2, consolidamos a fundamentação conceitual das quatro famílias de gerenciadores de pacotes sob a ótica de **Sistemas Operacionais** — organização do sistema de arquivos (VFS), resolução e vinculação dinâmica de dependências (ELF/`ld.so`), atomicidade de atualização e recuperação, e mecanismos de proteção e isolamento.

Para este checkpoint da **Semana 4**, adotamos uma decisão metodológica rigorosa:
1. **Isolar um único programa de referência — o `GNU hello` — através de todas as quatro famílias**, eliminando diferenças espúrias causadas por árvores de dependências heterogêneas;
2. **Aprofundar a explicação de como os experimentos são executados dentro de um único hospedeiro `NixOS` (`Linux 7.3.4`)**, detalhando quais mecanismos do kernel são exercitados nativamente, onde entra o isolamento por container (apenas no Debian FHS), onde há separação entre receita oficial do FreeBSD Ports e compilação controlada do código-fonte, e **qual é a validade científica e o limite de cada medição**.

*(Observação: a bateria complementar com pacotes maiores de terminal e interface gráfica já foi coletada e encontra-se preservada em [`./reserva-apresentacao-futura/`](./reserva-apresentacao-futura/README.md) e [`./evidencias/`](./evidencias/) para a consolidação da apresentação final).*

### Por que o `GNU hello` é o melhor exemplo único para isolar mecanismos de SO?
Quando instalamos programas complexos, o tempo e o espaço medidos misturam o custo do **gerenciador de pacotes** com o custo de dezenas de bibliotecas auxiliares. O `GNU hello` possui apenas **uma dependência dinâmica (`libc.so.6`)** e **46 catálogos de tradução (`NLS`, arquivos `.mo`)**. Isso permite medir, sem ruído externo:
- o custo puro da transação do `dpkg` sobre o FHS (`/usr/bin/hello`, `/var/lib/dpkg`, `fsync` e `rename`);
- o efeito exato de uma opção de compilação do FreeBSD Ports (`OPTIONS_DEFINE=NLS`: `--enable-nls` vs. `--disable-nls`) sobre o tempo de construção e sobre a árvore de arquivos gerada;
- a diferença entre o cabeçalho ELF tradicional (sem `RUNPATH`, resolvendo em `/lib/x86_64-linux-gnu`) e o cabeçalho ELF do `Nix` (`RUNPATH` apontando para `/nix/store/<hash>-glibc-.../lib`), além do custo de ativação e rollback de geração por troca de symlinks;
- o funcionamento real da deduplicação por hardlinks (`OSTree`), do confinamento por namespaces (`Bubblewrap`) e da compressão de imagem somente-leitura (`SquashFS` com `xz`, `zstd` e `gzip`) aplicados à própria árvore de arquivos do `GNU hello`.

---

## 2. Como é Possível Testar as Quatro Famílias no Mesmo Hospedeiro NixOS?

Todos os experimentos foram executados na mesma máquina física para garantir igualdade de CPU, memória RAM, armazenamento NVMe e versão do kernel:

| Componente | Especificação Verificada ([`ambiente-experimental.json`](./evidencias/ambiente-experimental.json)) |
| :--- | :--- |
| **CPU** | AMD Ryzen 5 2600 Six-Core Processor (6 núcleos físicos / 12 threads, x86_64) |
| **Memória RAM e Disco** | 15 GiB DDR4 · SSD NVMe (ext4, 513 GiB livres) |
| **Sistema Hospedeiro** | NixOS 26.11 (`26.11.20261111.d4f25a3`, Xantusia) |
| **Kernel e Segurança** | Linux `7.3.4` · `cgroup v2` · LSMs ativos: `lockdown,capability,landlock,yama,bpf,ima` |
| **Ferramentas Nativas** | `nix 2.35.6`, `flatpak 1.18.4`, `ostree 2026.2`, `bwrap 0.13.1`, `squashfs-tools 4.7.5`, `strace 7.2`, `readelf 2.46`, `docker 29.9.2` |

Uma dúvida fundamental de Sistemas Operacionais é: **todos os testes foram feitos em container? Como o NixOS consegue executar testes de Debian, FreeBSD Ports, Nix e Flatpak/Snap?**

A resposta é **não**: apenas o Debian rodou em container. Os demais experimentos rodaram como **processos nativos diretamente no NixOS**. A tabela abaixo explica o mecanismo exato de cada um:

| Família | Modo de Execução no NixOS | Por que esse modo é necessário e como funciona no kernel? |
| :--- | :--- | :--- |
| **1. Nix** | **100% Nativo no host** | O sistema hospedeiro já é NixOS. Os comandos `nix profile add`, `nix profile rollback` e `nix path-info` operam diretamente sobre o `/nix/store` real da máquina e criam links simbólicos em perfis isolados (`--profile /tmp/...`). |
| **2. Flatpak (`OSTree` + `Bubblewrap`) e `SquashFS` (Snap)** | **100% Nativo no host** | Os binários `ostree`, `bwrap`, `mksquashfs` e `unsquashfs` estão instalados nativamente no NixOS. Eles invocam diretamente as chamadas de sistema do kernel Linux `7.3.4` (`linkat` para hardlinks do OSTree; `unshare`, `mount` e `pivot_root` para namespaces do Bubblewrap). |
| **3. Debian (`APT 3.0.4` + `dpkg 1.22.22`)** | **Container Linux (`debian:trixie-slim`)** | O NixOS não possui `/usr/bin`, `/lib/x86_64-linux-gnu` nem `/var/lib/dpkg` na raiz do sistema, pois abole o FHS global. O container Docker cria um **namespace de montagem (`mnt namespace`)** com o sistema de arquivos FHS oficial do Debian 13 (`Trixie`), permitindo que os binários reais `apt` e `dpkg` executem diretamente sobre o **mesmo kernel Linux `7.3.4`** sem emulação de CPU nem hipervisor. |
| **4. FreeBSD Ports (`misc/hello` + build `NLS`)** | **Inspeção da receita oficial + compilação nativa no host** | Um container Docker **não pode rodar FreeBSD**, pois containers compartilham o kernel do host (Linux) e o FreeBSD possui outro kernel (kernel FreeBSD). Por isso, dividimos o teste em duas partes transparentes: (a) inspeção direta da receita oficial `misc/hello` da árvore FreeBSD Ports (`Makefile`, `distinfo`) e (b) compilação nativa do mesmo tarball oficial (`hello-2.12.3.tar.gz`, SHA-256 idêntico) com as flags `--enable-nls` e `--disable-nls`. |

---

## 3. Análise Crítica da Validade Experimental (Validade Interna vs. Limites)

Para defender os resultados com rigor acadêmico, distinguimos quatro níveis de validade nas medições realizadas:

### 3.1. O que tem validade 100% exata (invariante ao ambiente)
- **Estrutura de pacotes, árvores de arquivos e cabeçalhos ELF (`readelf -d`, `dpkg-deb -I/-c`, `Makefile`/`distinfo`):**
  Os pacotes `.deb` do Debian 13, o derivation `/nix/store/sd779x86bjaqxj2lzh2jsir4h0zjz6d1-hello-2.12.3` e o tarball oficial `hello-2.12.3.tar.gz` são **exatamente os artefatos oficiais de produção**. O fato de o binário `/usr/bin/hello` do Debian possuir apenas `NEEDED: libc.so.6` (sem `RUNPATH`) e de o binário do Nix possuir `RUNPATH: /nix/store/r3hvhzl5fxhrgn0rfy5g7rda17702pj4-glibc-2.44-57/lib` gravado no cabeçalho ELF é uma propriedade estática do arquivo binário — o resultado é idêntico em qualquer máquina.

### 3.2. O que tem validade 100% nativa (processos diretos no host)
- **Operações do Nix (`nix profile add` e `nix profile rollback`), deduplicação `OSTree`, isolamento `Bubblewrap` e compressão `SquashFS`:**
  Como essas ferramentas rodam nativamente no NixOS sobre o sistema de arquivos `ext4` (NVMe) e o kernel Linux `7.3.4`, não há qualquer camada intermediária. O compartilhamento do mesmo inode (`10495848`) do binário `bin/hello` entre dois commits `OSTree` e a sobrecarga de `+4,50 ms` (`963` syscalls) do `Bubblewrap` refletem o comportamento real do kernel Linux em hardware físico.

### 3.3. Validade e limite do container Debian (`OverlayFS` vs. `ext4` puro)
- **Por que o teste é altamente válido para comparar algoritmos de SO:**
  Em Linux, um container não é uma máquina virtual: quando o `dpkg -i` executa dentro do container `debian:trixie-slim`, cada chamada `openat`, `write`, `fsync`, `rename` e `fcntl` é atendida diretamente pelo mesmo kernel Linux `7.3.4` e pelo mesmo SSD NVMe. Assim, o perfil de **`2.478` chamadas de sistema** medidas com `strace -fc` na instalação do `hello_2.10-5_amd64.deb` retrata fielmente o algoritmo transacional do `dpkg`.
- **Qual é a ressalva metodológica:**
  O sistema de arquivos raiz (`/`) de um container Docker utiliza **OverlayFS** sobre o `ext4` do host. Operações intensivas em metadados (como criar arquivos temporários `.dpkg-new` e renomeá-los) sofrem uma pequena sobrecarga do driver `overlay` em comparação a uma partição `ext4` montada diretamente. Ainda assim, a instalação local do `hello` levou apenas **`37,33 ± 0,47 ms`**, demonstrando que a sobrecarga do OverlayFS para um pacote pequeno é mínima.

### 3.4. Validade e limite do experimento de compilação (`FreeBSD Ports misc/hello`)
- **O que é idêntico ao FreeBSD Ports:**
  A receita oficial `misc/hello/Makefile` do FreeBSD Ports define `PORTVERSION=2.12.3`, `USES=cpe charsetfix gmake` e `OPTIONS_DEFINE=NLS`, passando `--disable-nls` ao `configure` quando a opção `NLS` é desmarcada. Nosso experimento compila exatamente o mesmo código-fonte oficial (`hello-2.12.3.tar.gz`, SHA-256 `bfd006eb...` verificado contra o `distinfo` do FreeBSD) com `./configure --enable-nls` vs. `./configure --disable-nls`. Por isso, **a redução de `50` para `4` arquivos instalados** (eliminação dos 46 catálogos `.mo`) e **a economia de `51,6%` no espaço instalado (`400,80 KiB` $\rightarrow$ `193,81 KiB`)** reproduzem com exatidão o efeito estrutural do port `misc/hello`.
- **Qual é a ressalva metodológica:**
  Como a compilação (`19.840,40 ms` com `NLS` e `19.288,05 ms` sem `NLS`, com `2.467.256` syscalls) rodou sobre kernel Linux com `GCC/glibc`, os tempos absolutos e nomes de syscalls específicas de kernel (`futex`, `openat`) pertencem ao ambiente Linux de referência, e não a uma execução do `bmake` sobre kernel FreeBSD (`Clang/libc`). Declarar essa distinção evita qualquer extrapolação indevida.

### 3.5. O achado experimental sobre o suporte do kernel para o Snap (`AppArmor`)
- Ao inspecionar `/sys/kernel/security/lsm` no host NixOS, verificamos os módulos `lockdown,capability,landlock,yama,bpf,ima` — **sem `apparmor`**.
- Longe de invalidar o estudo, esse fato **comprova experimentalmente uma diferença arquitetural central entre Flatpak e Snap**: enquanto o `Bubblewrap` (usado pelo Flatpak) funciona em qualquer kernel Linux com *user namespaces* padrão, o confinamento estrito do `Snap` exige que o sistema hospedeiro forneça o LSM `AppArmor` ativo e o daemon `snapd` integrado ao `systemd`. Para avaliar o mecanismo de armazenamento do Snap sem `snapd`, aplicamos `mksquashfs` e `unsquashfs` diretamente sobre a árvore do `GNU hello`, medindo o custo real dos compressores `xz`, `zstd` e `gzip` usados por pacotes `.snap`.

---

## 4. Resultados Experimentais com o Exemplo Único (`GNU hello`)

Todas as medições cronometradas foram executadas com **3 repetições independentes**, separando o download da operação local em disco. Os logs completos estão em [`./evidencias/`](./evidencias/).

### 4.1. Debian (`APT 3.0.4` / `dpkg 1.22.22`) — Mutação In-Place no FHS
Evidências: [`debian-apt-dpkg.txt`](./evidencias/debian-apt-dpkg.txt), [`debian-metricas.json`](./evidencias/debian-metricas.json) e [`hello-unico-complemento.json`](./evidencias/hello-unico-complemento.json).

- **Pacote analisado:** `hello_2.10-5_amd64.deb` (`51,38 KiB` de download `.deb`; `188 KiB` de `Installed-Size`).
- **Organização de arquivos no FHS:** O comando `dpkg -L hello` mostra que os arquivos são espalhados diretamente na hierarquia global: o executável vai para `/usr/bin/hello`, os manuais para `/usr/share/man/man1/hello.1.gz` e `/usr/share/info/hello.info.gz`, a documentação para `/usr/share/doc/hello/` e os catálogos de tradução para `/usr/share/locale/<idioma>/LC_MESSAGES/hello.mo`.
- **Vinculação dinâmica ELF (`readelf -d` e `ldd`):**
  ```text
  0x0000000000000001 (NEEDED)  Shared library: [libc.so.6]
  libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
  ```
  O binário **não possui `RPATH` nem `RUNPATH`**. Ele depende inteiramente do diretório global `/lib/x86_64-linux-gnu` do sistema operacional.
- **Desempenho e chamadas de sistema (`dpkg -i` local, 3 repetições):**
  - Tempo de instalação local: **`37,33 ± 0,47 ms`** (repetições: `37,00 ms`, `38,00 ms`, `37,00 ms`).
  - Tempo de execução do binário (`/usr/bin/hello --version`): **`2,00 ± 0,00 ms`**.
  - Perfil `strace -fc`: **`2.478` chamadas de sistema** (`104` erros esperados de busca em cache). Para garantir consistência ao escrever diretamente no FHS e atualizar `/var/lib/dpkg/status`, o `dpkg` executa bloqueios de arquivo (`fcntl`), extrai arquivos temporários, força escrita em disco (`fsync`) e aplica renomeação atômica (`rename`) por arquivo.

---

### 4.2. FreeBSD Ports (`misc/hello`) e Compilação Controlada (`--enable-nls` vs. `--disable-nls`)
Evidências: [`freebsd-ports-e-compilacao-hello.txt`](./evidencias/freebsd-ports-e-compilacao-hello.txt) e [`ports-compilacao-metricas.json`](./evidencias/ports-compilacao-metricas.json).

- **Receita oficial no FreeBSD Ports (`misc/hello/Makefile` e `distinfo`):**
  - Versão: `PORTVERSION=2.12.3`
  - Tarball oficial: `hello-2.12.3.tar.gz` (`1.269.080 bytes` / `1.239,34 KiB`, SHA-256 `bfd006eb9fd7a1a8fd4c8ef4f6ef26b1b7f271894c51e6d2c1b021a7ec5d2929`).
  - Opção de configuração: `OPTIONS_DEFINE=NLS`, `NLS_USES=gettext`, `NLS_CONFIGURE_ENABLE=nls`.
- **Comparação experimental (3 repetições completas de `extract -> configure -> make -j4 -> make DESTDIR=... install`):**

| Métrica Verificada (`hello 2.12.3`) | Com `NLS` (`--enable-nls`) | Sem `NLS` (`--disable-nls`) | Diferença / Impacto de SO |
| :--- | :--- | :--- | :--- |
| **Tempo de `./configure`** | `14.139,33 ± 163,68 ms` | `13.949,95 ± 174,89 ms` | `-1,3%` (testes de M4/autoconf quase idênticos) |
| **Tempo de `make -j4` (compilação)** | `4.819,95 ± 8,90 ms` | `4.888,16 ± 4,34 ms` | `~4,8 s` em ambos os casos |
| **Tempo de `make DESTDIR=... install` (stage)** | `687,89 ± 16,44 ms` | `258,30 ± 3,66 ms` | **`-62,5%` no tempo de instalação em stage** |
| **Tempo total de construção** | **`19.840,40 ± 183,84 ms`** | **`19.288,05 ± 175,85 ms`** | **~`530x` o tempo de instalar o `.deb` pronto (`37,3 ms`)** |
| **Tamanho instalado no `STAGEDIR`** | **`400,80 KiB` (`410.422 B`)** | **`193,81 KiB` (`198.462 B`)** | **`-51,6%` de espaço final instalado** |
| **Arquivos instalados (`STAGEDIR`)** | **`50` arquivos** (`46` `.mo`) | **`4` arquivos** (`0` `.mo`) | **`-46` arquivos de localização em `share/locale/`** |
| **Espaço temporário de build (`WRKDIR`)** | `7,45 MiB` (`723` arquivos) | `7,45 MiB` (`723` arquivos) | `~19x` maior que o pacote final instalado |
| **Total de syscalls (`strace -fc`)** | **`2.467.256` syscalls** | **`2.382.742` syscalls** | **`-84.514` syscalls sem `NLS` (~`1.000x` mais syscalls que `dpkg -i`)** |

**Interpretação de SO:** Compilar a partir do código-fonte desloca para a máquina local um custo de **~19,8 segundos**, **7,45 MiB de diretório temporário** e **2,47 milhões de chamadas de sistema** (sendo `790.471 openat`, `307.984 read`, `273.631 close` e `4.261 execve` disparados pelos subprocessos do script `configure` e do compilador). Em contrapartida, oferece uma capacidade impossível no modelo binário fixo do Debian: **adaptar o artefato construído**, cortando **51,6% do tamanho final instalado** e **92% da quantidade de arquivos** ao desativar o suporte `NLS`.

---

### 4.3. Nix (`Nix 2.35.6`) — Store Imutável, `RUNPATH` por Hash e Rollback Atômico
Evidências: [`nix-perfis-geracoes-vinculacao.txt`](./evidencias/nix-perfis-geracoes-vinculacao.txt), [`nix-metricas.json`](./evidencias/nix-metricas.json) e [`hello-unico-complemento.json`](./evidencias/hello-unico-complemento.json).

- **Caminho no store imutável:** `/nix/store/sd779x86bjaqxj2lzh2jsir4h0zjz6d1-hello-2.12.3`.
- **Tamanho próprio (NAR) vs. Fechamento completo (Closure):**
  - Tamanho próprio do pacote `hello` (NAR): **`273,04 KiB`** (`279.592 bytes`).
  - Fechamento completo (`closure` com `glibc-2.44-57`, `libidn2`, `libunistring`, `xgcc-libgcc`): **`36,73 MiB`** (`38.516.712 bytes` em `5` caminhos do store).
  - *Nota de SO:* Como os outros 4 pacotes da closure (`glibc`, etc.) já fazem parte da closure base do sistema, eles são compartilhados diretamente no `/nix/store` sem duplicação.
- **Vinculação dinâmica ELF (`readelf -d` e `ldd` em `/nix/store/...-hello-2.12.3/bin/hello`):**
  ```text
  0x0000000000000001 (NEEDED)   Shared library: [libc.so.6]
  0x000000000000001d (RUNPATH)  Library runpath: [/nix/store/r3hvhzl5fxhrgn0rfy5g7rda17702pj4-glibc-2.44-57/lib]
  libc.so.6 => /nix/store/r3hvhzl5fxhrgn0rfy5g7rda17702pj4-glibc-2.44-57/lib/libc.so.6
  ```
  Ao contrário do Debian (`/lib/x86_64-linux-gnu/libc.so.6`), o binário `hello` do Nix traz gravado no próprio cabeçalho ELF o endereço criptográfico exato da `glibc` com que foi construído (`RUNPATH`). Isso elimina o *dependency hell*: dez versões diferentes da `glibc` podem coexistir no `/nix/store` sem conflito.
- **Ativação de perfil e rollback atômico (3 repetições com `hello` já presente no store):**
  - `nix profile add` (criação de geração com `hello`): **`41,28 ± 0,89 ms`** (repetições: `40,25 ms`, `41,78 ms`, `41,81 ms`), com **`3.617` syscalls**.
  - `nix profile rollback` (reversão atômica entre gerações do perfil de `hello`): **`34,70 ± 0,52 ms`** (repetições: `35,29 ms`, `34,33 ms`, `34,48 ms`), com **`3.525` syscalls** (contendo apenas **`1 symlink`**, **`1 rename`** e **`1 flock`**, sem nenhum `fsync` de extração de pacotes).
  - Tempo de execução do binário: **`3,28 ± 0,10 ms`**.

---

### 4.4. Mecanismos de Flatpak (`OSTree` + `Bubblewrap`) e Snap (`SquashFS`) Aplicados ao `GNU hello`
Evidências: [`flatpak-snap-isolamento-e-imagens.txt`](./evidencias/flatpak-snap-isolamento-e-imagens.txt), [`flatpak-snap-metricas.json`](./evidencias/flatpak-snap-metricas.json) e [`hello-unico-complemento.json`](./evidencias/hello-unico-complemento.json).

Para manter **100% de consistência com o exemplo único `GNU hello`**, testamos diretamente os três mecanismos de Sistemas Operacionais que sustentam o Flatpak e o Snap sobre a própria árvore de arquivos e o próprio binário do `GNU hello`:

#### A. Deduplicação entre versões via `OSTree 2026.2` (mecanismo de armazenamento do Flatpak)
Comitamos a árvore completa do `hello` (`246,67 KiB`) em um repositório `OSTree` (`--mode=bare-user`) na branch `app/org.gnu.Hello/x86_64/stable`:
- **Commit v1 (`74eec73e...`):** árvore original do `hello`.
- **Commit v2 (`bced831c...`):** atualização apenas do manual `share/man/man1/hello.1.gz`, mantendo o binário `bin/hello` e os catálogos `.mo` inalterados.
- **Verificação de inodes no sistema de arquivos (`stat` nos dois checkouts simultâneos `co-1` e `co-2`):**
  - `co-1/bin/hello` $\rightarrow$ **`inode = 10495848`**, `nlink = 3`.
  - `co-2/bin/hello` $\rightarrow$ **`inode = 10495848`**, `nlink = 3`.
  - `co-1/share/man/man1/hello.1.gz` $\rightarrow$ `inode = 10495853` vs. `co-2/share/man/man1/hello.1.gz` $\rightarrow$ `inode = 10495856`.
- **Conclusão de SO:** O `OSTree` endereça cada arquivo pelo seu hash SHA-256 e materializa as versões no disco usando **hardlinks Posix (`linkat`)**. Duas versões instaladas do pacote compartilham fisicamente o mesmo `inode` (`10495848`) para o binário `bin/hello`, consumindo zero bytes extras para arquivos não modificados.

#### B. Confinamento de processo e sistema de arquivos via `Bubblewrap 0.13.1` (motor de sandbox do Flatpak)
Executamos o binário `hello` e testes de leitura/escrita dentro de um sandbox `bwrap --unshare-all` (criando novos namespaces de usuário, montagem, PID, rede e IPC):
1. **Overhead de criação do sandbox para executar `hello` (3 repetições):**
   - Execução direta de `hello`: **`3,28 ± 0,10 ms`**.
   - Execução de `hello` confinado com `bwrap --ro-bind /nix /nix --proc /proc --dev /dev --tmpfs /tmp --unshare-all`: **`7,78 ± 0,43 ms`**.
   - **Sobrecarga líquida do sandbox:** apenas **`+4,50 ms`**, exigindo **`963` chamadas de sistema** (destacando-se `1 unshare`, `17 mount`, `8 mount_setattr` e `2 pivot_root`).
2. **Controle de acesso ao sistema de arquivos (3 políticas verificadas):**
   - **Sem bind da pasta do usuário:** tentativa de ler arquivo fora do sandbox falha imediatamente com `No such file or directory` (`exit code 1`), pois o diretório sequer existe no namespace de montagem do processo após o `pivot_root`.
   - **Com `--ro-bind` (somente-leitura):** leitura autorizada (`exit code 0`), mas tentativa de gravar na pasta falha no VFS com `Read-only file system` (`exit code 1`).
   - **Com `--bind` (leitura e escrita):** leitura e gravação autorizadas (`exit code 0`).

#### C. Empacotamento em imagem comprimida somente-leitura via `SquashFS 4.7.5` (mecanismo de armazenamento do Snap)
Empacotamos a árvore completa do `hello` (`252.587 bytes` / `246,67 KiB` descompactados) em imagens `.snap` (`SquashFS 4.0`) com os três algoritmos suportados (`xz`, `zstd` e `gzip`), em 3 repetições:

| Compressor `SquashFS` (`hello`) | Tamanho da Imagem `.snap` | Razão vs. Original (`246,67 KiB`) | Tempo de Compressão (`mksquashfs`) | Tempo de Extração (`unsquashfs`) |
| :--- | :--- | :--- | :--- | :--- |
| **`xz`** | **`64,00 KiB`** (`65.536 B`) | **`0,259` (`25,9%`)** | `50,13 ± 0,60 ms` | `10,14 ± 0,17 ms` |
| **`zstd`** | **`68,00 KiB`** (`69.632 B`) | **`0,276` (`27,6%`)** | **`37,71 ± 2,88 ms` (`-24,8%`)** | `10,19 ± 0,21 ms` |
| **`gzip`** | **`72,00 KiB`** (`73.728 B`) | **`0,292` (`29,2%`)** | `36,87 ± 2,03 ms` | `10,42 ± 0,46 ms` |

---

## 5. Síntese Comparativa Transversal com o Exemplo Único (`GNU hello`)

A tabela abaixo resume todas as medições obtidas para o **`GNU hello`** no mesmo hardware e kernel (`Linux 7.3.4`), relacionando os números diretamente ao mecanismo de Sistema Operacional de cada abordagem:

| Dimensão de SO (`GNU hello`) | Debian (`APT / dpkg`) | FreeBSD Ports / Build do Fonte (`misc/hello`) | Nix (`nix profile` + `/nix/store`) | Flatpak (`OSTree` + `bwrap`) & Snap (`SquashFS`) |
| :--- | :--- | :--- | :--- | :--- |
| **Ambiente de execução do teste** | Container `debian:trixie-slim` sobre kernel `7.3.4` | Receita oficial FreeBSD Ports + build nativo no host | **100% nativo** no host NixOS `26.11` | **100% nativo** no host (`ostree`, `bwrap`, `squashfs`) |
| **Organização no VFS** | FHS global mutável (`/usr/bin/hello`, `/usr/share/locale/...`) | Prefixo `/usr/local` via `STAGEDIR` (`50` arq. c/ NLS; `4` s/ NLS) | Diretório imutável `/nix/store/<hash>-hello-2.12.3` | Commits `OSTree` c/ hardlinks (`inode 10495848`) ou imagem `.snap` `SquashFS` |
| **Vinculação dinâmica ELF (`readelf -d`)** | `NEEDED: libc.so.6` · **sem `RUNPATH`** (`/lib/x86_64-linux-gnu`) | Vinculado à `libc` do ambiente de compilação | `NEEDED: libc.so.6` + **`RUNPATH: /nix/store/<hash>-glibc/lib`** | Resolve bibliotecas dentro do runtime montado no namespace do sandbox |
| **Tamanho do artefato / disco** | `.deb`: `51,38 KiB` · Instalado: `188 KiB` | Tarball: `1.239 KiB` · Build: `7,45 MiB` · Final: **`400,8 KiB` (c/ NLS) ou `193,8 KiB` (s/ NLS, `-51,6%`)** | NAR próprio: **`273,04 KiB`** · Closure total c/ `glibc`: `36,73 MiB` | Imagem `SquashFS` do `hello`: **`64,0 KiB` (`xz`) / `68,0 KiB` (`zstd`)** · `OSTree`: `0 B` extra p/ binário igual |
| **Tempo da operação principal (3 rep.)** | `dpkg -i`: **`37,33 ± 0,47 ms`** | Build completo: **`19.840,4 ± 183,8 ms`** (c/ NLS) / **`19.288,1 ± 175,9 ms`** (s/ NLS) | `profile add`: **`41,28 ± 0,89 ms`** · `rollback`: **`34,70 ± 0,52 ms`** | `bwrap` sandbox: **`7,78 ± 0,43 ms`** (`+4,50 ms` vs. `3,28 ms` direto) |
| **Chamadas de sistema (`strace -fc`)** | **`2.478` syscalls** (`fsync`, `rename`, `fcntl` no FHS) | **`2.467.256` syscalls** (c/ NLS) / **`2.382.742`** (s/ NLS) | **`3.617` syscalls** (add) / **`3.525` syscalls** (rollback: `1 symlink`, `1 rename`) | **`963` syscalls** (`1 unshare`, `17 mount`, `8 mount_setattr`, `2 pivot_root`) |
| **Recuperação / Rollback** | Não transacional (exige reinstalar `.deb` anterior) | Recompilação ou reinstalação do pacote gerado | **Instantânea e atômica (`34,7 ms`)** por troca de link simbólico de geração | Reversão de commit `OSTree` ou montagem da revisão `.snap` anterior |

---

## 6. Conclusões do Checkpoint e Próximos Passos (Semana 5)

1. **Controlar o experimento com um único pacote (`GNU hello`) torna a comparação justa e transparente:** como o programa é o mesmo em todas as famílias, a diferença entre **`2.478` syscalls (`37,3 ms`)** no `dpkg`, **`2.467.256` syscalls (`19.840 ms`)** na compilação a partir do fonte, **`3.525` syscalls (`34,7 ms`)** no rollback atômico do `Nix` e **`963` syscalls (`+4,5 ms`)** no sandbox `Bubblewrap` reflete **exclusivamente a arquitetura de Sistemas Operacionais de cada gerenciador**.
2. **Transparência metodológica fortalece a validade do trabalho:** demonstramos exatamente como um único hospedeiro `NixOS` (`Linux 7.3.4`) permite executar nativamente `Nix`, `OSTree`, `Bubblewrap`, `SquashFS` e o build GNU Autotools, enquanto isola o FHS do `Debian 13` em container sobre o mesmo kernel e documenta os limites exatos do `OverlayFS`, do kernel `FreeBSD` e do `AppArmor`.
3. **Rumo à Semana 5:** na entrega final, integraremos este experimento controlado de base (`GNU hello`) com os casos de maior escala já coletados e guardados em [`./reserva-apresentacao-futura/`](./reserva-apresentacao-futura/README.md), fechando a matriz de decisão final do projeto.
