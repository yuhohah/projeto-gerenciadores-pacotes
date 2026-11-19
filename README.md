# Gerenciadores de pacotes em Unix/Linux

Projeto comparativo sobre organização de arquivos, dependências, atualizações, recuperação, proteção e uso de recursos.

O recorte atual contempla apenas **Debian (APT/dpkg), FreeBSD Ports, Nix, Flatpak e Snap**.

## Apresentação da semana 1

- [PowerPoint editável](./semana-01/slides/apresentacao-semana-01.pptx).
- [PDF para projeção](./semana-01/slides/apresentacao-semana-01.pdf).
- [Apresentação no navegador](./semana-01/slides/apresentacao-semana-01.html).
- [Roteiro de fala](./semana-01/slides/roteiro-de-fala.md).

São 11 slides: 10 principais e um de apoio. O modelo mantém os fundos e logos da UFG/INF, com fontes ampliadas para projeção. O slide 9 contém as entregas semanais.

## Entrega da semana 2

- [Relatório parcial consolidado](./semana-02/relatorio-parcial-01.md).
- [PowerPoint editável](./semana-02/slides/apresentacao-semana-02.pptx).
- [PDF para projeção](./semana-02/slides/apresentacao-semana-02.pdf).
- [Apresentação no navegador](./semana-02/slides/apresentacao-semana-02.html).
- [Roteiro de fala](./semana-02/slides/roteiro-de-fala.md).

São 15 slides principais e 2 de apoio. O conteúdo integra os materiais dos quatro integrantes e distingue pesquisa, validação pelo terminal e pilotos pendentes, com o template da semana 1.

## Entrega da semana 4

- [Relatório parcial 2 consolidado](./semana-04/relatorio-parcial-02.md).
- [Protocolo e resultados experimentais](./semana-04/protocolo-e-resultados.md).
- [PowerPoint editável](./semana-04/slides/apresentacao-semana-04.pptx).
- [PDF para projeção](./semana-04/slides/apresentacao-semana-04.pdf).
- [Apresentação no navegador](./semana-04/slides/apresentacao-semana-04.html).
- [Roteiro de fala](./semana-04/slides/roteiro-de-fala.md).
- [Evidências brutas e script de benchmark](./semana-04/evidencias/resumo-comparativo.json).

São 15 slides principais e 2 de apoio. O material apresenta as medições reais, perfis de syscalls (`strace`), inspeção de vinculação dinâmica ELF (`readelf`/`ldd`), deduplicação `OSTree`, confinamento `Bubblewrap` e análise de compressão `SquashFS` para as quatro famílias estudadas.

## Documentação

- [Semana 4 — comparações, medidas e resultados](./semana-04/README.md): relatório parcial 2, protocolo experimental, evidências e slides.
- [Semana 2 — tarefas e entregas](./semana-02/README.md): relatório parcial 1, apresentação e preparação dos testes para os quatro integrantes.
- [Fundamentação e fontes](./semana-01/fundamentacao-e-fontes.md): conceitos, cuidados de interpretação e bibliografia pertinente ao recorte.
- [Escopo e plano](./semana-01/escopo-e-plano.md): critérios de comparação, exemplos práticos e entregas.
- [Edição e geração dos slides](./semana-04/slides/README.md): formatos, dependências e comando de geração.

O conteúdo e a diagramação dos slides estão em [gerar_apresentacao.py](./semana-04/slides/gerar_apresentacao.py). Os [fundos originais](./semana-01/slides/assets/README.md) devem ser mantidos para regenerar os arquivos. PowerPoint, PDF e HTML exportados já incorporam esses fundos.
