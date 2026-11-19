# Slides — apresentação oral da semana 01

- [PowerPoint editável](./apresentacao-semana-01.pptx): apresentação com notas de fala.
- [PDF](./apresentacao-semana-01.pdf): cópia com fontes incorporadas para apresentar e compartilhar.
- [Apresentação no navegador](./apresentacao-semana-01.html): funciona offline; use as setas para navegar, F para tela cheia e N para notas.
- [Roteiro de fala](./roteiro-de-fala.md): divisão entre quatro pessoas e tempo sugerido por slide.

São **10 slides principais e 1 slide de apoio**. O tempo estimado é de oito minutos, a confirmar em ensaio. Os responsáveis estão identificados como Pessoa 1–4 nas notas; substitua pelos nomes do grupo quando necessário.

A versão para projeção usa títulos de **36 a 48 pontos** e conteúdo principal de **24 a 30 pontos**. Apenas a numeração das páginas usa fonte menor. O slide 9 apresenta exclusivamente as entregas previstas das semanas 1 a 5, com descrições curtas. O antigo slide 12 de referências foi removido; as fontes continuam disponíveis no roteiro de fala.

O visual segue o PDF **Teoria dos Grafos - Emparelhamento** fornecido: mesmos fundos e logos da UFG e do INF, extraídos do arquivo original. A identificação do grupo/duração na capa e o rodapé com código e nome da disciplina foram removidos. O texto do conteúdo permanece editável no PowerPoint; os fundos estão incorporados nos arquivos.

O conteúdo apresenta a proposta do projeto e não resultados de experimentos. O recorte atual inclui **apenas cinco representantes em quatro famílias**:

- **Binários tradicionais mutáveis (FHS):** Debian, com APT/dpkg.
- **Baseados em código-fonte (Source/Ports):** FreeBSD Ports.
- **Funcionais e imutáveis:** Nix.
- **Containerizados / sandboxed:** Flatpak (OSTree + Bubblewrap) e Snap (SquashFS + AppArmor/cgroups).

O título usa Unix/Linux para abranger FreeBSD. A parte prática contempla exemplos das quatro famílias; FreeBSD exige ambiente próprio, como uma máquina virtual. Compilação, instalação de binários e ativação de perfis serão tratadas como operações distintas.

## Regenerar

O [script de geração](./gerar_apresentacao.py) contém o conteúdo e a diagramação. Ele produz todos os formatos com a mesma fonte de dados.

```sh
uv run --with python-pptx --with Pillow --with reportlab python gerar_apresentacao.py
```

O script requer Fontconfig e uma instalação de Liberation Sans para medir e incorporar fontes no PDF. No PowerPoint, a fonte indicada é Arial, de métricas compatíveis.

Os três fundos em [assets/](./assets/) precisam acompanhar o script para regenerar os arquivos. As apresentações exportadas em PowerPoint, PDF e HTML já incorporam os fundos e funcionam sem essa pasta.
