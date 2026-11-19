# Relatório parcial 1 — Gerenciadores de pacotes em Unix/Linux

**Etapa:** semana 2 — fundamentação e preparação dos exemplos.  
**Versão consolidada:** 5 de novembro de 2026.  
**Estado:** materiais dos quatro integrantes integrados. Há uma validação inicial de Nix pelo terminal; os demais exemplos têm fundamentação e procedimentos, sem evidências de execução anexadas. Não foram realizados benchmarks comparativos.

## 1. Introdução e objetivo

Instalar um programa envolve mais que copiar um executável. É necessário disponibilizar bibliotecas, organizar arquivos, escolher versões compatíveis e decidir quais recursos o programa poderá acessar. Atualizações modificam o ambiente e podem exigir recuperação de componentes anteriores. Essas decisões aproximam os gerenciadores de pacotes dos temas de Sistemas Operacionais: sistema de arquivos, processos, proteção, compatibilidade e administração de recursos.

**Pergunta orientadora:** como diferentes gerenciadores organizam o software e quais consequências suas escolhas trazem para armazenamento, compatibilidade, recuperação e proteção?

Esta etapa consolida a fundamentação, incorpora os exemplos enviados pelos integrantes e define o que será demonstrado. O objetivo é comparar soluções para necessidades concretas, sem antecipar um vencedor universal. As conclusões distinguem mecanismos descritos nas fontes, procedimentos planejados e resultados efetivamente observados.

## 2. Escopo e materiais incorporados

O trabalho contempla cinco representantes em quatro famílias:

- **Binários tradicionais mutáveis (FHS, padrão de organização dos diretórios):** Debian, com APT/dpkg.
- **Baseados em código-fonte (Source/Ports):** FreeBSD Ports.
- **Funcionais e imutáveis:** Nix.
- **Containerizados / sandboxed:** Flatpak, com OSTree/Bubblewrap, e Snap, com SquashFS/AppArmor/cgroups.

APT e dpkg são camadas complementares de um representante. Em FreeBSD, o foco é construir pelas receitas de Ports; `pkg` aparece no registro e instalação dos pacotes, sem acrescentar outra família. Os rótulos são didáticos: os representantes também utilizam receitas, bibliotecas compartilhadas e mecanismos do hospedeiro em combinações distintas.

Foram incorporados [Debian: APT e dpkg](./materiais-integrantes/debian-apt-dpkg.pdf), com oito slides, e [FreeBSD: Ports](./materiais-integrantes/freebsd-ports.pdf), com quatro. O primeiro propõe `tmux`; o segundo, `misc/hello`. Ambos explicam procedimentos, mas não apresentam logs suficientes para considerar seus pilotos executados. A consolidação mantém esses exemplos didáticos e corrige as generalizações técnicas indicadas abaixo.

## 3. Fundamentação das quatro famílias

### 3.1. Debian — APT/dpkg

**Funções e instalação.** O dpkg desempacota, configura, remove e registra pacotes `.deb`. O APT consulta repositórios, seleciona uma solução de dependências e obtém os pacotes necessários, utilizando o dpkg na instalação. `apt update` renova os índices disponíveis; não atualiza sozinho os programas instalados. Isso separa consulta ao catálogo de alteração dos arquivos da máquina. [Debian FAQ, capítulo 8](https://www.debian.org/doc/manuals/debian-faq/pkgtools.en.html).

**Exemplo e consulta.** O material propõe instalar `tmux` e consultar dependências e versão. O piloto deve registrar saídas de `apt-cache depends tmux`, `apt show tmux` e `dpkg -l tmux`. Acrescentar `dpkg -L tmux` permite mostrar arquivos administrados; `dpkg -S /caminho/do/arquivo` consulta o pacote associado a um caminho. As listas não abrangem necessariamente todos os arquivos criados depois por scripts ou pela aplicação. [Manual dpkg-query](https://manpages.debian.org/trixie/dpkg/dpkg-query.1.en.html).

**Versões e projetos.** As preferências do APT influenciam a versão selecionada para uma instalação. Pinning não cria ambientes independentes por projeto, nem toda regra mantém eternamente a mesma versão. Projetos incompatíveis podem precisar de um mecanismo adicional de separação. O exemplo oral deve explicar essa limitação, sem misturar releases para demonstrá-la. Registrar origens e versões é essencial para repetir a instalação. [Manual apt_preferences](https://manpages.debian.org/trixie/apt/apt_preferences.5.en.html).

**Atualizações.** Podem mudar executáveis e bibliotecas compartilhadas. Por padrão, `apt-get upgrade` não remove pacotes nem instala novos; `apt-get dist-upgrade` pode instalar e remover para resolver mudanças de dependências. Essa distinção não deve ser extrapolada para todo comando chamado upgrade. Uma simulação ajuda a examinar o plano. `apt -f install` tenta corrigir dependências quebradas; não garante completar toda instalação e pode propor remoções. [Manual apt-get](https://manpages.debian.org/trixie/apt/apt-get.8.en.html). Arquivos administrados como conffiles recebem tratamento para preservar alterações locais, podendo exigir uma decisão; isso não é backup de todos os dados. [Debian Policy, arquivos de configuração](https://www.debian.org/doc/debian-policy/ch-files.html#configuration-files).

**Uso e limitações.** Para desenvolvimento, é uma opção prática para obter ferramentas integradas à distribuição. A contrapartida é administrar a compatibilidade com o conjunto de versões instalado. A organização segue diretórios padronizados e distingue executáveis, bibliotecas e configuração; consultar os arquivos de um pacote torna essa relação visível. [Debian Policy, arquivos](https://www.debian.org/doc/debian-policy/ch-files.html). Não há, nos materiais recebidos, um rollback geral demonstrado nem medições de desempenho.

### 3.2. FreeBSD Ports — receitas e construção

**Da fonte à instalação.** Um port reúne instruções, verificações e ajustes para construir software. O fluxo inclui obtenção das fontes, extração, aplicação de patches, configuração, compilação, preparação em uma árvore temporária, geração de pacote e instalação. As dependências entram conforme as etapas necessárias. Esse percurso relaciona arquivos temporários, ferramentas de construção e resultado instalado. [Porter's Handbook, funcionamento das etapas](https://docs.freebsd.org/en/books/porters-handbook/slow-porting/).

**Personalização.** O piloto proposto é `misc/hello`. A receita consultada oferece a opção **NLS**, suporte a idiomas, com ajustes e dependências associados. O integrante deve mostrar a opção disponível na revisão realmente usada e explicar sua escolha, em vez de sugerir que qualquer característica do programa pode ser alterada por um menu. [Receita oficial de misc/hello](https://cgit.freebsd.org/ports/tree/misc/hello/Makefile).

**Custo da construção.** Compilar utiliza CPU e memória e produz arquivos de trabalho, além de exigir fontes e dependências. Rede, paralelismo e componentes já presentes mudam o custo observado. Medir apenas o tamanho final ignora esse trabalho. O manual diferencia instalação de binários e construção pelos Ports; obter um binário evita a compilação local correspondente, mas não demonstra menor manutenção em qualquer situação. [FreeBSD Handbook, Packages and Ports](https://docs.freebsd.org/en/books/handbook/ports/).

**Repetição e decisão.** O procedimento deve registrar versão do FreeBSD, arquitetura, revisão da árvore, fontes/checksums, opções, dependências e comandos. Essas informações permitem investigar diferenças; não garantem identidade binária por si sós. Para o trabalho, o controle adicional faz sentido quando existe uma opção de construção relevante. O esforço precisa ser justificado pelo requisito, sem expandir a apresentação para administração completa de FreeBSD. Jails, poudriere e repositório próprio permanecem possibilidades futuras, fora do piloto principal.

**Estado do exemplo:** foram recebidos roteiro e explicações, sem evidência de compilação ou medidas. Faltam ambiente, opção efetivamente escolhida, trecho do log e execução final de `hello`.

### 3.3. Nix — componentes, perfis e gerações

O Nix mantém componentes em caminhos próprios, normalmente em `/nix/store`. Um perfil seleciona os programas disponíveis por referências a esses caminhos; gerações preservam estados do perfil. Componentes podem coexistir sem substituir diretamente os arquivos anteriores. Imutabilidade refere-se aos resultados administrados no store, não aos documentos pessoais. [Perfis e gerações](https://nix.dev/manual/nix/2.34/package-management/profiles.html).

Projetos podem declarar ferramentas distintas. Para compartilhar um ambiente, registrar configuração, revisão do Nixpkgs, SO, arquitetura e versão do Nix. No exemplo, `flake.nix` e `flake.lock` acompanham o projeto: a revisão fixada reduz variações na seleção de receitas. Não comprova identidade binária ou funcionamento idêntico em qualquer hospedeiro. [Ambientes declarativos](https://nix.dev/tutorials/first-steps/declarative-shell.html) e [fixação do Nixpkgs](https://nix.dev/tutorials/first-steps/towards-reproducibility-pinning-nixpkgs).

O rollback de um perfil seleciona uma geração preservada. Não desfaz automaticamente documentos, configurações pessoais ou alterações em bancos de dados. Recuperar programas, recuperar a configuração declarada e recuperar dados são tarefas diferentes. [Manual de rollback](https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-profile-rollback.html).

O exemplo de GNOME Text Editor 50.1 validou dois perfis com **a mesma versão**, remoção em apenas um e recuperação da geração anterior. Demonstra independência da seleção e recuperação do perfil; não demonstra duas versões ou atualização do editor. O benefício para equipes é explicitar ferramentas e dependências; os custos incluem aprendizado e espaço para componentes preservados. Detalhes e cinco respostas: [relatório Nix](./nix/relatorio-nix.md).

### 3.4. Flatpak e Snap — distribuição e permissões

**Empacotamento e dependências.** No Flatpak, um manifesto orienta a construção com `flatpak-builder`; o runtime fornece bibliotecas de execução e o SDK, ferramentas de construção. Dependências adicionais podem acompanhar a aplicação. [Conceitos](https://docs.flatpak.org/en/latest/basic-concepts.html) e [primeira construção](https://docs.flatpak.org/en/latest/first-build.html). No Snap, `snapcraft.yaml` descreve componentes, base e comandos; Snapcraft constrói e gera o `.snap`. Construir localmente e publicar são etapas distintas. [Referência Snapcraft](https://ubuntu.com/docs/snapcraft/9/reference/snapcraft-yaml/).

**Mecanismos.** OSTree administra conteúdo versionado do Flatpak, e Bubblewrap participa do ambiente isolado do processo. [Funcionamento interno](https://docs.flatpak.org/en/latest/under-the-hood.html). O Snap usa uma imagem SquashFS somente leitura, montada como parte da instalação da revisão. AppArmor e outros mecanismos participam do confinamento; cgroups agrupam processos e apoiam controles de recursos, sem impor automaticamente uma cota universal de CPU/RAM. [Formato Snap](https://snapcraft.io/docs/reference/development/yaml-schemas/the-snap-format/) e [arquitetura](https://snapcraft.io/docs/reference/system-architecture/).

**Acesso e manutenção.** Permissões e portais influenciam arquivos, rede e integração no Flatpak. No Snap, interfaces, modo de confinamento e suporte do hospedeiro influenciam os acessos. Verificar políticas reais é indispensável: o formato do pacote não prova que uma pasta específica esteja bloqueada. [Permissões Flatpak](https://docs.flatpak.org/en/latest/sandbox-permissions.html) e [confinamento Snap](https://snapcraft.io/docs/explanation/security/snap-confinement/). Para distribuir, o desenvolvedor mantém receitas, dependências incluídas e testes das políticas; runtimes/bases compartilhados também afetam o trabalho. As cinco respostas estão no [relatório Flatpak/Snap](./flatpak-snap/relatorio-flatpak-snap.md).

## 4. Comparação pelos critérios de Sistemas Operacionais

### 4.1. Arquivos e armazenamento

Debian administra arquivos distribuídos pelos diretórios do sistema; Ports acrescenta a área temporária da construção antes da instalação. Nix separa componentes no store e seleciona referências por perfis. Flatpak combina aplicação e runtime; Snap combina imagens de revisões e componentes compartilhados. Consultar caminhos e registros torna essas diferenças observáveis. Espaço de dependências compartilhadas não deve ser atribuído integralmente a cada aplicação.

### 4.2. Dependências e compatibilidade

APT calcula dependências para o conjunto instalado; Ports explicita requisitos para construir e executar; Nix permite selecionar componentes por ambiente. Flatpak/Snap controlam parte do ambiente entregue com a aplicação por runtimes, bases e bibliotecas adicionais. Nenhuma dessas estratégias elimina toda dependência do hospedeiro. Dois perfis iguais validam seleção independente, enquanto duas versões diferentes exigem outro teste.

### 4.3. Atualizações e recuperação

No Debian e Ports, observar arquivos e dependências modificados pela operação. No Nix, observar a geração selecionada. Flatpak e Snap administram conteúdo/revisões de aplicação, mas os respectivos procedimentos de recuperação ainda não foram testados pelo grupo. Em todos os casos, especificar o estado recuperado e os dados excluídos. Uma reinstalação da mesma versão não equivale a atualização; retornar programas não equivale a restaurar documentos.

### 4.4. Proteção durante a execução

Instalar por Debian, Ports ou Nix não estabelece, sozinho, uma política de confinamento específica para a aplicação. O isolamento de construção do Nix tem outra finalidade. [Opção sandbox do Nix](https://nix.dev/manual/nix/2.34/command-ref/conf-file.html#conf-sandbox). Em Flatpak e Snap, testar permissões efetivas e relacioná-las ao suporte do sistema. Uma imagem somente leitura protege aquele conteúdo de alterações, mas o programa pode modificar documentos aos quais tenha acesso.

### 4.5. Uso de recursos

Separar download, construção, instalação, ativação e execução. Medir condições iniciais, caches, rede e componentes presentes. `tmux`, `hello` e um editor gráfico realizam tarefas diferentes: seus tempos/tamanhos não fundamentam um ranking de gerenciadores. O trabalho ainda não possui medidas comparáveis de tempo, CPU, memória ou crescimento líquido de disco.

## 5. Plano de demonstrações e testes

O [plano de testes](./plano-de-testes.md) organiza procedimentos. Os exemplos `tmux` e `hello` permanecem demonstrações didáticas dos mecanismos. Para comparações controladas, a aplicação comum proposta é GNOME Text Editor: abrir `comparacao.txt`, alterar a última linha, salvar `resultado.txt` e reabrir. A viabilidade gráfica e a construção em FreeBSD precisam ser verificadas antes de prometer essa tarefa em todos os representantes.

O núcleo dos testes é: instalar e consultar dependências/arquivos; observar seleção de ambientes; repetir instruções por outro colega; atualizar e investigar recuperação quando houver versões disponíveis; testar permissões em Flatpak/Snap. Registrar data, responsável, SO/arquitetura, versões, origem do pacote, comandos, saídas, resultado e limite de interpretação.

**Cronograma:** semana 2 valida pequenos pilotos; semana 3 apresenta as demonstrações preparadas; semana 4 repete procedimentos e compara evidências; semana 5 consolida resultados e limitações. Não é necessário publicar em lojas nem construir uma aplicação própria para cumprir este escopo.

### 5.1. O que foi efetivamente verificado

**Nix, 5 de novembro de 2026:** Nix 2.34.9, NixOS em `x86_64-linux`, revisão Nixpkgs `3ec636362e1816bc2f0888fa0fa2c69f1bc9e504`, editor 50.1. A execução automatizada pelo assistente avaliou a configuração, obteve o editor pelo cache e consultou sua versão. Dois perfis selecionaram o mesmo executável; remover em A preservou B; retornar da geração 2 à 1 recuperou A. Um documento alterado por Python permaneceu alterado. Não houve edição pela janela. [Evidências reais](./nix/evidencias/validacao.md).

**Flatpak/Snap, checagem documental:** manifesto Flathub na revisão `5f9138c4ef35c63c58e54a5558f5661d249412a0` declara runtime 51, fonte do editor 51.0 e `--filesystem=host`. API Snap Store consultada para `latest/stable`, amd64, informou editor 48.3, revisão 53, base core24 e metadado strict. São declarações da receita/catálogo; não comprovam instalação, funcionamento ou bloqueios locais. Links consultados e valores estão na [checagem de preparação](./flatpak-snap/evidencias/validacao.md).

### 5.2. Limitações e pendências

- **Debian:** preencher ambiente/versões, executar o piloto e incluir consulta aos arquivos; o PDF ainda contém campos de status sem preenchimento.
- **Ports:** registrar FreeBSD, revisão, opção NLS escolhida, construção e resultado de `hello`; não há medições anexadas.
- **Nix:** concluir a tarefa gráfica e repetição em outra máquina. A cópia para outra pasta usou o mesmo hospedeiro/store. Não foram testadas duas versões, atualização ou confinamento.
- **Flatpak/Snap:** ferramentas e sessão gráfica estavam ausentes na preparação. Executar instalação, consultas de permissões, tarefa gráfica e teste controlado de acesso; registrar a restauração das configurações alteradas.
- **Comparação:** as versões consultadas do editor diferem. Sem controlar versão, plataforma e dependências, o formato não pode ser tratado como a única variável de desempenho.

## 6. Síntese parcial e próximos passos

A pesquisa sustenta escolhas conforme a necessidade: Debian integra ferramentas ao conjunto da distribuição; Ports oferece controle da construção; Nix explicita componentes e seleção por ambientes; Flatpak/Snap organizam distribuição e políticas de acesso de aplicações. São interpretações dos mecanismos, ainda sujeitas aos pilotos.

O único resultado prático consolidado é a seleção independente e recuperação de um perfil Nix, com limites documentados. Os próximos passos são preencher evidências de Debian/Ports, executar os roteiros gráficos e ensaiar na máquina da apresentação. A semana 2 entrega fundamentação e plano consistente; conclusões quantitativas ficam condicionadas aos testes posteriores.

## Referências e materiais de apoio

As fontes primárias estão vinculadas junto às afirmações: Debian Project (FAQ, Policy e manuais APT/dpkg); FreeBSD Project (Handbook, Porter's Handbook e árvore de Ports); Nix/NixOS (manual 2.34 e nix.dev); Flatpak (documentação e manifesto Flathub); Canonical (documentação Snap/Snapcraft e API da loja). **Consulta/consolidação: 5 de novembro de 2026.** Receitas e catálogos são mutáveis: prevalecem as revisões registradas nas evidências.

Os PDFs dos integrantes são materiais fornecidos pelo grupo, preservados em [materiais-integrantes](./materiais-integrantes/), e não substituem fontes técnicas ou prova de execução. Os relatórios específicos de [Nix](./nix/relatorio-nix.md) e [Flatpak/Snap](./flatpak-snap/relatorio-flatpak-snap.md) mantêm o detalhamento das respostas e dos procedimentos.
