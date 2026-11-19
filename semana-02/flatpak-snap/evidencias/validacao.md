# Checagem de preparação — Flatpak e Snap

**Estado:** checagem documental concluída; testes de aplicação pendentes.

**Data da consulta registrada:** 5 de novembro de 2026, 09:28:12 UTC (06:28:12 em São Paulo). Preparação executada pelo assistente. O [registro estruturado](./consulta-fontes.json) contém ambiente, URLs e valores obtidos.

## 1. O que foi verificado nesta máquina

Uma consulta por Python com `shutil.which` não encontrou `flatpak`, `snap`, `snapcraft` ou `flatpak-builder` no PATH. Também não havia `DISPLAY` ou `WAYLAND_DISPLAY` na sessão. O ambiente de preparação é o NixOS já registrado na parte de Nix.

Isso descreve a disponibilidade de comandos nesta sessão; não é uma avaliação de compatibilidade das ferramentas com todas as instalações dessa distribuição. Não foram configurados serviços, instaladas aplicações ou modificadas permissões nesta preparação.

## 2. Consulta da receita Flatpak

Foi consultada a revisão `5f9138c4ef35c63c58e54a5558f5661d249412a0` do [manifesto mantido no Flathub](https://github.com/flathub/org.gnome.TextEditor/blob/5f9138c4ef35c63c58e54a5558f5661d249412a0/org.gnome.TextEditor.json). O registro contém:

- ID `org.gnome.TextEditor`.
- Runtime `org.gnome.Platform`, versão `51`, e SDK `org.gnome.Sdk`.
- Fonte do editor `51.0`, além de módulos adicionais.
- Permissões declaradas, incluindo `--filesystem=host` e acessos gráficos.

**O que isso demonstra:** quais componentes e acessos essa receita declara.

**O que ainda depende de instalação e teste:** versão efetivamente obtida, commit instalado, overrides locais, autorizações por portais, funcionamento gráfico e acessos realmente permitidos. O número da versão do runtime não substitui a versão da aplicação.

## 3. Consulta do catálogo Snap

A API pública da Snap Store foi consultada com campos explícitos para base, confinamento, versão e revisão. No canal `latest/stable`, arquitetura `amd64`, foram obtidos:

- Editor `48.3`.
- Revisão do pacote `53`.
- Base `core24`.
- Metadado de confinamento `strict`.

Fonte: [consulta à API da loja](https://api.snapcraft.io/v2/snaps/info/gnome-text-editor?fields=base,confinement,version,revision,download). A [página do pacote](https://snapcraft.io/gnome-text-editor) apresenta Ken VanDine como publicador.

**O que isso demonstra:** os metadados anunciados pelo catálogo para esse canal e arquitetura no momento da consulta.

**O que ainda depende de instalação e teste:** revisão instalada, interfaces conectadas, suporte de confinamento do hospedeiro, funcionamento gráfico e bloqueio efetivo de acesso a documentos. Um metadado `strict` não substitui a verificação dessas condições.

O tutorial oficial de empacotamento GTK4 usa uma receita didática com `core22` e fonte `42.2`. Ele explica o procedimento; não comprova a receita da revisão 53 da loja.

## 4. Procedimento de comparação preparado

O [guia do integrante 4](../README.md) utiliza o mesmo GNOME Text Editor e o mesmo conteúdo de `comparacao.txt` da parte de Nix. Ele prevê:

1. Registrar instalação, dependências, versões e permissões.
2. Abrir, editar, salvar e reabrir o documento em cada formato.
3. No Flatpak, testar leitura e escrita diretas com acesso temporariamente limitado à pasta de teste.
4. No Snap, relacionar leitura direta à conexão da interface `home`, quando declarada, preservando seu estado inicial ao terminar.
5. Distinguir autorizações por portais de acesso direto ao caminho do arquivo.

Os comandos foram preparados a partir da documentação. Os 13 blocos Bash do guia passaram pela checagem de sintaxe com `bash -n`; os links locais foram conferidos e o arquivo de entrada coincide com o utilizado na parte de Nix. Esses resultados estão no registro estruturado. A checagem de sintaxe detecta erros de escrita; não valida a execução pelas ferramentas nem confirma os resultados esperados.

## 5. Pendências para o piloto

- [ ] Preparar uma máquina Linux com as duas ferramentas e suporte de confinamento registrado.
- [ ] Registrar versões e componentes realmente instalados.
- [ ] Consultar permissões, overrides, autorizações por portais e interfaces.
- [ ] Executar a tarefa gráfica e guardar capturas.
- [ ] Executar os testes de acesso direto e registrar saídas e códigos de retorno.
- [ ] Conferir a restauração do estado inicial das interfaces após o experimento.
- [ ] Se houver atualização entre versões, registrar versões anteriores e posteriores e repetir a tarefa.

Construir pacotes próprios do editor e publicá-los em lojas não foi executado. O relatório explica o fluxo de empacotamento; a demonstração principal utiliza os pacotes já distribuídos.

**Limite da conclusão atual:** há uma comparação fundamentada e um procedimento preparado. Ainda não há resultados de instalação, execução, confinamento, atualização ou desempenho de Flatpak e Snap neste ambiente. Diferenças de versão entre as fontes consultadas também impedem tratar os formatos como a única variável de uma comparação de desempenho.
