# Gerenciadores de pacotes em Unix/Linux

Projeto comparativo sob a ótica de **Sistemas Operacionais** sobre organização de arquivos (VFS), resolução de dependências e vinculação dinâmica (`ELF`/`ld.so`), atualizações e recuperação atômica, proteção/isolamento e uso de recursos.

O recorte atual contempla cinco representantes em quatro famílias: **Debian (`APT/dpkg`)**, **FreeBSD `Ports`**, **`Nix`**, **`Flatpak` (`OSTree` + `Bubblewrap`)** e **`Snap` (`SquashFS` + `AppArmor`/`cgroups`)**.

## Estrutura e entregas por semana

### Semana 1 — Proposta e fundamentação

- [PDF para projeção](./semana-01/slides/apresentacao-semana-01.pdf): **10 slides principais + 1 de apoio** no padrão visual UFG/INF.
- [Roteiro de fala](./semana-01/slides/roteiro-de-fala.md): divisão entre os quatro integrantes e tempos sugeridos.
- [Fundamentação e fontes](./semana-01/fundamentacao-e-fontes.md): conceitos de SO, cuidados de interpretação e bibliografia.
- [Escopo e plano](./semana-01/escopo-e-plano.md): critérios comuns de comparação, exemplos planejados e cronograma.
- [Script gerador dos slides](./semana-01/slides/gerar_apresentacao.py) e [detalhes da apresentação](./semana-01/slides/README.md).

### Semana 2 — Relatório parcial 1 e plano de testes

- [Relatório parcial 1 consolidado](./semana-02/relatorio-parcial-01.md): integração conceitual das quatro famílias.
- [Plano de testes](./semana-02/plano-de-testes.md): preparação dos pilotos e critérios de validação.
- [PDF para projeção (com referências)](./semana-02/slides/apresentacao-semana-02-com-referencias.pdf): **15 slides principais + 2 slides bibliográficos** com links clicáveis.
- [Script gerador dos slides](./semana-02/slides/gerar_apresentacao.py).

### Semana 4 — Metodologia no NixOS, validade e comparação controlada (`GNU hello`)

- [Relatório parcial 2 consolidado](./semana-04/relatorio-parcial-02.md): explicação da execução das quatro famílias a partir de um único hospedeiro **NixOS (`Linux 7.3.4`)**, análise de validade experimental e resultados comparativos sobre o exemplo único transversal **`GNU hello`** (`libc.so.6` + 46 catálogos `NLS`).
- [Protocolo e resultados experimentais](./semana-04/protocolo-e-resultados.md): tabelas com as 3 repetições individuais, perfil de chamadas de sistema (`strace -fc`) e matriz de validade interna vs. limites metodológicos.
- [PDF para projeção](./semana-04/slides/apresentacao-semana-04.pdf): **12 slides principais + 1 de apoio** (13 slides no total):
  - **Slides 1–4:** escolha do `GNU hello`, arquitetura dos testes no NixOS (`Nix`, `OSTree`, `Bubblewrap` e `SquashFS` nativos no host; `Debian` em container FHS no mesmo kernel; `FreeBSD Ports` via receita `misc/hello` + build controlado do mesmo tarball) e limites honestos (`OverlayFS`, toolchain Linux/GCC e ausência de `AppArmor` no kernel para o Snap).
  - **Slide 5:** slide em branco reservado para inserção do vídeo demonstrativo.
  - **Slides 6–12:** comparações diretas entre métodos (layout em disco/`RUNPATH`, instalação vs. compilação, espaço/`NLS`, sandbox vs. execução direta, atualização/rollback e síntese).
  - **Slide 13 (apoio):** números completos das repetições e totais de `strace -fc`.
- [Vídeo demonstrativo em terminal (`demo-execucao-hello.mp4`)](./semana-04/slides/demo-execucao-hello.mp4): gravação (`1080p30` H.264, ~57,6 s) produzida para o Slide 5 a partir de [`demo_video_hello.py`](./semana-04/evidencias/demo_video_hello.py).
- [Roteiro de fala e divisão dos slides](./semana-04/slides/roteiro-de-fala.md) e [detalhes dos slides](./semana-04/slides/README.md).
- [Documentação da Semana 4](./semana-04/README.md), [script da bateria experimental](./semana-04/evidencias/executar_experimentos.py) e [resumo comparativo (`JSON`)](./semana-04/evidencias/resumo-comparativo.json).
- [Reserva para apresentação futura](./semana-04/reserva-apresentacao-futura/README.md): preserva o material e os slides anteriores da bateria ampliada com três pacotes (`hello`, `tmux` e `gnome-text-editor`).

## Execução dos scripts

### Demonstração visual em terminal (`GNU hello`)

```bash
python3 semana-04/evidencias/demo_video_hello.py
```

Opções disponíveis em [`demo_video_hello.py`](./semana-04/evidencias/demo_video_hello.py):
- `--pause`: aguarda `Enter` entre cada bloco de comandos.
- `--skip-build`: pula a etapa de compilação do tarball `GNU hello` para uma execução rápida.

### Regeneração dos slides

Dentro da pasta `slides/` desejada (por exemplo, [`semana-04/slides/`](./semana-04/slides/README.md)):

```bash
uv run --with python-pptx --with Pillow --with reportlab python gerar_apresentacao.py
```

O script lê os [fundos originais da UFG/INF](./semana-01/slides/assets/README.md) em [`./semana-01/slides/assets/`](./semana-01/slides/assets/) e gera PowerPoint (`.pptx`), PDF vetorial (`.pdf`), apresentação offline (`.html`) e roteiro (`.md`). Requer `fontconfig` com `Liberation Sans` instalada (no NixOS, pode ser necessário disponibilizar a `zlib` do sistema em `LD_LIBRARY_PATH` para o `Pillow`). Os PDFs versionados no repositório já incorporam fontes e imagens de fundo de forma independente.
