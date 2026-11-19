# Validação do exemplo Nix

**Estado:** validação pelo terminal concluída. A tarefa gráfica e a repetição em outra máquina continuam pendentes.

**Data:** 5 de novembro de 2026; início da segunda validação às 03:37:36 UTC (00:37:36 em São Paulo). Execução automatizada pelo assistente no ambiente de preparação; não corresponde a uma apresentação ou execução pelos integrantes.

## Ambiente registrado

- Nix: `2.34.9`.
- SO: NixOS `26.11.20261023.3ec6363`; kernel Linux `7.3.0`.
- Arquitetura: `x86_64-linux`.
- Revisão Nixpkgs: `3ec636362e1816bc2f0888fa0fa2c69f1bc9e504`.
- GNOME Text Editor: `50.1`.
- Sem `DISPLAY` ou `WAYLAND_DISPLAY` na sessão utilizada.
- Comandos `nix-command` e flakes disponíveis na configuração do ambiente.

## Procedimentos e resultados observados

1. **Avaliação da configuração:** `nix flake check --no-build --no-update-lock-file` terminou com código zero. Essa checagem avaliou a flake; não verificou a interface gráfica.
2. **Obtenção do editor:** `nix build .#editor --no-update-lock-file --no-link --print-out-paths` disponibilizou o pacote no store. O log registrou obtenção de binários do cache, sem compilação local do editor.
3. **Ambiente declarado:** `nix develop --command gnome-text-editor --version`, com o lock preservado, informou `50.1`. A consulta ao executável retornou um caminho no store.
4. **Perfis A e B:** ambos foram criados em um diretório temporário, selecionaram o mesmo executável e responderam à consulta de versão.
5. **Remoção apenas em A:** o executável deixou de existir em `perfil-a/bin`; a consulta pelo caminho de B continuou funcionando.
6. **Gerações e retorno:** o histórico registrou inclusão e remoção do editor. `nix profile rollback --profile .../perfil-a` retornou da geração 2 para a 1, recuperando o executável em A.
7. **Documento fora do perfil:** o validador Python copiou `comparacao.txt` para `resultado.txt` e alterou a última linha. Após o rollback, ela continuou como `Resultado: concluído`. Essa edição foi feita por código, não pela janela do editor.
8. **Cópia em outra pasta:** `flake.nix`, `flake.lock` e `comparacao.txt` foram copiados para outro diretório temporário. O comando de obtenção selecionou o mesmo caminho do editor. Isso verifica a cópia na mesma máquina e com o mesmo store, não uma instalação independente em outra máquina.

Os perfis temporários e a cópia de trabalho foram removidos após o registro. Nenhuma operação foi dirigida ao perfil padrão do usuário; os componentes obtidos permanecem sujeitos à administração normal do store.

### Caminho obtido

```text
/nix/store/94r4v2l4r5lzmik62h7mnfi7bwvqnmfz-gnome-text-editor-50.1
```

### Armazenamento: interpretar as medidas corretamente

Antes da obtenção, a simulação informou **4 caminhos**, **2,1 MiB de download** e **7,9 MiB descompactados** adicionais nas condições daquela máquina. A consulta do fechamento do pacote — editor e dependências transitivas — informou **957,2 MiB**.

Esses números respondem a perguntas diferentes: o download adicional foi pequeno porque grande parte das dependências já estava presente. O fechamento inclui componentes compartilháveis e não representa o crescimento exclusivo do disco causado por esta instalação. Não foram medidos tempo, CPU, RAM nem crescimento líquido do disco. Os valores não fundamentam um ranking contra os outros gerenciadores.

## Ajuste do procedimento de verificação

A primeira validação executou os comandos com sucesso, mas uma asserção comparou os caminhos dos perfis completos e falhou. Essa comparação era inadequada: perfis podem conter metadados distintos mesmo selecionando o mesmo executável. A segunda validação comparou os destinos resolvidos de `perfil-a/bin/gnome-text-editor` e `perfil-b/bin/gnome-text-editor`; eles coincidiram. O log preserva ambas as passagens. A falha inicial foi do critério de verificação, não da execução do editor.

## Pendências para o integrante

- [ ] Abrir o editor por `nix develop`, editar e salvar o arquivo pela janela.
- [ ] Reabrir `resultado.txt` e guardar uma captura do resultado e da versão.
- [ ] Pedir a outro integrante que repita a configuração em outra máquina compatível e registre as dificuldades.
- [ ] Para uma comparação futura de versões ou atualizações, escolher duas revisões que forneçam versões diferentes e repetir a tarefa em ambas.

**Alcance da evidência:** foram demonstradas seleção independente de perfis, compartilhamento do executável e recuperação de uma geração após remoção do pacote. Não foram demonstrados confinamento de acesso a arquivos, duas versões diferentes do editor, atualização entre versões ou identidade binária entre construções independentes.

## Arquivos do registro

- [Comandos e saídas reais](./comandos.txt).
- [Resumo estruturado da segunda validação](./resultado.json).
- [Procedimento para repetir e roteiro de fala](../README.md).
