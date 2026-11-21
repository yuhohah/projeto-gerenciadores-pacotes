# Resultados Experimentais e Análise Comparativa — Semana 5

Este documento reúne os resultados finais dos testes em [`semana-05/evidencias/`](./evidencias/), comparando **cada aplicativo contra si mesmo nos cinco gerenciadores de pacotes** (`Debian APT/dpkg`, `FreeBSD Ports`, `Nix`, `Flatpak` e `Snap`), usando versões alinhadas pela referência do Debian:

1. **Tabela 1 — [`GNOME Text Editor` (`48.3`)](#1-gnome-text-editor-483)** *(aplicativo leve–médio, editor de texto)*
2. **Tabela 2 — [`VLC Media Player` (`3.0.24`)](#2-vlc-media-player-3024)** *(aplicativo médio–pesado, áudio e vídeo)*
3. **Tabela 3 — [`Blender` (`4.3.x` / `4.5 LTS`)](#3-blender-43x--45-lts)** *(aplicativo muito pesado, modelagem e renderização 3D)*

> **Como os testes foram feitos:** todos os testes rodaram no mesmo computador (processador AMD Ryzen 5 2600, 6 núcleos / 12 threads), com **3 repetições por tarefa** (os números abaixo mostram o valor mediano).
> - **Debian, Nix, Flatpak e Snap:** rodaram no Linux (`7.3.4`), com o serviço oficial do Snap (`snapd`) ativo para executar os pacotes Snap de verdade.
> - **Como o FreeBSD `Ports` foi rodado:** como programas do FreeBSD não rodam direto no Linux, subimos uma **máquina virtual com FreeBSD `14.4`** no mesmo computador, usando diretamente a CPU física da máquina (QEMU/KVM). Para medir apenas o tempo de compilar cada aplicativo — e não gastar várias horas compilando bibliotecas básicas do sistema —, instalamos antes as dependências prontas via `pkg`, compilamos cada um dos 3 programas a partir do código-fonte pelo `/usr/ports` (`make build` + `make install`) e depois rodamos exatamente as mesmas 3 tarefas dentro do FreeBSD.

---

## 1. `GNOME Text Editor` (`48.3`)

**Mesma tarefa executada nos 5 gerenciadores:** abrir o programa e consultar sua versão e bibliotecas gráficas (`gnome-text-editor --version`).

| Critério / Métrica | **Debian (`APT/dpkg`)** | **FreeBSD `Ports`** | **Nix** | **Flatpak** | **Snap (`snapd`)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Versão avaliada** | `48.3-3` | `47.4`\* (`editors/gnome-text-editor`) | `48.3` | `48.3` | `48.3` |
| **Download do pacote** | `45,04 MiB` | `0,61 MiB` | `2,48 MiB` | `1,4 MB` (`+ 432,8 MB` base) | `1,07 MiB` |
| **Espaço total em disco (com dependências/bases)** | `179,74 MiB` | `911,10 MiB` (`2,20 MiB` do app + `126` pacotes) | `991,36 MiB` (`315` pastas) | `2,5 MB` (`+ 1,1 GB` base GNOME) | `1,07 MiB` (`+ 1.176,54 MiB` bases Snap) |
| **Opções de compilação / empacotamento** | Pronto (`133` pacotes) | `0` opções extras no `Makefile` | Pacote pronto | Base compartilhada `GNOME 51` | Bases `core24` + `gnome-46` + `mesa` |
| **Instalação / Compilação (tempo)** | **`14,80 s`** | **`15,24 s`**† | **`36,57 ms`** | *Não cronometrada* (local) | **`2,76 s`**‡ |
| **Voltar versão (rollback)** | Não nativo | Não nativo | **`29,73 ms`** | Sim (por versão no OSTree) | Sim (revisões do Snap) |
| **Segurança / Isolamento (sandbox)** | Sem isolamento | Sem isolamento | Sem isolamento | **Isolado** (sem acesso à rede) | **Isolado (`strict`)** (`8` permissões) |
| **Execução — Tempo** | **`34,00 ms`** | **`36,49 ms`** | **`33,26 ms`** | **`36,80 ms`** | **`434,45 ms`** |
| **Execução — RAM usada (pico)** | **`25,14 MiB`** | **`56,82 MiB`** | **`23,46 MiB`** | **`23,43 MiB`** | **`33,23 MiB`** |
| **Execução — CPU (`usuário + sistema` / `%`)** | **`0,02 + 0,00 = 0,02 s`** (`96%`) | **`0,03 + 0,00 = 0,03 s`** (`82%`) | **`0,01 + 0,01 = 0,02 s`** (`93%`) | **`0,01 + 0,01 = 0,02 s`** (`93%`) | **`0,09 + 0,16 = 0,25 s`** (`59%`) |
| **Execução — Chamadas ao SO (`syscalls`)** | **`1.105`** | **`1.713`** | **`1.896`** | **`2.435`** | **`17.181`** |

**Principais pontos do `GNOME Text Editor`:**
- **Execução, RAM e CPU:** **Debian** (`34,00 ms`), **Nix** (`33,26 ms`), **FreeBSD `Ports`** (`36,49 ms`) e **Flatpak** (`36,80 ms`) tiveram tempos praticamente iguais. No FreeBSD, a RAM usada (`56,82 MiB`) ficou maior por causa do gerenciador de memória próprio do FreeBSD e de uma versão mais nova da biblioteca gráfica (`GTK 4.20`). Já o **Snap** demorou **`434,45 ms`** (~12× mais), usou **`0,25 s`** de CPU e fez **`17.181` chamadas ao sistema** por causa da etapa de preparação do seu isolamento (`strict`).
- **Instalação vs. compilação:** como o aplicativo é pequeno (`0,61 MiB` de código-fonte), compilar e instalar no **FreeBSD `Ports`** levou apenas **`15,24 s`** — praticamente empatado com descompactar os `133` pacotes do **Debian** (`14,80 s`), atrás do **Snap** (`2,76 s`) e do **Nix** (`36,57 ms`).
- **Melhor compressão no Snap:** **`zstd`** (`16,63 ms` de extração).

---

## 2. `VLC Media Player` (`3.0.24`)

**Mesma tarefa executada nos 5 gerenciadores:** converter um arquivo de áudio `WAV` (2 segundos) para `OGG` pelo terminal, sem abrir janela gráfica, conferindo se o áudio final foi gerado corretamente (`~11,5 KiB`).

| Critério / Métrica | **Debian (`APT/dpkg`)** | **FreeBSD `Ports`** | **Nix** | **Flatpak** | **Snap (`snapd`)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Versão avaliada** | `3.0.24` | `3.0.24` (`multimedia/vlc`) | `3.0.24` | `3.0.24` | `3.0.24-rc1` |
| **Download do pacote** | `128,90 MiB` | `26,34 MiB` | `65,89 MiB` | `58,1 MB` (`+ 367,4 MB` base) | `264,78 MiB` |
| **Espaço total em disco (com dependências/bases)** | `477,60 MiB` | `1.843,79 MiB` (`57,19 MiB` do app + `183` pacotes) | `1.071,72 MiB` (`249` pastas) | `149,8 MB` (`+ 974,3 MB` base KDE) | `264,78 MiB` (`+ 2.223,89 MiB` bases Snap) |
| **Opções de compilação / empacotamento** | Pronto (`253` pacotes) | **`72` opções** (`33` ativas por padrão) | Pacote pronto | Base compartilhada `KDE 5.15` | Bases `core24` + `kf6` + `mesa` |
| **Instalação / Compilação (tempo)** | **`27,83 s`** | **`3 min 43 s`** (`222,92 s`)† | **`36,33 ms`** | *Não cronometrada* (local) | **`6,94 s`**‡ |
| **Voltar versão (rollback)** | Não nativo | Não nativo | **`29,85 ms`** | Sim (por versão no OSTree) | Sim (revisões do Snap) |
| **Segurança / Isolamento (sandbox)** | Sem isolamento | Sem isolamento | Sem isolamento | **Isolado** (acesso a dispositivos e arquivos) | **Isolado (`strict`)** (**`25` permissões separadas**) |
| **Execução — Tempo** | **`222,00 ms`** | **`204,85 ms`** | **`188,61 ms`** | **`192,46 ms`** | **`444,45 ms`** |
| **Execução — RAM usada (pico)** | **`40,06 MiB`** | **`125,96 MiB`** | **`35,20 MiB`** | **`34,42 MiB`** | **`39,62 MiB`** |
| **Execução — CPU (`usuário + sistema` / `%`)** | **`0,08 + 0,02 = 0,10 s`** (`57%`) | **`0,10 + 0,01 = 0,11 s`** (`52%`) | **`0,07 + 0,02 = 0,09 s`** (`52%`) | **`0,07 + 0,03 = 0,09 s`** (`53%`) | **`0,15 + 0,13 = 0,29 s`** (`66%`) |
| **Execução — Chamadas ao SO (`syscalls`)** | **`4.935`** | **`4.865`** | **`5.618`** | **`6.121`** | **`15.935`** |

**Principais pontos do `VLC 3.0.24`:**
- **Execução, RAM e CPU:** **Nix** (`188,61 ms`) e **Flatpak** (`192,46 ms`) foram os mais rápidos e econômicos em memória. O **FreeBSD `Ports`** foi mais rápido que o **Debian** (`204,85 ms` vs. `222,00 ms`) e fez o **menor número de chamadas ao sistema (`4.865`)**, mas consumiu mais RAM (`125,96 MiB`). O **Snap** manteve RAM parecida com o Debian (`39,62 MiB`), porém levou **`444,45 ms`** e **`15.935` chamadas** por causa da abertura no modo `strict`.
- **Compilação vs. pacote pronto:** num programa médio–pesado já aparece o custo de compilar no computador do usuário — o **FreeBSD `Ports`** levou **`3 min 43 s`** (~8× o tempo do Debian), mas permite escolher entre **72 opções de recursos** (formatos de áudio/vídeo, aceleração e interfaces).
- **Melhor compressão no Snap:** **`zstd`** (`45,28 ms` de extração).

---

## 3. `Blender` (`4.3.x` / `4.5 LTS`)

**Mesma tarefa executada nos 5 gerenciadores:** renderizar uma cena 3D (`320×240`, `4 amostras`, 4 threads na CPU) salvando uma imagem `PNG`, sem abrir janela gráfica, conferindo o arquivo gerado (`~44–49 KiB`).

| Critério / Métrica | **Debian (`APT/dpkg`)** | **FreeBSD `Ports`** | **Nix** | **Flatpak** | **Snap (`snapd`)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Versão avaliada** | `4.3.2` | `4.5.14`\* (`graphics/blender4`) | `4.3.2` | `4.3.2` | `4.3.1` |
| **Download do pacote** | `281,58 MiB` | `81,16 MiB` | `252,15 MiB` | `508,8 MB` (`+ 282,7 MB` base) | `402,27 MiB` |
| **Espaço total em disco (com dependências/bases)** | `1.093,95 MiB` | `4,51 GiB` (`219,68 MiB` do app + `204` pacotes) | `2.243,89 MiB` (`330` pastas) | `1,2 GB` (`+ 724,2 MB` base) | `402,27 MiB` (`+ 63,80 MiB` base `core20`) |
| **Opções de compilação / empacotamento** | Pronto (`355` pacotes) | **`57` opções** (`46` ativas por padrão) | Pacote pronto | Base `Freedesktop 26.08` | Base `core20` (`27` canais de versão) |
| **Instalação / Compilação (tempo)** | **`42,68 s`** | **`34 min 12 s`** (`2.052,32 s`)† | **`36,61 ms`** | *Não cronometrada* (local) | **`5,42 s`**‡ |
| **Voltar versão (rollback)** | Não nativo | Não nativo | **`29,17 ms`** | Sim (por versão no OSTree) | Sim (revisões do Snap) |
| **Segurança / Isolamento (sandbox)** | Sem isolamento | Sem isolamento | Sem isolamento | **Isolado** (acesso a vídeo e arquivos) | **Modo `classic`** (**sem isolamento**) |
| **Execução — Tempo** | **`1.880,00 ms`** | **`1.624,06 ms`** | **`1.338,76 ms`** | **`1.337,37 ms`** | **`642,99 ms`** |
| **Execução — RAM usada (pico)** | **`351,03 MiB`** | **`426,79 MiB`** | **`316,13 MiB`** | **`268,20 MiB`** | **`295,46 MiB`** |
| **Execução — CPU (`usuário + sistema` / `%`)** | **`1,85 + 0,17 = 2,02 s`** (`109%`) | **`1,75 + 0,04 = 1,79 s`** (`110%`) | **`1,35 + 0,11 = 1,46 s`** (`109%`) | **`1,32 + 0,16 = 1,47 s`** (`111%`) | **`0,68 + 0,12 = 0,80 s`** (`126%`) |
| **Execução — Chamadas ao SO (`syscalls`)** | **`12.980`** | **`14.331`** | **`16.133`** | **`16.122`** | **`13.307`** |

**Principais pontos do `Blender`:**
- **Execução, RAM e CPU:** com o sistema aquecido, o **Snap `4.3.1` (`classic`)** foi o mais rápido (**`642,99 ms`**, `0,80 s` de CPU), seguido por **Flatpak** (`1.337,37 ms`, menor RAM: `268,20 MiB`), **Nix** (`1.338,76 ms`), **FreeBSD `Ports`** (`1.624,06 ms`, `426,79 MiB`) e **Debian** (`1.880,00 ms`). O Snap venceu porque entrega o **executável oficial já otimizado pela própria equipe do Blender** e, por usar o modo **`classic`**, pula toda a preparação pesada do modo `strict`. *(Na primeira abertura a frio, antes de ficar em cache na memória, o Snap levou `6,39 s`.)*
- **Custo alto de compilar um app grande (`Ports`):** compilar apenas o `blender4` levou **`34 min 12 s`** (somando **`3,29 horas` de trabalho dos núcleos da CPU** e pico de `1,13 GiB` de RAM no compilador), além de ocupar **`4,51 GiB`** em disco por causa das `204` bibliotecas ligadas às `46` opções ativas por padrão. No mesmo app, o **Nix** ativou em **`36,61 ms`**, o **Snap** instalou em **`5,42 s`** e o **Debian** em **`42,68 s`**.
- **Segurança no Blender:** o **Flatpak** continua isolando o aplicativo sem perder velocidade, enquanto o **Snap** precisa desativar o isolamento (`classic`) e depender de bibliotecas gráficas do sistema.
- **Melhor compressão no Snap:** **`gzip`** (`164,15 ms` de extração).

---

### Notas sobre as 3 tabelas

- **(\*) Versões no FreeBSD `Ports`:** `47.4` é a versão mais recente do `gnome-text-editor` disponível no Ports; para o Blender, usamos o port oficial **`graphics/blender4` (`4.5.14` LTS)**, compatível com o Python padrão do FreeBSD 14.4.
- **(†) Como o FreeBSD `Ports` foi rodado e cronometrado:** instalamos o **FreeBSD `14.4`** numa **máquina virtual (QEMU/KVM)** no mesmo computador, repassando a CPU física diretamente para a VM. As dependências de compilação foram instaladas antes via pacotes prontos (`pkg`), e cronometramos a **compilação do código-fonte + instalação** de cada um dos 3 programas (`make build` + `make install`: `8` tarefas paralelas no Editor/VLC e `6` no Blender para caber nos 8 GiB de RAM da VM). Compilar também todas as bibliotecas de apoio do zero levaria várias horas extras. Depois da instalação, cada programa rodou 1 vez para aquecer e 3 vezes cronometradas (medindo tempo/RAM/CPU com `/usr/bin/time -l` e chamadas ao sistema com `truss`).
- **(‡) Tempo de instalação no `Snap`:** os tempos na tabela (`2,76 s`, `6,94 s` e `5,42 s`) são da **instalação local sem internet** (com as bases já baixadas, comparável ao Debian offline). Na primeira instalação online baixando tudo da loja, os tempos foram `142,6 s` (Editor), `297,7 s` (VLC) e `64,1 s` (Blender).
- **Por que o `Snap` demorou bem mais no `GNOME Text Editor` (`434 ms`) e no `VLC` (`444 ms`)?** O modo de isolamento (`confinement`: `strict` ou `classic`) é próprio do **Snap**. Nos dois apps em modo **`strict`** (isolado), toda vez que o programa abre o Snap precisa montar o ambiente seguro, conectar pacotes de apoio e rodar vários scripts de preparação antes do aplicativo começar — isso cria **25 a 27 processos extras** (contra 1 no Debian) e dispara **15,9 a 17,2 mil chamadas ao sistema**, criando um atraso fixo de **~250 a 400 ms** que pesa muito em tarefas rápidas. Já o `Blender` usa o modo **`classic`** (sem isolamento), pulando essa etapa (só 8 processos) e evitando o atraso.

---

## 4. Reaproveitamento de Disco entre Aplicativos e Volta de Versão (`Rollback`)

- **Debian (`/usr` compartilhado):** usa o menor espaço porque todos os programas dividem uma única cópia de cada biblioteca nas pastas padrão do sistema (`180 MiB` → `478 MiB` → `1,09 GiB`).
- **FreeBSD `Ports` (`/usr/local` compartilhado):** também divide bibliotecas entre programas, mas como o padrão ativa muitas opções extras (`46` no Blender), o espaço total instalado cresceu bastante (`4,51 GiB` no Blender) — podendo ser reduzido se o usuário desmarcar o que não usa antes de compilar.
- **Nix (`/nix/store`):** quando os 3 apps usam a **mesma versão do repositório**, **`48,7%` das pastas são reaproveitadas** (`447` de `917`, com `176` comuns aos 3). Quando fixamos 3 versões históricas diferentes, o reaproveitamento cai para **`0%`**, porque cada versão fica isolada sem gerar conflito.
- **Flatpak:** entre versões diferentes do mesmo app, o sistema reaproveita os mesmos arquivos no disco sem duplicar o que não mudou. Porém, como os 3 apps usam interfaces diferentes (GNOME, KDE e Freedesktop), exigem **3 bases separadas** (~`2,8 GB` no total).
- **Snap:** os 3 apps juntos com suas bases ocuparam **`3,52 GiB`** em disco (`kf6-core24`, usada pelo VLC, sozinha ocupa `1,62 GiB`), reaproveitando partes comuns entre Editor e VLC.
- **Dados pessoais protegidos no `rollback` (`Nix`):** voltar para uma versão anterior do perfil levou apenas **`~29 ms`** (trocando um atalho) e manteve intactos os documentos do usuário e outros perfis.

---

## 5. Por que NÃO dá para atualizar um app de um gerenciador usando outro?

Uma dúvida comum é: *"Se eu instalei o `VLC` ou o `Blender` pelo `APT`, posso atualizar usando `Flatpak`, `Snap` ou `Nix`?"*

**Não.** Cada gerenciador controla seus programas de forma totalmente separada por **quatro motivos**:

1. **Registros separados:** cada um guarda sua própria lista de programas instalados (`dpkg`, `pkg`, `nix`, `OSTree`, `snapd`). Um gerenciador não sabe o que o outro instalou.
2. **Pastas separadas (duplicação em vez de atualização):** instalar o `Blender` pelo `Flatpak` quando ele já existe pelo `APT` não substitui o antigo — cria uma **segunda cópia paralela** no disco.
3. **Formatos e modos de execução incompatíveis:** o `Debian` usa as bibliotecas globais do sistema; o `Nix` usa pastas isoladas em `/nix/store`; o `Flatpak` roda dentro de uma caixa isolada; e o `Snap` monta arquivos compactados (`SquashFS`). Eles não conseguem atualizar o pacote um do outro.
4. **Sistemas diferentes (`FreeBSD Ports`):** programas compilados para o FreeBSD são feitos para outro sistema operacional e não substituem programas Linux.

### Duas exceções aparentes

- **Ferramentas do mesmo ecossistema:** instalar um `.deb` com `dpkg` e atualizar com `apt` (ou compilar no `FreeBSD Ports` e atualizar com `pkg`) funciona porque ambos usam o **mesmo registro local**.
- **Lojas gráficas (`GNOME Software`, `KDE Discover`):** mostram atualizações de `APT`, `Flatpak` e `Snap` juntas na tela, mas nos bastidores apenas chamam cada gerenciador separado.

> **Na prática:** para trocar de gerenciador, **desinstale no antigo e instale no novo** — seus arquivos pessoais continuam salvos.

---

## 6. Síntese Final — Qual escolher em cada cenário?

| Prioridade | Melhor escolha | Resumo baseado nos testes |
| :--- | :--- | :--- |
| **Economizar disco e integrar direto ao sistema** | **Debian (`APT/dpkg`)** | Menor uso de disco (`180 MiB` → `478 MiB` → `1,09 GiB`) e poucas chamadas ao SO; porém sem isolamento e instalação mais demorada (`14,8–42,7 s`). |
| **Personalizar recursos na compilação** | **FreeBSD `Ports`** | Permite escolher cada recurso antes de compilar (**72 opções no VLC** e **57 no Blender**) e entrega boa velocidade de execução (`4.865` chamadas no VLC), mas o tempo de compilação cresce muito em apps grandes (`15,2 s` → `3 min 43 s` → `34 min 12 s`). |
| **Reprodutibilidade e volta rápida sem risco** | **Nix** | Ativa em `~36,5 ms` e volta versão em `~29,5 ms` sem tocar nos arquivos pessoais, reaproveita `48,7%` do disco na mesma revisão e roda rápido nos 3 apps. |
| **Segurança com isolamento sem perder desempenho** | **Flatpak** | Isola os aplicativos com atraso quase zero (`+3–4 ms`, empate no Blender) e uso de RAM igual ao nativo, mantendo o isolamento até no `Blender`. |
| **Canais oficiais e builds prontos do fabricante** | **Snap (`snapd`)** | Instalação local rápida (`2,8–6,9 s`), `27` canais no `Blender` e melhor tempo no render do `Blender` (`643 ms`); porém apps `strict` abrem mais devagar (`434–444 ms`), bases ocupam mais espaço (`3,52 GiB`) e o `Blender` abre mão do isolamento (`classic`). |
