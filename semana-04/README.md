# Semana 4 — Relatório parcial 2, metodologia no NixOS, validade e comparação controlada (`GNU hello`)

Esta pasta reúne as entregas da **Semana 4**, focadas em:
1. **Explicar detalhadamente como os testes das quatro famílias são realizados a partir de um único hospedeiro `NixOS` (`Linux 7.3.4`) e qual é a validade (e o limite) de cada medição**;
2. **Realizar a comparação experimental controlada utilizando um único exemplo transversal (`GNU hello`)** em todas as quatro abordagens (`Debian APT/dpkg`, `FreeBSD Ports` / build do fonte, `Nix` e mecanismos `OSTree` / `Bubblewrap` / `SquashFS` de `Flatpak` e `Snap`);
3. **Preservar os resultados adicionais já coletados** (com `tmux` e `gnome-text-editor`) em [`./reserva-apresentacao-futura/`](./reserva-apresentacao-futura/README.md) para uso na apresentação futura.

## Entregas principais desta apresentação (Exemplo único: `GNU hello`)

- [Relatório parcial 2](./relatorio-parcial-02.md): metodologia de execução no NixOS, análise de validade experimental e comparação das quatro famílias sobre o `GNU hello`.
- [Protocolo, validade e resultados experimentais](./protocolo-e-resultados.md): tabelas com as 3 repetições individuais, perfil de syscalls (`strace -fc`) e matriz de validade.
- [PowerPoint editável](./slides/apresentacao-semana-04.pptx): 12 slides principais (com slide 5 em branco para o vídeo) + 1 de apoio no padrão visual UFG/INF.
- [PDF para projeção](./slides/apresentacao-semana-04.pdf): versão vetorial com fontes incorporadas.
- [Apresentação HTML offline](./slides/apresentacao-semana-04.html): apresentação navegável no navegador (`F` para tela cheia, `N` para notas).
- [Roteiro de fala e divisão dos slides](./slides/roteiro-de-fala.md): falas sugeridas, tempos e divisão entre Integrantes 1 a 4.

## Reserva para apresentação futura (Bateria multi-pacotes)

- [Pasta de reserva da bateria completa (`hello`, `tmux`, `gnome-text-editor`)](./reserva-apresentacao-futura/README.md): contém o relatório, protocolo, slides (`.pptx`, `.pdf`, `.html`) e roteiro com todos os três pacotes já medidos.

## Evidências brutas e scripts

- [Complemento experimental do exemplo único `GNU hello`](./evidencias/hello-unico-complemento.json)
- [Ambiente e kernel (`Ryzen 5 2600`, `NixOS 26.11`, Linux `7.3.4`)](./evidencias/ambiente-experimental.json)
- [Debian (`APT` + `dpkg` em container `debian:trixie-slim`)](./evidencias/debian-metricas.json)
- [FreeBSD Ports (`misc/hello`) e compilação controlada (`hello-2.12.3` com e sem `NLS`)](./evidencias/ports-compilacao-metricas.json)
- [Nix (`/nix/store`, perfis, gerações, rollback e `RUNPATH` ELF)](./evidencias/nix-metricas.json)
- [Flatpak (`OSTree` + `Bubblewrap`) e Snap (`SquashFS`)](./evidencias/flatpak-snap-metricas.json)
- [Script reprodutível da bateria experimental](./evidencias/executar_experimentos.py)
