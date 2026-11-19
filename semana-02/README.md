# Semana 2 — Fundamentação e plano de testes

Os materiais dos quatro integrantes estão integrados no relatório e na apresentação. A entrega explica os mecanismos e organiza os pilotos; as medidas comparativas completas ficam para a etapa posterior.

## Entregas

- [Relatório parcial 1 consolidado](./relatorio-parcial-01.md).
- [PowerPoint editável](./slides/apresentacao-semana-02.pptx).
- [PDF para projeção](./slides/apresentacao-semana-02.pdf).
- [Apresentação HTML offline](./slides/apresentacao-semana-02.html).
- [Roteiro de fala e divisão dos slides](./slides/roteiro-de-fala.md).
- [Plano de testes atualizado](./plano-de-testes.md).

São 15 slides principais e 2 de apoio, com cerca de 11 minutos e 30 segundos de fala. O visual e os logos são os da semana 1, com conteúdo principal em 26–30 pt. A duração deve ser confirmada em ensaio.

## Material dos integrantes

- **Integrante 1 — Debian:** [PDF fornecido](./materiais-integrantes/debian-apt-dpkg.pdf); conteúdo consolidado na seção 3.1 do relatório. Piloto: tmux, dependências e arquivos.
- **Integrante 2 — FreeBSD Ports:** [PDF fornecido](./materiais-integrantes/freebsd-ports.pdf); conteúdo consolidado na seção 3.2. Piloto: misc/hello, NLS e construção.
- **Integrante 3 — Nix:** [relatório, procedimento e evidências](./nix/README.md). Piloto: seleção em dois perfis e recuperação de geração.
- **Integrante 4 — Flatpak e Snap:** [relatório, procedimento e checagem documental](./flatpak-snap/README.md). Piloto planejado: editor e acesso a arquivos.

A [divisão original das perguntas](./divisao-do-grupo.md) continua disponível. Cada parte deve ser revisada por outro integrante, usando os critérios comuns: arquivos, dependências, atualizações/recuperação, proteção e recursos.

## O que já foi verificado

- Debian e Ports: materiais recebidos e fundamentação incorporada; os PDFs não comprovam execução dos pilotos.
- Nix: validação pelo terminal no ambiente de preparação, com limites registrados; etapa gráfica e outro computador pendentes.
- Flatpak/Snap: consulta a documentação, receita e catálogo; testes de aplicação pendentes.
- Não há benchmark comparativo concluído.

## O que fazer antes da demonstração

1. Registrar ambientes e versões e executar os pilotos de Debian e Ports.
2. Concluir a tarefa gráfica de Nix e pedir a um colega que repita as instruções em outra máquina.
3. Executar os procedimentos de Flatpak/Snap numa máquina adequada e registrar permissões e suporte de confinamento.
4. Verificar a viabilidade da tarefa comum do editor. Preservar tmux e hello como ilustrações; comparar tempos somente com tarefas e condições justificadas.
5. Guardar comandos, saídas reais, capturas e uma explicação do que cada resultado demonstra.
6. Ensaiar a apresentação e ajustar a fala ao tempo disponível.

Os slides atuais relatam o estado acima. Depois dos pilotos, atualizar relatório, plano e apresentação com os resultados efetivamente observados.

## Edição e fontes

- [Como editar e regenerar os slides](./slides/README.md).
- [Fundamentação da semana 1](../semana-01/fundamentacao-e-fontes.md).
- [Escopo e cronograma](../semana-01/escopo-e-plano.md).
