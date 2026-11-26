# Comparação Prática de Gerenciadores de Pacotes em Unix/Linux

**Disciplina:** Sistemas Operacionais (`INF0336`) — Instituto de Informática (UFG)  
**Integrantes:** Luan de Paula Mota (`202003588`) · Joao Carlos (`202401792`) · Gabrielle Siqueira (`202200511`) · Lya Ribeiro (`202107857`)

---

## 1. Introdução e Objetivo

Gerenciadores de pacotes definem como programas são instalados, atualizados, isolados e executados no sistema operacional. Este relatório compara **cinco gerenciadores de pacotes** em quatro famílias, avaliando na prática instalação/compilação, espaço em disco, volta de versão (*rollback*), segurança (isolamento) e desempenho em execução:

- **Debian (`APT/dpkg`) — binários tradicionais:** instala pacotes prontos nas pastas padrão do sistema, compartilhando bibliotecas entre todos os programas.
- **FreeBSD `Ports` — código-fonte:** baixa o código-fonte e compila cada programa no computador do usuário, permitindo escolher recursos antes da construção.
- **`Nix` — funcional e imutável:** guarda cada programa e suas bibliotecas em pastas isoladas (`/nix/store`), permitindo voltar versões por troca de atalho.
- **`Flatpak` — isolado (sandbox):** executa aplicativos em ambiente isolado usando bases gráficas compartilhadas e controle de versões (`OSTree`).
- **`Snap` (`snapd`) — isolado (sandbox):** distribui programas em arquivos compactados (`SquashFS`), rodando no modo isolado (`strict`) ou livre (`classic`).

---

## 2. Ambiente e Como os Testes Foram Feitos

Todos os testes rodaram no **mesmo computador físico** (`AMD Ryzen 5 2600`, 6 núcleos / 12 threads, `15 GiB` de RAM, SSD NVMe), comparando **cada aplicativo contra si mesmo nos cinco gerenciadores**, com **3 repetições por tarefa** (mediana reportada):

1. **`GNOME Text Editor` (`48.3`)** *(leve–médio)*: abrir e consultar versão e bibliotecas gráficas (`gnome-text-editor --version`).
2. **`VLC Media Player` (`3.0.24`)** *(médio–pesado)*: converter um áudio `WAV` (2 s) para `OGG` pelo terminal, sem interface gráfica.
3. **`Blender` (`4.3.x` / `4.5 LTS`)** *(muito pesado)*: renderizar uma cena 3D (`320×240`, 4 amostras, 4 threads na CPU) em imagem `PNG` pelo terminal.

- **Debian, Nix, Flatpak e Snap:** rodaram no Linux (`7.3.4`), com o serviço oficial do Snap (`snapd`) ativo para execução real dos pacotes.
- **Execução do FreeBSD `Ports`:** como programas do FreeBSD não rodam direto no Linux, subimos uma **máquina virtual com FreeBSD `14.4`** no mesmo computador repassando diretamente a CPU física via QEMU/KVM (`8` vCPUs, `8 GiB` RAM). As dependências de compilação foram pré-instaladas via `pkg`; cada um dos 3 programas foi compilado a partir do código-fonte pelo `/usr/ports` (`make build` + `make install`) e executado nas mesmas 3 tarefas dentro do FreeBSD.

---

## 3. Resultados Experimentais por Aplicativo

### 3.1 `GNOME Text Editor` (`48.3`)

| Critério | **Debian (`APT/dpkg`)** | **FreeBSD `Ports`** | **Nix** | **Flatpak** | **Snap (`snapd`)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Versão / Base** | `48.3-3` (`133` pkgs) | `47.4`\* (`0` opç.) | `48.3` (pronto) | `48.3` (`GNOME 51`) | `48.3` (`core24`+`gnome-46`) |
| **Download do pacote** | `45,04 MiB` | `0,61 MiB` | `2,48 MiB` | `1,4 MB` (+`432,8 MB` base) | `1,07 MiB` |
| **Disco total (c/ bases)** | **`179,74 MiB`** | `911,10 MiB` (`126` pkgs) | `991,36 MiB` | `2,5 MB` + `1,1 GB` GNOME | `1,07` + `1.177 MiB` bases |
| **Instalação / Compil.** | `14,80 s` | `15,24 s`† | **`36,57 ms`** | Local (`OSTree`) | `2,76 s`‡ |
| **Voltar versão** | Não nativo | Não nativo | **`29,73 ms`** | Sim (`OSTree`) | Sim (revisões) |
| **Isolamento (sandbox)** | Sem isolamento | Sem isolamento | Sem isolamento | **Isolado** (sem rede) | **Isolado (`strict`)** (`8` perm.) |
| **Execução — Tempo** | `34,00 ms` | `36,49 ms` | **`33,26 ms`** | `36,80 ms` | `434,45 ms` |
| **Execução — RAM (pico)** | `25,14 MiB` | `56,82 MiB` | `23,46 MiB` | **`23,43 MiB`** | `33,23 MiB` |
| **Execução — CPU / SO** | `0,02 s` (`96%`) / **`1.105`** | `0,03 s` (`82%`) / `1.713` | `0,02 s` (`93%`) / `1.896` | `0,02 s` (`93%`) / `2.435` | `0,25 s` (`59%`) / `17.181` |

- **Destaques:** **Nix** (`33,26 ms`), **Debian** (`34,00 ms`), **Ports** (`36,49 ms`) e **Flatpak** (`36,80 ms`) ficaram empatados. No FreeBSD, a RAM (`56,82 MiB`) foi maior pelo gerenciador de memória próprio e `GTK 4.20`; por ser pequeno (`0,61 MiB` de fonte), compilar no `Ports` (`15,24 s`) empatou com o Debian (`14,80 s`). O **Snap** levou `434,45 ms` (~12× mais) e `17.181` chamadas pelo modo `strict` (melhor compressão: `zstd`, `16,63 ms`).

### 3.2 `VLC Media Player` (`3.0.24`)

| Critério | **Debian (`APT/dpkg`)** | **FreeBSD `Ports`** | **Nix** | **Flatpak** | **Snap (`snapd`)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Versão / Base** | `3.0.24` (`253` pkgs) | `3.0.24` (**`72` opç.**, `33` pdr.) | `3.0.24` (pronto) | `3.0.24` (`KDE 5.15`) | `3.0.24-rc1` (`core24`+`kf6`) |
| **Download do pacote** | `128,90 MiB` | `26,34 MiB` | `65,89 MiB` | `58,1 MB` (+`367,4 MB` base) | `264,78 MiB` |
| **Disco total (c/ bases)** | **`477,60 MiB`** | `1.843,79 MiB` (`183` pkgs) | `1.071,72 MiB` | `149,8 MB` + `974 MB` KDE | `264,8` + `2.224 MiB` bases |
| **Instalação / Compil.** | `27,83 s` | `3 min 43 s`† | **`36,33 ms`** | Local (`OSTree`) | `6,94 s`‡ |
| **Voltar versão** | Não nativo | Não nativo | **`29,85 ms`** | Sim (`OSTree`) | Sim (revisões) |
| **Isolamento (sandbox)** | Sem isolamento | Sem isolamento | Sem isolamento | **Isolado** (disp./arq.) | **Isolado (`strict`)** (`25` perm.) |
| **Execução — Tempo** | `222,00 ms` | `204,85 ms` | **`188,61 ms`** | `192,46 ms` | `444,45 ms` |
| **Execução — RAM (pico)** | `40,06 MiB` | `125,96 MiB` | `35,20 MiB` | **`34,42 MiB`** | `39,62 MiB` |
| **Execução — CPU / SO** | `0,10 s` (`57%`) / `4.935` | `0,11 s` (`52%`) / **`4.865`** | `0,09 s` (`52%`) / `5.618` | `0,09 s` (`53%`) / `6.121` | `0,29 s` (`66%`) / `15.935` |

- **Destaques:** **Nix** (`188,61 ms`) e **Flatpak** (`192,46 ms`, menor RAM: `34,42 MiB`) lideraram. O **FreeBSD `Ports`** superou o Debian (`204,85 ms`) com o **menor número de chamadas ao SO (`4.865`)**, porém compilar já levou `3 min 43 s` (~8× o Debian) em troca de **`72` opções** configuráveis. O **Snap** levou `444,45 ms` e `15.935` chamadas pelo modo `strict` (melhor compressão: `zstd`, `45,28 ms`).

### 3.3 `Blender` (`4.3.x` / `4.5 LTS`)

| Critério | **Debian (`APT/dpkg`)** | **FreeBSD `Ports`** | **Nix** | **Flatpak** | **Snap (`snapd`)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Versão / Base** | `4.3.2` (`355` pkgs) | `4.5.14`\* (**`57` opç.**, `46` pdr.) | `4.3.2` (pronto) | `4.3.2` (`Fdo 26.08`) | `4.3.1` (`core20`, `27` canais) |
| **Download do pacote** | `281,58 MiB` | `81,16 MiB` | `252,15 MiB` | `508,8 MB` (+`282,7 MB` base) | `402,27 MiB` |
| **Disco total (c/ bases)** | `1.093,95 MiB` | `4,51 GiB` (`204` pkgs) | `2.243,89 MiB` | `1,2 GB` + `724 MB` base | **`402,3` + `63,8 MiB` `core20`** |
| **Instalação / Compil.** | `42,68 s` | `34 min 12 s`† | **`36,61 ms`** | Local (`OSTree`) | `5,42 s`‡ |
| **Voltar versão** | Não nativo | Não nativo | **`29,17 ms`** | Sim (`OSTree`) | Sim (revisões) |
| **Isolamento (sandbox)** | Sem isolamento | Sem isolamento | Sem isolamento | **Isolado** (vídeo/arq.) | Modo `classic` (sem isolam.) |
| **Execução — Tempo** | `1.880,00 ms` | `1.624,06 ms` | `1.338,76 ms` | `1.337,37 ms` | **`642,99 ms`** |
| **Execução — RAM (pico)** | `351,03 MiB` | `426,79 MiB` | `316,13 MiB` | **`268,20 MiB`** | `295,46 MiB` |
| **Execução — CPU / SO** | `2,02 s` (`109%`) / **`12.980`** | `1,79 s` (`110%`) / `14.331` | `1,46 s` (`109%`) / `16.133` | `1,47 s` (`111%`) / `16.122` | **`0,80 s`** (`126%`) / `13.307` |

- **Destaques:** com cache aquecido, o **Snap `4.3.1` (`classic`)** venceu (`642,99 ms`, `0,80 s` de CPU; 1ª abertura a frio: `6,39 s`) por entregar o executável oficial otimizado e pular o modo `strict` (melhor compressão: `gzip`, `164,15 ms`). **Flatpak** (`1.337,37 ms`, menor RAM: `268,20 MiB`, único com isolamento ativo) e **Nix** (`1.338,76 ms`) vieram a seguir. Compilar o `blender4` no **`Ports`** levou **`34 min 12 s`** (`3,29 h` somadas de CPU; `1,13 GiB` de RAM no compilador) e ocupou `4,51 GiB` pelas `46` opções padrão.

> **Notas:** **(\*)** `47.4` é a versão mais nova do Editor no Ports; no Blender, usamos `graphics/blender4` (`4.5.14` LTS), compatível com o Python padrão do FreeBSD 14.4. **(†)** `make build` + `make install` na VM FreeBSD 14.4 (`13,8+1,5 s`; `184,1+38,9 s`; `2.028,6+23,7 s`); compilar todas as dependências do zero levaria horas extras. **(‡)** Instalação local do Snap (offline, bases já baixadas); na 1ª instalação online da loja foram `142,6 s`, `297,7 s` e `64,1 s`. **CPU / SO:** tempo efetivo de CPU (> `100%` no Blender pelo uso de múltiplos núcleos) e chamadas ao SO (`strace`/`truss`).

---

## 4. Análise Transversal

- **Por que o Snap demorou mais no Editor (`434 ms`) e no VLC (`444 ms`)?** O confinamento (`confinement`) é próprio do Snap. No modo **`strict`** (Editor e VLC), cada abertura monta o ambiente isolado, conecta pacotes de apoio (`kf6-core24`, etc.) e roda scripts extras — gerando **25 a 27 processos** (contra `1` no Debian) e **15,9–17,2 mil chamadas ao SO**, com atraso fixo de **~250–400 ms**. No **`classic`** (Blender), o isolamento é desligado (`8` processos), eliminando esse atraso.
- **Disco, reaproveitamento e rollback:** o **Debian** economiza mais disco (`180 MiB` → `1,09 GiB`), mas sem rollback nativo. O **`Ports`** cresce conforme opções padrão (`4,51 GiB` no Blender), ajustáveis antes de compilar. O **`Nix`** reaproveitou **`48,7%`** das pastas na mesma revisão (`447/917`, `176` comuns; `0%` em revisões distintas) e voltou versão em **`~29 ms`** preservando arquivos pessoais. O **`Flatpak`** precisou de 3 bases gráficas (`~2,8 GB`), mas manteve isolamento nos 3 apps sem perder velocidade. O **`Snap`** ocupou **`3,52 GiB`** ao todo (`kf6-core24`: `1,62 GiB`).
- **Por que não dá para atualizar pacotes entre gerenciadores distintos?** Cada um possui **registro próprio** (`dpkg`, `pkg`, `nix`, `OSTree`, `snapd`), **pastas separadas** (instalar em outro duplica o app), **formatos incompatíveis** e, no FreeBSD `Ports`, **outro sistema operacional**. Exceções aparentes são ferramentas do mesmo ecossistema (`dpkg`/`apt`; `Ports`/`pkg`) e lojas gráficas que apenas chamam cada gerenciador em separado. Para trocar, desinstala-se no antigo e instala-se no novo mantendo os arquivos pessoais.

---

## 5. Conclusão e Síntese por Cenário

Não há um único "melhor" gerenciador: cada arquitetura prioriza um compromisso distinto de Sistemas Operacionais.

| Prioridade | Melhor escolha | Justificativa baseada nos testes |
| :--- | :--- | :--- |
| **Economizar disco e integrar ao sistema** | **Debian (`APT/dpkg`)** | Menor espaço (`180 MiB` → `1,09 GiB`) e poucas chamadas ao SO; sem isolamento e sem rollback nativo. |
| **Personalizar recursos na compilação** | **FreeBSD `Ports`** | Máximo controle (`72` opç. no VLC; `57` no Blender) e boa velocidade, mas compilação longa em apps grandes (`34 min 12 s`). |
| **Reprodutibilidade e rollback seguro** | **`Nix`** | Ativação em `~36,5 ms`, rollback em `~29,5 ms` sem tocar nos arquivos pessoais e `48,7%` de reaproveitamento na mesma revisão. |
| **Segurança com alto desempenho** | **`Flatpak`** | Melhor equilíbrio geral: isolamento ativo nos 3 apps (inclusive no Blender) com tempo e RAM iguais ao nativo. |
| **Builds oficiais e múltiplos canais** | **`Snap` (`snapd`)** | Instalação local rápida (`2,8–6,9 s`), `27` canais e melhor render no Blender (`643 ms`), porém atraso em `strict` (`434–444 ms`) e `3,52 GiB`. |

---

## 6. Entregas do Repositório por Semana

| Sem. | Tema | Arquivos no repositório |
| :---: | :--- | :--- |
| **1** | Proposta e fundamentação | [Slides (PDF)](./semana-01/slides/apresentacao-semana-01.pdf) · [Escopo e plano](./semana-01/escopo-e-plano.md) · [Fundamentação](./semana-01/fundamentacao-e-fontes.md) |
| **2** | Revisão conceitual | [Relatório parcial 1](./semana-02/relatorio-parcial-01.md) · [Slides c/ referências (PDF)](./semana-02/slides/apresentacao-semana-02-com-referencias.pdf) |
| **3** | Demonstrações práticas | Apresentação oral em sala das 4 famílias *(evidências consolidadas na Semana 4)* |
| **4** | Comparação controlada (`hello`) | [Relatório parcial 2 (PDF)](./semana-04/relatorio-parcial-02.pdf) · [Slides (PDF)](./semana-04/slides/apresentacao-semana-04.pdf) · [Script](./semana-04/evidencias/executar_experimentos.py) · [JSON](./semana-04/evidencias/resumo-comparativo.json) |
| **5** | Resultados finais (3 apps) | [Relatório final (PDF)](./semana-05/relatorio-final.pdf) · [Análise (MD)](./semana-05/resultados-e-comparacao.md) · [Slides PDF](./semana-05/slides/apresentacao-semana-05.pdf) · [PPTX](./semana-05/slides/apresentacao-semana-05.pptx) · [Script](./semana-05/evidencias/executar_testes_finais.py) · [JSON](./semana-05/evidencias/resumo-testes-finais.json) |

---

## 7. Referências

1. [Debian Policy Manual — Pacotes e sistema de arquivos (`APT/dpkg`)](https://www.debian.org/doc/debian-policy/)
2. [FreeBSD Handbook — Installing Applications: Packages and Ports](https://docs.freebsd.org/en/books/handbook/ports/) e [FreeBSD Ports Collection](https://cgit.freebsd.org/ports/)
3. DOLSTRA, E.; DE JONGE, M.; VISSER, E. [Nix: A Safe and Policy-Free System for Software Deployment (USENIX LISA, 2004)](https://www.usenix.org/conference/lisa-04/nix-safe-and-policy-free-system-software-deployment) e [Nix Reference Manual](https://nix.dev/manual/nix/latest/)
4. [Flatpak Documentation — Under the Hood (`OSTree` e `Bubblewrap`)](https://docs.flatpak.org/en/latest/under-the-hood.html)
5. [Snapcraft Documentation — Snap Confinement (`strict` vs. `classic`)](https://snapcraft.io/docs/explanation/security/snap-confinement/)
6. [Linux `strace(1)`](https://man7.org/linux/man-pages/man1/strace.1.html) e [FreeBSD `truss(1)`](https://man.freebsd.org/cgi/man.cgi?query=truss)
