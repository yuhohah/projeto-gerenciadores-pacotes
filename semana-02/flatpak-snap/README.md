# Parte do integrante 4 — Flatpak e Snap

## Material e estado da preparação

- [Relatório: respostas às cinco perguntas, comparação e fontes](./relatorio-flatpak-snap.md).
- Este guia: demonstração planejada, roteiro de fala e tópicos para slides.
- [Checagem do ambiente e das fontes](./evidencias/validacao.md): o que foi efetivamente conferido.

**Estado:** pesquisa documental e roteiro preparados. Instalação, execução, empacotamento e testes de permissões ainda não foram realizados. No ambiente de preparação, `flatpak`, `snap`, `flatpak-builder` e `snapcraft` estão ausentes do PATH e não há sessão gráfica.

## A ideia que deve ficar clara

Os dois formatos fornecem uma aplicação com dependências e um ambiente de execução com regras de acesso. Para Sistemas Operacionais, observar **onde ficam os arquivos, quais componentes são compartilhados e o que o processo consegue acessar**.

- **Flatpak:** OSTree administra o conteúdo versionado distribuído; Bubblewrap ajuda a montar o ambiente isolado do processo. O runtime fornece uma base compartilhável de bibliotecas.
- **Snap:** o pacote usa uma imagem SquashFS comprimida e somente leitura. O snapd administra instalação, revisões e execução. AppArmor participa das regras de acesso; cgroups agrupam processos e participam de controles de recursos. Quotas de CPU/RAM dependem de configuração e suporte.

Confinamento depende das permissões efetivas e do hospedeiro. O relatório explica esses componentes sem exigir conhecimento interno deles.

## Exemplo comum e perguntas do teste

**Aplicação:** GNOME Text Editor.

- Flatpak: `org.gnome.TextEditor`, distribuído pelo Flathub.
- Snap: `gnome-text-editor`, distribuído pela Snap Store.

**Tarefa:** abrir [comparacao.txt](./comparacao.txt), trocar a última linha para `Resultado: concluído`, salvar outro arquivo e reabri-lo. A mesma entrada é usada na parte de Nix.

Perguntas a responder com evidências:

1. Quais componentes foram instalados junto com o editor?
2. Quais permissões estão efetivamente concedidas?
3. O processo consegue ler ou gravar na pasta de teste?
4. O que muda quando uma permissão é alterada?
5. Quais versões, revisões e condições limitam a comparação?

## Preparação na máquina da demonstração — pendente

Usar uma máquina Linux com Flatpak e snapd funcionando e uma sessão gráfica. Preferir a mesma máquina para os dois formatos. Registrar SO, arquitetura e versões. Confirmar o suporte de confinamento antes de interpretar bloqueios.

Os comandos seguintes são um **roteiro baseado na documentação**, ainda sem validação neste ambiente. Executar por etapas no ensaio e guardar as saídas reais. A instalação das ferramentas do sistema depende da distribuição; a [configuração do Flatpak](https://flatpak.org/setup/) e a [instalação do snapd](https://snapcraft.io/docs/installing-snapd) orientam essa preparação.

### 1. Instalar o editor e consultar componentes

Flatpak, em instalação do usuário:

```bash
flatpak --version
flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user flathub org.gnome.TextEditor
flatpak info --user org.gnome.TextEditor
flatpak info --user --show-runtime org.gnome.TextEditor
flatpak info --user --show-location org.gnome.TextEditor
flatpak info --user --show-commit org.gnome.TextEditor
flatpak info --user --show-permissions org.gnome.TextEditor
flatpak override --user --show org.gnome.TextEditor
flatpak override --system --show org.gnome.TextEditor
flatpak permission-show org.gnome.TextEditor
```

Guardar a versão, o commit instalado, o runtime e as permissões. O manifesto descreve os acessos pedidos pelo pacote; overrides e autorizações por portais também podem interferir. As consultas são documentadas na [referência do Flatpak](https://docs.flatpak.org/en/latest/flatpak-command-reference.html).

Snap:

```bash
snap version
sudo snap install gnome-text-editor
snap info --verbose gnome-text-editor
snap list
snap connections gnome-text-editor
snap debug confinement
snap debug sandbox-features
```

Registrar versão e revisão do editor, canal, base, componentes compartilhados instalados, interfaces conectadas e o suporte do hospedeiro. Os comandos `debug` podem variar entre versões. Um pacote declarado `strict` ainda precisa de suporte adequado para que essa política seja efetiva. Fontes: [confinamento](https://snapcraft.io/docs/explanation/security/snap-confinement/) e [comandos de diagnóstico](https://forum.snapcraft.io/t/internal-debugging-commands/5341).

### 2. Preparar os mesmos arquivos

No terminal aberto nesta pasta:

```bash
comparacao_dir=$(mktemp -d "$HOME/so-pacotes-integrante4-XXXXXXXX")
cp comparacao.txt "$comparacao_dir/comparacao.txt"
printf 'Pasta do teste: %s\n' "$comparacao_dir"
```

Manter esse terminal aberto para reutilizar a variável. A pasta fica no diretório pessoal, tem nome único e contém apenas os arquivos do experimento.

### 3. Abrir, salvar e reabrir pela janela

Flatpak:

```bash
flatpak run --user org.gnome.TextEditor --standalone "$comparacao_dir/comparacao.txt"
```

Alterar a última linha e usar **Salvar como** para criar `resultado-flatpak.txt` na pasta indicada. Fechar e reabrir:

```bash
flatpak run --user org.gnome.TextEditor --standalone "$comparacao_dir/resultado-flatpak.txt"
```

Snap:

```bash
snap run gnome-text-editor --standalone "$comparacao_dir/comparacao.txt"
```

Salvar como `resultado-snap.txt`, fechar e reabrir:

```bash
snap run gnome-text-editor --standalone "$comparacao_dir/resultado-snap.txt"
```

Conferir a versão na janela e guardar capturas. `--standalone` solicita uma instância independente; confirmar a opção na versão instalada durante o ensaio. Uma abertura via seletor de arquivos pode envolver um portal, ou seja, acesso mediado pela escolha do usuário.

### 4. Flatpak: testar acesso direto de leitura e escrita

A receita consultada declara `--filesystem=host`. Portanto, um bloqueio não deve ser presumido na configuração padrão. O teste abaixo pede uma configuração diferente **apenas para cada execução**, sem criar override persistente.

Primeiro, verificar leitura em uma pasta exposta como somente leitura:

```bash
flatpak run --user --nofilesystem=host:reset --filesystem="$comparacao_dir":ro --command=sh org.gnome.TextEditor -c 'cat "$1"' sh "$comparacao_dir/comparacao.txt"
```

Depois, tentar gravar na mesma pasta com a mesma restrição:

```bash
flatpak run --user --nofilesystem=host:reset --filesystem="$comparacao_dir":ro --command=sh org.gnome.TextEditor -c 'printf "%s\n" "Resultado: teste de permissao" > "$1"' sh "$comparacao_dir/escrita-flatpak.txt"
```

Por fim, conceder leitura e escrita apenas à pasta de teste:

```bash
flatpak run --user --nofilesystem=host:reset --filesystem="$comparacao_dir" --command=sh org.gnome.TextEditor -c 'printf "%s\n" "Resultado: teste de permissao" > "$1"' sh "$comparacao_dir/escrita-flatpak.txt"
```

**Expectativa a validar:** leitura permitida; gravação negada com `:ro`; gravação permitida quando a pasta é exposta sem `:ro`. Registrar erro e código de saída quando houver. Esses comandos executam um shell do runtime no contexto da aplicação para observar acesso direto; não simulam a interface do editor nem medem acessos por portais. Se `host:reset` ou o comando solicitado não estiver disponível, registrar a incompatibilidade e ajustar o piloto antes da aula. [Fonte das opções](https://docs.flatpak.org/en/latest/flatpak-command-reference.html#flatpak-run).

### 5. Snap: relacionar acesso direto à interface home

Este teste depende de a instalação declarar `strict`, de o sistema oferecer o suporte necessário e de `snap connections gnome-text-editor` listar a interface `home`. Se essas condições não forem atendidas, registrar a limitação.

1. Guardar a saída de `snap connections gnome-text-editor` e o estado inicial de `home`.
2. Copiar o caminho absoluto mostrado no passo 2.
3. Abrir um shell no contexto do snap:

```bash
snap run --shell gnome-text-editor
```

Nesse shell, usar `cat` com o caminho absoluto de `comparacao.txt` copiado do terminal principal. Registrar a leitura e sair com `exit`. Não depender de `$HOME` dentro do snap: essa variável pode apontar para a pasta de dados da aplicação.

Se `home` estava conectada, no terminal principal:

```bash
sudo snap disconnect gnome-text-editor:home
snap connections gnome-text-editor
snap run --shell gnome-text-editor
```

Repetir o mesmo acesso direto com `cat`, registrar o resultado e sair com `exit`. **Expectativa a validar:** a retirada da interface pode bloquear o acesso direto ao documento. Se continuar permitido, investigar outras interfaces e o suporte do hospedeiro antes de interpretar o resultado.

Restaurar a conexão que estava presente no início e conferir novamente:

```bash
sudo snap connect gnome-text-editor:home :home
snap connections gnome-text-editor
```

Se `home` já estava desconectada, registrar esse estado e planejar uma etapa explícita de conexão, teste e desconexão para retornar ao estado inicial. Fechar e reabrir os processos a cada mudança.

Esse teste altera uma interface de acesso à pasta pessoal; ele não corresponde exatamente à concessão de uma única pasta no Flatpak. A leitura pelo shell evita confundir acesso direto e autorização mediada por um seletor de arquivos. Fontes: [interface home](https://snapcraft.io/docs/reference/interfaces/home-interface/), [conexões](https://snapcraft.io/docs/how-to-guides/manage-snaps/connect-interfaces/) e [shell de diagnóstico](https://snapcraft.io/docs/reference/development/environment-variables/).

## Empacotamento: o que explicar e o que entregar

Para esta parte, estudar as receitas e descrever o fluxo. A compilação dos dois pacotes do editor é uma atividade adicional, ainda não executada nesta preparação.

**Flatpak:** identificar ID, runtime, SDK, módulos/fontes e permissões no manifesto. Explicar que o builder constrói os módulos, que o resultado pode ser exportado para um repositório e que um bundle é uma alternativa de distribuição local. A publicação no Flathub possui requisitos próprios. [Tutorial oficial](https://docs.flatpak.org/en/latest/first-build.html).

**Snap:** identificar nome, base, partes da construção, comandos da aplicação e interfaces no `snapcraft.yaml`. Explicar que `snapcraft pack` produz o arquivo `.snap`, que o teste local e a publicação são etapas distintas e que a Snap Store utiliza revisões e canais. O [tutorial GTK4](https://ubuntu.com/docs/snapcraft/9/how-to/integrations/craft-a-gtk4-app/) explica o empacotamento do editor; sua receita didática não comprova a receita da revisão distribuída atualmente.

## Registro que cada piloto deve produzir

Guardar data e responsável; SO/arquitetura; versões e componentes; comando executado e saída; estado inicial e final das permissões; captura da tarefa concluída; interpretação e limites. Registrar alterações necessárias para repetir o procedimento.

Versão, revisão do pacote e commit da receita são identificadores diferentes. A receita consultada no Flathub aponta para editor 51.0; o catálogo Snap consultado aponta para 48.3 no canal stable em amd64. Confirmar os valores efetivamente instalados. Download inicial, espaço exclusivo, componentes compartilhados e uso durante execução devem ser analisados separadamente.

## Roteiro de fala — cerca de 3 minutos, mais a demonstração

“Nossa parte compara duas maneiras de distribuir aplicações. As duas fornecem dependências e utilizam mecanismos de isolamento, mas a organização e as regras de acesso são diferentes.

No Flatpak, o runtime reúne bibliotecas que várias aplicações podem compartilhar. O OSTree administra o conteúdo distribuído, e o Bubblewrap ajuda a montar o ambiente isolado. No Snap, a aplicação é distribuída em uma imagem comprimida e somente leitura. O snapd administra as revisões, enquanto mecanismos como AppArmor aplicam regras de acesso.

O ponto de Sistemas Operacionais é observar o processo: quais arquivos ele consegue ver, onde pode gravar e quais recursos recebe. O exemplo escolhido usa o mesmo editor para abrir e salvar o mesmo tipo de documento. O teste planejado irá consultar primeiro as permissões e depois verificar se uma alteração muda o acesso direto ao arquivo.

Um pacote Flatpak pode receber acesso amplo a arquivos; um Snap pode usar modos de confinamento diferentes. Por isso precisamos olhar a configuração e o suporte do sistema antes de concluir que houve proteção.

Para quem distribui software, a escolha também envolve preparar as dependências, manter a receita, testar permissões e atualizar os componentes. A conclusão depende dessas necessidades e das evidências coletadas.”

A checagem de receitas e catálogos já foi feita; os testes de execução continuam pendentes. Depois do piloto, acrescentar à fala apenas os resultados efetivamente registrados.

## Conteúdo sugerido para três slides

**Slide 1 — Como a aplicação é fornecida**

- Flatpak: aplicação + runtime compartilhado.
- Snap: imagem do pacote + base e componentes.
- Dependências exigem manutenção.

**Slide 2 — O que o processo pode acessar**

- Permissões e interfaces definem acessos.
- A configuração do pacote importa.
- O suporte do SO também importa.

**Slide 3 — Exemplo e comparação**

- Mesmo editor, mesma tarefa de arquivo.
- Consultar permissões e testar uma mudança.
- Explicar diferenças e limites observados.

Reutilizar os fundos e logos existentes quando esses tópicos forem incorporados aos slides do grupo. Manter fontes nas notas e texto curto na projeção.
