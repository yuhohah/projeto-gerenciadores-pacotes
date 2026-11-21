# Gerenciadores de Pacotes em Unix/Linux

**Disciplina:** Sistemas Operacionais (`INF0336`) — Instituto de Informática (UFG)

## Participantes

> Espaço reservado para os nomes dos integrantes do grupo:

- **Integrante 1:** `Luan de Paula Mota - 202003588`
- **Integrante 2:** `Joao Carlos - 202401792`
- **Integrante 3:** `Gabrielle Siqueira - 202200511`
- **Integrante 4:** `Lya Ribeiro - 202107857`

---

## Sobre o Trabalho

Este projeto compara **cinco gerenciadores de pacotes** de sistemas Unix e Linux para entender, na prática, como cada modelo instala, atualiza, organiza, protege e executa programas no computador:

| Família | Gerenciador avaliado | Ideia principal |
| :--- | :--- | :--- |
| **Binários tradicionais** | **Debian (`APT/dpkg`)** | Instala pacotes prontos nas pastas padrão do sistema, compartilhando bibliotecas entre todos os programas. |
| **Código-fonte** | **FreeBSD `Ports`** | Baixa o código-fonte e compila cada programa no computador do usuário, permitindo escolher quais recursos incluir. |
| **Funcional e imutável** | **`Nix`** | Guarda cada programa e suas bibliotecas em pastas separadas com identificador próprio, permitindo voltar versões quase instantaneamente. |
| **Isolados (sandbox)** | **`Flatpak`** | Roda aplicativos dentro de uma caixa isolada usando bases gráficas compartilhadas e controle de versões. |
| **Isolados (sandbox)** | **`Snap` (`snapd`)** | Distribui programas como arquivos compactados e isolados (modo `strict`) ou livres (modo `classic`). |

### Como os testes finais foram feitos

Para fazer uma comparação justa, rodamos todos os testes no **mesmo computador** (`AMD Ryzen 5 2600`, 6 núcleos / 12 threads, 15 GiB de RAM) comparando **cada aplicativo contra si mesmo nos 5 gerenciadores**, com 3 repetições por tarefa:

1. **`GNOME Text Editor` (`48.3`)** — aplicativo leve–médio (abrir e consultar a versão e bibliotecas gráficas).
2. **`VLC Media Player` (`3.0.24`)** — aplicativo médio–pesado (converter um áudio `WAV` para `OGG` pelo terminal).
3. **`Blender` (`4.3.x` / `4.5 LTS`)** — aplicativo muito pesado (renderizar uma cena 3D em imagem `PNG` usando 4 threads na CPU).

- **Debian, Nix, Flatpak e Snap** rodaram no Linux, com o serviço oficial do Snap (`snapd`) ativo.
- **FreeBSD `Ports`** rodou em uma **máquina virtual com FreeBSD `14.4`** no mesmo computador usando diretamente a CPU física (QEMU/KVM): instalamos antes as dependências prontas via `pkg`, compilamos cada um dos 3 programas a partir do código-fonte pelo `/usr/ports` (`make build` + `make install`) e executamos as mesmas 3 tarefas dentro do FreeBSD.

### Principais conclusões

- **Não existe um único "melhor" gerenciador:** cada modelo prioriza um objetivo diferente.
- **Debian (`APT/dpkg`):** menor uso de disco (`180 MiB` → `1,09 GiB`) e instalação simples, mas sem isolamento e sem volta rápida de versão.
- **FreeBSD `Ports`:** máxima personalização (`72` opções no VLC; `57` no Blender), porém compilar apps grandes exige tempo (`34 min 12 s` no Blender).
- **`Nix`:** ativação e volta de versão quase instantâneas (`~36 ms` e `~29 ms`), convivência de versões sem conflito e `48,7%` de reaproveitamento de disco na mesma revisão.
- **`Flatpak`:** melhor equilíbrio entre **segurança e velocidade** — manteve isolamento ativo nos 3 aplicativos com execução muito rápida (`36,8 ms`, `192,5 ms` e `1.337 ms`).
- **`Snap` (`snapd`):** demora bem mais em tarefas curtas no modo isolado (`strict`) — `434 ms` no Editor e `444 ms` no VLC — por montar o ambiente isolado a cada abertura; já no Blender (modo `classic`, sem isolamento) foi o mais rápido (`643 ms`) por entregar o executável oficial otimizado.
- **Atualizações entre gerenciadores:** não é possível atualizar um aplicativo instalado por um gerenciador usando outro, pois cada um mantém seu próprio registro, suas pastas e seu formato de execução.

---

## Resumo das Entregas por Semana

| Semana | Tema | Principais entregas |
| :---: | :--- | :--- |
| **Semana 1** | Proposta e fundamentação | Apresentação oral, slides (PDF), roteiro de fala, escopo e fundamentação |
| **Semana 2** | Revisão conceitual e plano de testes | Relatório parcial 1, plano de testes e slides com referências (PDF) |
| **Semana 3** | Demonstrações práticas | Apresentação oral 2 em sala demonstrando as quatro famílias *(consolidada na Semana 4)* |
| **Semana 4** | Metodologia e comparação controlada (`GNU hello`) | Relatório parcial 2 (PDF/LaTeX/Markdown), protocolo, slides (PDF), vídeo demonstrativo e evidências |
| **Semana 5** | Resultados finais (`Editor`, `VLC` e `Blender`) | Relatório final (PDF/LaTeX), análise comparativa (Markdown), apresentação final (PDF/PPTX/HTML), roteiro e evidências |

---

## Arquivos de Cada Semana

### Semana 1 — Proposta e Fundamentação
- **Apresentação (PDF):** [`apresentacao-semana-01.pdf`](./semana-01/slides/apresentacao-semana-01.pdf) *(10 slides principais + 1 de apoio)*
- **Fundamentação e fontes:** [`fundamentacao-e-fontes.md`](./semana-01/fundamentacao-e-fontes.md)
- **Slides e detalhes:** [`slides`](./semana-01/slides/apresentacao-semana-01.pdf)

### Semana 2 — Relatório Parcial  e Plano de Testes
- **Relatório parcial :** [`relatorio-parcial-01.md`](./semana-02/relatorio-parcial-01.md)
- **Plano de testes:** [`plano-de-testes.md`](./semana-02/plano-de-testes.md)
- **Apresentação (PDF com referências):** [`apresentacao-semana-02-com-referencias.pdf`](./semana-02/slides/apresentacao-semana-02-com-referencias.pdf) *(15 slides principais + 2 de referências)*

### Semana 3 — Apresentação Oral 2 (Demonstrações Práticas)
- **Entrega:** apresentação oral em sala com demonstrações das quatro famílias de gerenciadores. Os testes automatizados e o vídeo de demonstração foram consolidados na pasta da Semana 4.

### Semana 4 — Relatório Parcial 2, Validade e Comparação Controlada (`GNU hello`)
- **Relatório parcial :** [`relatorio-parcial-02.pdf`](./semana-04/relatorio-parcial-02.pdf) 
- **Protocolo e resultados:** [`protocolo-e-resultados.md`](./semana-04/protocolo-e-resultados.md)
- **Apresentação (PDF):** [`apresentacao-semana-04.pdf`](./semana-04/slides/apresentacao-semana-04.pdf) *(12 slides principais + 1 de apoio)*
- **Scripts e evidências:** [`executar_experimentos.py`](./semana-04/evidencias/executar_experimentos.py) · [`resumo-comparativo.json`](./semana-04/evidencias/resumo-comparativo.json)

### Semana 5 — Relatório Final, Slides Finais e Comparação de 3 Aplicativos
- **Relatório final:** [`relatorio-final.pdf`](./semana-05/relatorio-final.pdf)
- **Resultados e análise comparativa (Markdown):** [`resultados-e-comparacao.md`](./semana-05/resultados-e-comparacao.md)
- **Apresentação final:** [`apresentacao-semana-05.pdf`](./semana-05/slides/apresentacao-semana-05.pdf) · [`apresentacao-semana-05.pptx`](./semana-05/slides/apresentacao-semana-05.pptx)
- **Roteiro dos testes, scripts e evidências:**  [`executar_testes_finais.py`](./semana-05/evidencias/executar_testes_finais.py) · [`resumo-testes-finais.json`](./semana-05/evidencias/resumo-testes-finais.json) · [`semana-05/README.md`](./semana-05/README.md)

---

## Como Reproduzir os Materiais
- **Rodar a bateria automatizada de testes da Semana 5:**
  ```bash
  python3 semana-05/evidencias/executar_testes_finais.py --dry-run
  ```
