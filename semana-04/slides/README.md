# Apresentação da semana 4

- [PowerPoint editável](./apresentacao-semana-04.pptx): texto, diagramas e notas de fala.
- [PDF para projeção](./apresentacao-semana-04.pdf): versão vetorial com fontes incorporadas.
- [Apresentação HTML offline](./apresentacao-semana-04.html): setas para navegar, `F` para tela cheia e `N` para notas.
- [Roteiro de fala](./roteiro-de-fala.md): responsáveis, tempos sugeridos, explicações e fontes.
- [Relatório parcial 2](../relatorio-parcial-02.md).
- [Protocolo, validade experimental e resultados](../protocolo-e-resultados.md).
- [Reserva para apresentação futura (bateria multi-pacotes)](../reserva-apresentacao-futura/README.md).

São **12 slides principais (incluindo o Slide 5 em branco reservado para o vídeo) e 1 de apoio**, com cerca de **10 minutos e 15 segundos** (incluindo o espaço para o vídeo), a confirmar em ensaio. Os responsáveis aparecem como Integrante 1–4 nas notas; nenhum nome foi inventado.

## Estrutura da apresentação

1. **Slides 1–4 — Metodologia e Validade no NixOS:**
   - Escolha do exemplo único (`GNU hello`, `libc.so.6`, cache local, 3 repetições e `strace -fc` separado).
   - Como os 4 métodos foram testados no mesmo NixOS (`Nix`, `OSTree`, `Bubblewrap` e `SquashFS` 100% nativos no host; `Debian` em container FHS sobre o mesmo kernel `7.3.4`; `FreeBSD Ports` via receita oficial `misc/hello` + build nativo do mesmo fonte).
   - Validade experimental (o que é 100% exato/nativo) e ressalvas honestas (`OverlayFS` no Debian, toolchain Linux/GCC no build e ausência de `AppArmor` no host).
2. **Slide 5 — Slide em branco para o vídeo:**
   - Slide limpo (sem títulos ou caixas) reservado para o apresentador inserir o vídeo demonstrativo dos testes.
3. **Slides 6–12 — Resultados simplificados em comparações diretas entre métodos:**
   - **Slide 6:** Onde o programa fica no disco e como resolve a `libc.so.6` (`FHS` vs. `STAGEDIR` vs. `/nix/store` + `RUNPATH` vs. `OSTree`/`.snap`).
   - **Slide 7:** Quanto tempo e syscalls custa instalar ou preparar (`37,3 ms` Debian vs. `41,3 ms` Nix vs. `37,7 ms` `.snap` vs. `19.840 ms` compilar do fonte).
   - **Slide 8:** Espaço em disco e personalização (`188 KiB` fixos vs. `400,8 → 193,8 KiB` `-51,6%` sem `NLS` vs. `273 KiB` NAR / `36,7 MiB` closure vs. `0 B` extra `OSTree` / `64 KiB` `.snap`).
   - **Slide 9:** Rodar direto no sistema vs. isolado em sandbox (`2,00–3,28 ms` direto vs. `+4,50 ms` no `Bubblewrap`, políticas de bind e exigência de `AppArmor` no Snap).
   - **Slide 10:** Atualização e rollback (`in-place` no Debian/Ports vs. rollback em `34,7 ms` no Nix por `1 symlink + 1 rename` e commits/revisões no Flatpak/Snap).
   - **Slide 11–12:** Quadro síntese das trocas de cada método e encerramento rumo à Semana 5.
4. **Slide 13 — Apoio:**
   - Números completos das 3 repetições e totais de chamadas de sistema (`strace -fc`) para perguntas.

## Regenerar

```bash
uv run --with python-pptx --with Pillow --with reportlab python gerar_apresentacao.py
```
