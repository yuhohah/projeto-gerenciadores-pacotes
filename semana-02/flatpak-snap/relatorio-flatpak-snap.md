# Integrante 4 — Flatpak e Snap

**Etapa:** semana 2, fundamentação e preparação dos exemplos.  
**Consulta às fontes:** 5 de novembro de 2026.  
**Estado:** pesquisa documental. Este relatório não apresenta instalações, construções de pacotes, testes gráficos ou medições executados com Flatpak/Snap. Os procedimentos práticos e as pendências estão no [guia desta parte](./README.md).

## Ideia principal e relação com Sistemas Operacionais

As duas alternativas procuram distribuir aplicações com um conjunto mais controlado de dependências e recursos acessíveis. Para Sistemas Operacionais, interessam duas perguntas: **como o programa é armazenado e atualizado?** E **o que ele pode acessar quando está executando?** Armazenamento e proteção são mecanismos diferentes: um pacote somente para leitura ainda pode executar um programa autorizado a modificar documentos. [Fontes: conceitos do Flatpak](https://docs.flatpak.org/en/latest/basic-concepts.html), [formato Snap](https://snapcraft.io/docs/reference/development/yaml-schemas/the-snap-format/) e [confinamento Snap](https://snapcraft.io/docs/explanation/security/snap-confinement/).

## 1. Como transformar uma aplicação em um pacote instalável?

### Flatpak

O desenvolvedor escreve um **manifesto**, geralmente JSON ou YAML, que informa identificação, ambiente de execução, ferramentas de construção, fontes, etapas de compilação e permissões. O `flatpak-builder` lê a receita, constrói os componentes e pode exportar o resultado para um repositório. Isso transforma uma descrição da construção em arquivos de aplicação que outra máquina poderá instalar; escrever a receita não significa que sua construção já foi validada. [Fonte: primeiro Flatpak](https://docs.flatpak.org/en/latest/first-build.html).

A distribuição pode utilizar Flathub ou um repositório próprio. Também existe o arquivo `.flatpak`, gerado com `flatpak build-bundle` a partir de um repositório construído. Esse arquivo não reúne automaticamente todas as dependências externas, como o runtime; portanto, não deve ser apresentado como uma solução offline completa. Um `.flatpakref` é uma referência de instalação, não o conteúdo completo da aplicação. [Fontes: repositórios](https://docs.flatpak.org/en/latest/repositories.html) e [bundles](https://docs.flatpak.org/en/latest/single-file-bundles.html).

### Snap

A receita é o **`snapcraft.yaml`**. Ela define nome, versão, base, componentes de construção, comandos da aplicação e confinamento. O Snapcraft obtém as fontes, constrói e prepara os arquivos; a etapa de empacotamento gera o arquivo `.snap`. No Snapcraft 9, `snapcraft pack` pode executar o ciclo necessário até produzir o pacote. A execução depende do ambiente de construção configurado. [Fontes: referência YAML](https://ubuntu.com/docs/snapcraft/9/reference/snapcraft-yaml/) e [comando pack](https://ubuntu.com/docs/snapcraft/9/reference/commands/pack/).

O pacote pode ser instalado localmente para validação. Publicar na Snap Store é outra etapa: exige autenticação, registro do nome, envio e liberação para um canal. Para o trabalho, estudar esse caminho e testar localmente já atende ao exemplo; não é necessário publicar um pacote do grupo na loja. [Fonte: publicação](https://ubuntu.com/docs/snapcraft/9/how-to/publishing/publish-a-snap/).

## 2. Como cada ferramenta fornece as dependências?

**Flatpak:** o runtime fornece bibliotecas básicas e pode ser compartilhado por várias aplicações. O SDK reúne ferramentas necessárias à construção; não é a mesma coisa que o runtime usado para executar. Dependências ausentes no runtime podem acompanhar a aplicação. Isso permite selecionar componentes sem exigir a substituição das bibliotecas utilizadas pelo restante da distribuição. [Fontes: conceitos](https://docs.flatpak.org/en/latest/basic-concepts.html) e [dependências](https://docs.flatpak.org/en/latest/dependencies.html).

**Snap:** a base fornece parte do ambiente de execução. Bibliotecas adicionais podem entrar no pacote, e interfaces de conteúdo permitem compartilhar componentes fornecidos por outros snaps. Extensões, como a do GNOME, ajudam a configurar esse ambiente. Não é correto dizer que todos os snaps carregam individualmente uma cópia completa de todas as bibliotecas. [Fontes: dependências](https://ubuntu.com/docs/snapcraft/9/how-to/crafting/manage-dependencies/) e [exemplo GTK4](https://ubuntu.com/docs/snapcraft/9/how-to/integrations/craft-a-gtk4-app/).

**Consequência para a comparação:** o primeiro aplicativo pode baixar componentes compartilhados que já estarão disponíveis para o segundo. O grupo deve registrar o estado inicial; medir apenas o tamanho anunciado do aplicativo deixa parte do armazenamento de fora. Essa é uma orientação metodológica decorrente das dependências descritas acima, não um resultado medido.

## 3. Qual é a função de cada tecnologia?

### OSTree e Bubblewrap no Flatpak

- **OSTree:** mantém e distribui versões dos arquivos binários da aplicação e dos runtimes. Objetos iguais podem ser compartilhados no armazenamento; a organização por versões apoia atualizações e retorno a versões disponíveis. Ele cuida da organização e distribuição dos arquivos, não define sozinho o acesso aos documentos. [Fonte: funcionamento interno](https://docs.flatpak.org/en/latest/under-the-hood.html).
- **Bubblewrap:** monta o ambiente de execução usando recursos do kernel Linux, especialmente namespaces, para controlar a visão que o processo tem do sistema. O Flatpak utiliza essa ferramenta como parte da sandbox. A política efetiva depende das opções configuradas pelo Flatpak: usar Bubblewrap não determina, por si só, uma política universal. [Fonte: projeto Bubblewrap](https://github.com/containers/bubblewrap).

### SquashFS, AppArmor e cgroups no Snap

- **SquashFS:** é o sistema de arquivos comprimido e somente para leitura do pacote `.snap`. Ao instalar uma revisão, sua imagem é montada, normalmente em `/snap/nome/revisao/`. Não é necessário montar novamente a imagem do pacote a cada abertura do aplicativo; a execução prepara seu ambiente de confinamento. [Fontes: formato Snap](https://snapcraft.io/docs/reference/development/yaml-schemas/the-snap-format/) e [arquitetura](https://snapcraft.io/docs/reference/system-architecture/).
- **AppArmor:** aplica políticas de acesso, incluindo arquivos e capacidades, por comando. No confinamento estrito, as interfaces concedem acessos adicionais. Namespaces e seccomp também participam da proteção; atribuir todo o confinamento ao AppArmor simplifica demais o mecanismo. [Fonte: políticas de segurança](https://snapcraft.io/docs/explanation/security/security-policies/).
- **cgroups:** agrupam processos para controle de recursos e, em situações previstas, de dispositivos. Sua presença não estabelece automaticamente um teto de CPU e memória para todo aplicativo. A documentação de quotas descreve limites configuráveis para serviços de snaps. Não realizamos um teste dessas quotas. [Fontes: arquitetura](https://snapcraft.io/docs/reference/system-architecture/), [políticas](https://snapcraft.io/docs/explanation/security/security-policies/) e [quotas](https://snapcraft.io/docs/how-to-guides/manage-snaps/use-resource-quotas/).

**Precisão necessária:** Snap tem `strict`, `classic` e o modo de desenvolvimento `devmode`. `classic` oferece acesso semelhante ao de software tradicional; `devmode` permite acesso para depuração e não comprova confinamento estrito. A proteção disponível também depende do kernel e da integração de segurança da distribuição. [Fontes: confinamento](https://snapcraft.io/docs/explanation/security/snap-confinement/) e [suporte das distribuições](https://snapcraft.io/docs/reference/administration/distribution-support/).

## 4. Como as permissões afetam arquivos, rede e recursos?

No **Flatpak**, a aplicação parte de acessos restritos, ampliados pelas permissões do pacote e por configurações locais. `--filesystem` concede acesso a locais do sistema de arquivos; `--share=network` permite acesso à rede. **Portais** podem mediar operações, como escolher um arquivo pela janela, sem conceder acesso geral a todos os documentos. Assim, abrir um arquivo pelo seletor não demonstra acesso irrestrito à pasta inteira. [Fonte: permissões](https://docs.flatpak.org/en/latest/sandbox-permissions.html).

No **Snap estrito**, interfaces conectam as necessidades do programa aos recursos permitidos pelo sistema. A interface `home` permite arquivos não ocultos pertencentes ao usuário em sua pasta pessoal; outras necessidades exigem interfaces apropriadas. Declarar uma interface e tê-la efetivamente conectada são estados distintos. Snap também pode utilizar portais na integração gráfica. As permissões tradicionais de proprietário e grupo continuam relevantes. [Fontes: interface home](https://snapcraft.io/docs/reference/interfaces/home-interface/), [portais](https://snapcraft.io/docs/explanation/snap-development/xdg-desktop-portals/) e [políticas](https://snapcraft.io/docs/explanation/security/security-policies/).

Logo, a análise deve registrar **permissões reais do pacote, alterações locais e caminho usado para abrir o arquivo**. A palavra “sandbox” não basta para afirmar que determinado acesso será bloqueado.

## 5. Qual é o esforço para distribuir, atualizar e manter?

**Flatpak:** exige manter manifesto, componentes incluídos, permissões e compatibilidade com o runtime escolhido. É possível hospedar o repositório ou utilizar Flathub. Atualizar significa disponibilizar novos commits e aplicá-los, por exemplo, com `flatpak update`; a automação também depende da integração do ambiente. O retorno a um commit anterior exige que ele esteja disponível. Trocar a versão da aplicação não restaura automaticamente seus documentos ou desfaz mudanças no formato de seus dados. [Fontes: repositórios](https://docs.flatpak.org/en/latest/repositories.html), [dependências](https://docs.flatpak.org/en/latest/dependencies.html) e [referência de comandos](https://docs.flatpak.org/en/latest/flatpak-command-reference.html#flatpak-update).

**Snap:** exige manter receita, base, componentes incluídos, interfaces e compatibilidade dos dados. A loja organiza revisões e canais; o snapd consulta atualizações automaticamente, com controles de agendamento e adiamento. Pacotes instalados apenas localmente não recebem automaticamente novas versões da loja. `snap revert` pode recuperar uma revisão preservada e seus dados de configuração associados, mas dados compartilhados em diretórios `common` e documentos externos não são automaticamente revertidos. [Fontes: publicação](https://ubuntu.com/docs/snapcraft/9/how-to/publishing/publish-a-snap/) e [atualizações e reversão](https://snapcraft.io/docs/how-to-guides/manage-snaps/manage-updates/).

Em ambos, incluir uma biblioteca no pacote transfere ao mantenedor a tarefa de acompanhar suas correções e publicar uma construção atualizada. Isolamento e atualização não dispensam manutenção.

## Exemplo explicado: GNOME Text Editor

A tarefa será abrir `comparacao.txt`, alterar a linha `Resultado: aguardando` para `Resultado: concluído`, salvar como `resultado.txt` e reabrir. Isso serve para comparar instalação e acesso a documentos; não é um benchmark do editor.

No **Flatpak**, o identificador é `org.gnome.TextEditor`. O manifesto Flathub na revisão `5f9138c4ef35c63c58e54a5558f5661d249412a0` usa GNOME Platform/SDK 51, inclui componentes adicionais e declara `--filesystem=host`, um acesso amplo. Ele aponta para a fonte 51.0; isso descreve a receita consultada, não prova a versão instalada ou distribuída a toda arquitetura. [Fonte: manifesto fixado](https://github.com/flathub/org.gnome.TextEditor/blob/5f9138c4ef35c63c58e54a5558f5661d249412a0/org.gnome.TextEditor.json).

No **Snap**, o nome é `gnome-text-editor`; a loja consultada apresenta Ken VanDine como publicador e 48.3 em `latest/stable`. A consulta à API para amd64 registrou revisão 53, base `core24` e metadado `strict`. Isso não comprova interfaces conectadas nem confinamento efetivo de uma instalação. O tutorial oficial de empacotamento usa o mesmo editor, porém uma receita didática com `source-tag: "42.2"`, `core22`, extensão GNOME e `strict`. **Essa receita não comprova como a revisão atual da loja foi construída.** [Fontes: loja](https://snapcraft.io/gnome-text-editor), [registro da consulta à API](./evidencias/consulta-fontes.json) e [tutorial GTK4](https://ubuntu.com/docs/snapcraft/9/how-to/integrations/craft-a-gtk4-app/).

## Síntese para a conclusão conjunta

**Avaliação baseada nas fontes:** Flatpak é uma opção pertinente para distribuir aplicações gráficas, com runtimes e portais, escolhendo Flathub ou repositório próprio. Seu custo inclui manter dependências próprias e revisar permissões amplas. Snap é pertinente para distribuir aplicações e serviços com canais, revisões e atualização administrada pelo snapd; exige avaliar base, interfaces e suporte de confinamento do sistema de destino.

O exemplo evidencia escolhas de armazenamento, manutenção e proteção. Ainda não permite afirmar qual consome menos recursos ou qual é universalmente melhor. A conclusão prática depende dos testes registrados e das necessidades da aplicação.
