# Integrante 3 — Nix: ambientes, versões e recuperação

**Estado:** fundamentação documental concluída em 5 de novembro de 2026. A validação inicial pelo terminal está registrada separadamente nas [evidências](./evidencias/validacao.md). A edição pela janela e a repetição em outra máquina continuam pendentes; os mecanismos documentados abaixo não devem ser confundidos com resultados desses testes ainda não realizados.

**Aplicação comum do grupo:** GNOME Text Editor. O exemplo consiste em abrir `comparacao.txt`, alterar a última linha para `Resultado: concluído`, salvar como `resultado.txt` e reabrir o resultado.

## 1. Ideia principal e relação com Sistemas Operacionais

O Nix trata cada resultado de construção como um componente identificado e preservado. Em vez de alterar os arquivos de uma instalação existente, uma nova versão pode ocupar outro caminho. Isso permite manter versões ou variantes lado a lado e selecionar quais serão utilizadas. Nesse contexto, **imutável** descreve os resultados armazenados pelo Nix; não significa que documentos, configurações pessoais ou todo o sistema operacional se tornem imutáveis. [Fonte: introdução do manual do Nix](https://nix.dev/manual/nix/2.34/introduction.html).

Para Sistemas Operacionais, a questão central é: **como organizar arquivos e dependências para mudar o software disponível sem sobrescrever todos os componentes anteriores?** O exemplo liga armazenamento, resolução de caminhos e manutenção do ambiente.

## 2. Como o Nix organiza versões e dependências?

Normalmente, os componentes ficam em `/nix/store`. Cada um tem um caminho próprio, com um identificador e um nome legível. Uma representação didática seria `/nix/store/<identificador>-gnome-text-editor-<versão>`. O identificador não deve ser interpretado simplesmente como a soma dos bytes do executável: seu cálculo depende do tipo de objeto. [Fonte: caminhos do store](https://nix.dev/manual/nix/2.34/store/store-path.html).

As receitas registram fontes, ferramentas e dependências. Uma mudança nesses elementos pode produzir outra variante, mesmo mantendo o número de versão do programa. No caso do GNOME Text Editor, a receita oficial inclui bibliotecas como GTK e libadwaita e ferramentas de construção como Meson e Ninja. Os nomes e versões efetivos devem ser consultados na revisão utilizada no experimento. [Fonte: receita do GNOME Text Editor no Nixpkgs](https://github.com/NixOS/nixpkgs/blob/master/pkgs/by-name/gn/gnome-text-editor/package.nix).

**Store, perfil e geração são coisas diferentes:**

- **Store:** guarda os componentes disponíveis e suas dependências.
- **Perfil:** reúne referências aos programas selecionados para determinado ambiente.
- **Geração:** registra uma versão desse perfil, permitindo selecionar um estado anterior.

Os perfis usam links simbólicos: referências do sistema de arquivos que levam aos componentes no store. Assim, guardar duas versões não obriga o usuário a chamar ambas pelo mesmo nome no mesmo ambiente. O perfil e o `PATH` ajudam a selecionar qual programa será encontrado pelo terminal. [Fonte: perfis e gerações](https://nix.dev/manual/nix/2.34/package-management/profiles.html).

## 3. Como manter ambientes diferentes para projetos diferentes?

Um projeto pode declarar suas ferramentas em um arquivo Nix. Ao entrar no ambiente desse projeto, as ferramentas escolhidas ficam disponíveis no terminal; outro projeto pode declarar escolhas diferentes. Bibliotecas idênticas podem ser compartilhadas no store, sem exigir uma cópia completa para cada projeto. [Fontes: ambientes declarativos](https://nix.dev/tutorials/first-steps/declarative-shell.html) e [organização dos pacotes](https://nix.dev/manual/nix/2.34/introduction.html).

O exemplo do grupo deve distinguir duas observações:

1. **Seleção de ambiente:** mostrar o caminho e a versão do editor disponível em um ambiente definido.
2. **Coexistência:** preparar dois perfis ou ambientes e verificar qual variante cada um seleciona.

Dois perfis com o mesmo pacote demonstram seleção independente, mas **não demonstram duas versões diferentes**. Para afirmar isso, é necessário registrar revisões que realmente forneçam versões distintas. Alterar apenas o nome do perfil não altera o programa.

Ambientes de desenvolvimento não são máquinas virtuais: continuam dependendo do sistema hospedeiro. Sair do terminal do ambiente muda a seleção de ferramentas; não apaga automaticamente seus componentes do store. [Fontes: ambientes temporários](https://nix.dev/tutorials/first-steps/ad-hoc-shell-environments.html) e [coleta de componentes não utilizados](https://nix.dev/manual/nix/2.34/package-management/garbage-collection.html).

## 4. O que registrar para outra pessoa repetir o ambiente?

Compartilhar somente a lista de nomes dos pacotes é insuficiente: duas máquinas podem consultar revisões diferentes do Nixpkgs. Fixar uma revisão identifica a coleção de receitas utilizada. [Fonte: fixação do Nixpkgs](https://nix.dev/tutorials/first-steps/towards-reproducibility-pinning-nixpkgs).

No procedimento do grupo, registrar:

- Arquivos de configuração e revisão do próprio projeto.
- Revisão exata do Nixpkgs e alterações locais, se existirem.
- `flake.nix` e `flake.lock`, se o exemplo usar flakes; em outra abordagem, a referência fixa utilizada no arquivo Nix.
- Sistema operacional, arquitetura, versão do Nix e recursos experimentais habilitados.
- Comandos, variáveis necessárias, versões observadas e arquivos de entrada.
- Para o editor gráfico, sessão gráfica e eventuais ajustes necessários para abrir a janela.

Em uma flake, `flake.nix` descreve entradas e resultados; `flake.lock` fixa as entradas resolvidas. Os dois arquivos devem acompanhar o projeto. O lock não guarda sozinho o código e todos os arquivos locais do projeto. A interface de flakes ainda é identificada como experimental no manual consultado. [Fonte: flakes e arquivos de lock](https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-flake.html).

O teste de repetição será um colega usar esses registros e executar a mesma tarefa. Primeiro comparar versões e comportamento; **não concluir identidade binária apenas porque a configuração é igual**. O ambiente gráfico e o suporte dos pacotes variam entre plataformas, e o Nix busca construções determinísticas sem tornar irrelevantes todas as condições externas. [Fontes: ambientes e suporte de plataformas](https://nix.dev/tutorials/first-steps/ad-hoc-shell-environments.html) e [modelo funcional](https://nix.dev/manual/nix/2.34/introduction.html).

## 5. O que pode ser recuperado ao retornar a uma geração?

O retorno de um perfil seleciona uma geração anterior dos programas daquele perfil. Não é uma restauração completa da máquina: não troca automaticamente o kernel ou os pacotes administrados pelo Debian e não desfaz edições em `resultado.txt`, preferências pessoais ou migrações de bancos de dados. Esse limite decorre do objeto da operação: **o perfil**, e não todos os arquivos do sistema. Processos já abertos também não são substituídos automaticamente; reabrir o programa é parte da verificação. [Fontes: operação de rollback](https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-profile-rollback.html) e [seleção por perfis](https://nix.dev/manual/nix/2.34/package-management/profiles.html).

Há três ações distintas:

- **Voltar uma geração do perfil:** selecionar os programas de um estado anterior preservado.
- **Voltar uma configuração do projeto:** recuperar seus arquivos Nix e, quando usado, o lock anterior no controle de versão; entrar novamente no ambiente correspondente.
- **Recuperar documentos e outros dados:** utilizar histórico ou backup desses dados.

Usar `nix develop` não cria, por si só, um histórico comum de instalações que possa ser desfeito com o rollback do perfil de aplicativos. O comando tem uma opção explícita para registrar seu ambiente em um perfil; o procedimento precisa indicar qual perfil foi usado. [Fonte: `nix develop`](https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-develop.html).

Manter gerações antigas preserva referências aos componentes necessários para recuperá-las, mas ocupa espaço. Apagar gerações e coletar componentes sem referências pode eliminar essa possibilidade local. Uma configuração antiga pode permitir uma nova obtenção ou construção, dependendo da disponibilidade de fontes e demais requisitos; isso difere de selecionar imediatamente uma geração ainda preservada. [Fonte: coleta de lixo](https://nix.dev/manual/nix/2.34/package-management/garbage-collection.html).

## 6. Proteção: o ambiente Nix não é um confinamento da aplicação

O Nix possui mecanismos de isolamento durante a **construção**, úteis para evitar dependências não declaradas. Isso não significa que um editor iniciado pelo Nix tenha automaticamente uma política que bloqueie o acesso aos documentos do usuário. [Fonte: opção `sandbox` do Nix](https://nix.dev/manual/nix/2.34/command-ref/conf-file.html#conf-sandbox).

Essa distinção orienta a comparação: Flatpak possui permissões para recursos da aplicação; no Snap, a interpretação depende também do modo de confinamento e do suporte do sistema. Portanto, coexistência de dependências e controle de acesso devem ser avaliados separadamente. [Fontes: permissões do Flatpak](https://docs.flatpak.org/en/latest/sandbox-permissions.html) e [confinamento do Snap](https://snapcraft.io/docs/explanation/security/snap-confinement/).

## 7. Benefícios, custos e comparação pertinente

**Interpretação para desenvolvimento individual:** o Nix é especialmente útil quando uma pessoa alterna entre projetos com ferramentas diferentes e quer registrar suas escolhas. O custo é aprender a configuração e cuidar do espaço ocupado pelos componentes preservados. [Base documental: ambientes declarativos](https://nix.dev/tutorials/first-steps/declarative-shell.html) e [coleta de lixo](https://nix.dev/manual/nix/2.34/package-management/garbage-collection.html).

**Interpretação para equipes:** arquivos compartilhados e revisões fixas tornam o ambiente mais explícito e reduzem diferenças causadas por coleções de pacotes distintas. O benefício depende de todos seguirem o procedimento e revisarem atualizações. Configurações que consultam `<nixpkgs>` sem controlar sua origem podem variar entre máquinas. [Fonte: boas práticas e dependências externas](https://nix.dev/guides/best-practices.html#lookup-paths).

**Comparação com Debian:** o Debian registra dependências e relações entre pacotes. A diferença a observar é como essa administração se relaciona com a seleção de componentes por perfis e caminhos próprios no Nix. Não se deve afirmar que o Debian carece de controle de dependências. [Fontes: metadados de pacotes Debian](https://www.debian.org/doc/manuals/debian-handbook/sect.package-meta-information.en.html) e [perfis Nix](https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-profile.html).

**Comparação com FreeBSD Ports:** ambos utilizam descrições de construção. Ports permite acompanhar e personalizar a construção de fontes; no Nix, a receita também pode resultar na obtenção de um binário previamente construído. Separar download, construção e ativação ao interpretar custos. [Fontes: manual de Ports](https://docs.freebsd.org/en/books/handbook/ports/) e [uso de cache binário no Nix](https://nix.dev/manual/nix/2.34/introduction.html#transparent-sourcebinary-deployment).

**Comparação com Flatpak e Snap:** o experimento com o mesmo editor permite confrontar armazenamento, dependências e acesso a arquivos. A escolha deve considerar a necessidade: preparar ferramentas de projetos, administrar software do sistema ou distribuir aplicações com determinadas políticas de acesso. As fontes não justificam um vencedor universal nem um ranking de desempenho sem medidas.

## 8. Exemplo e evidências a apresentar

**Configuração do exemplo:** o roteiro utiliza GNOME Text Editor a partir da revisão `3ec636362e1816bc2f0888fa0fa2c69f1bc9e504` do Nixpkgs. A configuração e o lock devem acompanhar a entrega. A revisão identifica a receita utilizada, e não substitui o registro da versão efetiva obtida. [Fonte: receita na revisão escolhida](https://github.com/NixOS/nixpkgs/blob/3ec636362e1816bc2f0888fa0fa2c69f1bc9e504/pkgs/by-name/gn/gnome-text-editor/package.nix).

**Procedimento preparado e validado pelo terminal:** localizar o executável e selecionar o editor em dois perfis de demonstração, A e B. Ambos utilizam a mesma versão. Remover o editor apenas de A permite observar a independência de seleção; retornar à geração anterior de A permite verificar a recuperação do perfil. Esse procedimento não demonstra duas versões do editor nem uma atualização. As saídas e os limites da execução estão no registro de evidências.

**Etapa gráfica pendente:** o ambiente de preparação não possui uma sessão gráfica disponível. A abertura da janela e a edição de `comparacao.txt` precisam ocorrer em uma sessão adequada. A presença do executável não comprova que a tarefa gráfica foi concluída. O [roteiro local](./README.md) orienta a validação; o [registro de evidências](./evidencias/validacao.md) reúne os resultados efetivamente executados, separados das etapas pendentes.

**Evidências necessárias:** versão do Nix e do editor; configuração e revisão fixada; caminho do executável; tarefa concluída; perfis e gerações realmente utilizados; comportamento após retorno de geração; repetição por colega. Medidas de tempo ou disco, se coletadas, devem indicar cache inicial e se houve compilação local.

**Limite importante:** acrescentar ou remover outro pacote de um perfil pode demonstrar gerações e recuperação, mas não equivale a testar uma atualização do editor. Para demonstrar atualização, registrar versões efetivamente diferentes e repetir a tarefa em ambas.

## 9. Síntese para a fala

“O Nix guarda os componentes em caminhos próprios e usa ambientes ou perfis para selecionar o que vamos utilizar. Isso ajuda projetos diferentes a manter suas ferramentas e facilita compartilhar a configuração com um colega. Uma geração anterior pode recuperar os programas daquele perfil, mas não desfaz mudanças nos documentos. Essa organização também não limita, sozinha, o acesso do editor aos arquivos. Vamos demonstrar essas diferenças com o mesmo editor usado pelo restante do grupo.”

As fontes próximas de cada afirmação são documentação oficial do projeto Nix/NixOS, a receita mantida no Nixpkgs e manuais oficiais dos demais representantes. Consulta em **5 de novembro de 2026**; conferir a revisão realmente usada antes da apresentação.
