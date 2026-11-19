# Apresentação da semana 2

- [PowerPoint editável](./apresentacao-semana-02.pptx): texto, diagramas e notas de fala.
- [PDF para projeção](./apresentacao-semana-02.pdf): versão com fontes incorporadas.
- [PDF enviado pelo grupo com cinco referências](./apresentacao-semana-02-com-referencias.pdf): preserva as 15 páginas e a ordem de `document(4).pdf` e acrescenta dois slides bibliográficos com links clicáveis. É uma variante do PDF fornecido, que tem sequência diferente da apresentação gerada abaixo.
- [Apresentação HTML offline](./apresentacao-semana-02.html): setas para navegar, F para tela cheia e N para notas.
- [Roteiro de fala](./roteiro-de-fala.md): responsáveis, tempos sugeridos, explicações e fontes.
- [Relatório parcial consolidado](../relatorio-parcial-01.md).

São **15 slides principais e 2 de apoio**, com cerca de **11 minutos e 30 segundos** de fala, a confirmar em ensaio. Os responsáveis aparecem como Integrante 1–4 nas notas; nenhum nome foi inventado. Os slides de apoio ficam após o encerramento e servem para perguntas.

## Conteúdo

A apresentação integra os materiais de Debian e FreeBSD enviados pelo grupo e a preparação de Nix, Flatpak e Snap. O foco é Sistemas Operacionais: arquivos, dependências, recuperação, proteção e recursos. Comandos secundários e fontes ficam nas notas.

O slide 11 apresenta o plano de quatro VMs: Debian com APT/dpkg, FreeBSD com Ports, Debian com Nix e Debian com Flatpak/Snap em snapshots separados. As notas explicam que se trata de preparação planejada, com hardware virtual equivalente e uma VM em teste por vez.

Os slides distinguem o estado das evidências:

- Debian e Ports: exemplos didáticos preparados, ainda sem execução comprovada nos materiais recebidos.
- Nix: validação pelo terminal no ambiente de preparação; janela e outro computador pendentes.
- Flatpak e Snap: checagem documental; execução pendente.
- Sem benchmark comparativo concluído.

`tmux` e `hello` ilustram os mecanismos de Debian e Ports. O editor de texto permanece como tarefa comum proposta, sujeita à validação em cada ambiente. Os tempos de programas diferentes não são tratados como um ranking.

## Visual e legibilidade

O gerador reutiliza os **mesmos três fundos da semana 1**, preservando os logos UFG/INF. Não acrescenta código ou nome da disciplina, identificação “grupo de 4” nem “projeto de 5 semanas” à capa ou aos rodapés.

Títulos usam 36–48 pt; conteúdo principal, 26–30 pt. Somente a numeração de página usa 14 pt. Os textos foram reduzidos para manter a leitura em sala de aula, sem reduzir a fonte para caber.

## Regenerar

```bash
uv run --with python-pptx --with Pillow --with reportlab python gerar_apresentacao.py
```

O [gerador](./gerar_apresentacao.py) contém conteúdo e diagramação e produz PowerPoint, PDF, HTML e roteiro a partir da mesma estrutura. Requer Fontconfig e Liberation Sans para medir e incorporar a fonte no PDF; o PowerPoint indica Arial, de métricas compatíveis.

Para regenerar, manter a estrutura do projeto: os [fundos originais](../../semana-01/slides/assets/README.md) são lidos diretamente da semana 1. Os três formatos exportados incorporam os fundos e funcionam sem essa pasta.
