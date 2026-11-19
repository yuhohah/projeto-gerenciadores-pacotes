# Roteiro de fala — Semana 02

Apresentação em grupo de quatro pessoas. Quinze slides principais, com duração estimada de 11 minutos e 30 segundos, e dois slides de apoio. Os tempos devem ser confirmados em ensaio. A divisão usa Integrante 1–4 porque os nomes não foram fornecidos.

PowerPoint: as notas também estão no modo do apresentador. HTML: tecla N exibe as notas. Para apresentar sem notas, mantenha-as fechadas e use tela cheia.

## Slide 1 — Gerenciadores de pacotes em Unix/Linux

**Integrante 1 · 0:00–0:15**

Apresentar a etapa: fundamentação e preparação dos exemplos da semana 2. O recorte permanece Debian com APT/dpkg, FreeBSD Ports, Nix, Flatpak e Snap. Esta apresentação consolida os materiais dos quatro integrantes. Há uma validação de Nix pelo terminal no ambiente de preparação; os demais procedimentos ainda exigem pilotos. A data dos registros é 5 de novembro de 2026. Os nomes do grupo não foram fornecidos, por isso a divisão aparece apenas nas notas como Integrante 1–4.

## Slide 2 — O que muda para o sistema operacional?

**Integrante 1 · 0:15–0:50**

Explicar as perguntas comuns sem entrar em mecanismos internos. Instalar um programa envolve escolher componentes, colocar arquivos em locais conhecidos e definir como o processo será executado. A comparação vai observar arquivos, dependências, atualizações e recuperação, proteção e uso de recursos. Perguntar pela situação de uso é mais útil do que antecipar uma ferramenta vencedora.

## Slide 3 — Debian: duas funções complementares.

**Integrante 1 · 0:50–1:35**

APT consulta repositórios, calcula uma solução para dependências e obtém os arquivos necessários. dpkg desempacota, configura e mantém o registro dos pacotes. APT/dpkg formam um único representante do trabalho. O dpkg verifica dependências, mas não vai buscá-las e instalá-las sozinho. apt update atualiza índices e é uma operação separada de apt install. APT pode usar fontes em sources.list e arquivos de sources.list.d. Uma atualização altera o conjunto instalado; escolher uma versão ou definir pinning não cria, por si só, ambientes separados por projeto.

Fontes: https://www.debian.org/doc/manuals/debian-faq/pkgtools.en.html; https://manpages.debian.org/trixie/apt/apt_preferences.5.en.html

## Slide 4 — Debian: arquivos e dependências.

**Integrante 1 · 1:35–2:15**

O material do integrante 1 escolheu tmux como exemplo. O estado de execução estava em aberto no PDF; não foram fornecidos logs ou a versão do Debian. O piloto está planejado. Instalar o programa, consultar dependências e observar os arquivos registrados. Em dpkg -l, interpretar o estado, não apenas a presença do nome. dpkg -L lista arquivos do pacote; dpkg -S permite consultar a qual pacote um arquivo pertence. Mostrar duas ou três linhas e explicar seu significado. Não é necessário colocar todas as saídas no slide. Para projetos incompatíveis, o controle de versões do pacote não substitui uma solução de ambiente independente.

Fontes: https://manpages.debian.org/trixie/dpkg/dpkg-query.1.en.html; https://manpages.debian.org/trixie/apt/apt_preferences.5.en.html

## Slide 5 — Ports: da receita ao programa instalado.

**Integrante 2 · 2:15–3:00**

O port é a receita, e não o programa já compilado. O framework coordena obtenção e verificação das fontes, extração, patches, configuração, construção, staging, geração e instalação do pacote. A sequência no slide agrupa fases para facilitar a explicação. Os arquivos de trabalho são temporários; o pacote instalado e os distfiles têm outros ciclos de vida. make install clean encadeia os alvos necessários e limpa a área de trabalho. FreeBSD utiliza seu próprio ambiente: uma VM com FreeBSD é uma opção para o piloto. O uso de pkg como ferramenta de registro ou instalação não adiciona outro representante ao recorte.

Fontes: https://docs.freebsd.org/en/books/handbook/ports/; https://docs.freebsd.org/en/books/porters-handbook/slow-porting/

## Slide 6 — Ports: personalizar tem um custo.

**Integrante 2 · 3:00–3:45**

O material do integrante 2 escolheu misc/hello, um programa pequeno. A receita consultada oferece NLS, suporte a idiomas. O piloto deve verificar a opção na árvore de Ports utilizada, registrar seu estado e acompanhar uma construção. A escolha fornece um exemplo concreto de personalização sem exigir detalhes de ABI, hardening, poudriere ou jails na apresentação. Registrar FreeBSD, arquitetura, revisão da árvore e opções. O custo envolve fontes, dependências, CPU, memória e arquivos temporários. A obtenção de um binário pronto evita a construção local, mas não permite concluir menor manutenção em todas as situações. Nenhum resultado medido de Ports foi fornecido.

Fontes: https://docs.freebsd.org/en/books/handbook/ports/; https://cgit.freebsd.org/ports/tree/misc/hello/Makefile

## Slide 7 — Nix: armazenar, selecionar e recuperar.

**Integrante 3 · 3:45–4:30**

O store guarda resultados de construção em caminhos próprios. Os perfis selecionam referências aos programas; gerações registram estados de um perfil. O modelo permite coexistência de variantes, mas ter dois perfis não comprova duas versões diferentes. Arquivos de configuração e revisão fixa ajudam a repetir um ambiente. O exemplo inclui flake.nix e flake.lock. Nix pode obter binários em cache; não é obrigatório compilar tudo localmente. A imutabilidade dos resultados do store não torna documentos do usuário imutáveis nem confina automaticamente o editor.

Fontes: https://nix.dev/manual/nix/2.34/package-management/profiles.html; https://nix.dev/tutorials/first-steps/towards-reproducibility-pinning-nixpkgs

## Slide 8 — Nix: o que foi validado pelo terminal.

**Integrante 3 · 4:30–5:20**

Validação de preparação feita pelo assistente em 5 de novembro de 2026, não apresentação executada pelos integrantes. Nix 2.34.9 no NixOS x86_64-linux, GNOME Text Editor 50.1 e revisão fixa da coleção de pacotes. Os perfis A e B selecionaram o mesmo executável. Remover de A não alterou B. O retorno à geração anterior recuperou a seleção de A. Um documento alterado por Python permaneceu alterado; a edição não foi realizada pela janela. Foi repetida a obtenção numa cópia em outra pasta da mesma máquina. Não foram demonstradas duas versões diferentes, atualização entre versões, abertura gráfica ou repetição em outro computador. Evidências: semana-02/nix/evidencias/validacao.md.

Fontes: https://nix.dev/manual/nix/2.34/package-management/profiles.html

## Slide 9 — Flatpak: dependências e acesso.

**Integrante 4 · 5:20–6:10**

O manifesto descreve como construir a aplicação, suas dependências e permissões. O runtime oferece uma base compartilhável; componentes adicionais podem acompanhar a aplicação. O SDK fornece ferramentas de construção. OSTree administra conteúdo versionado, e Bubblewrap participa da criação do ambiente isolado. Os portais mediam operações como escolher um arquivo. O isolamento efetivo depende da política do pacote e das configurações locais. A receita consultada do GNOME Text Editor declara filesystem=host: não devemos presumir bloqueio da pasta pessoal. A fonte 51.0 no manifesto não comprova a versão instalada ou disponível a todas as arquiteturas. Não houve instalação ou execução de Flatpak neste ambiente.

Fontes: https://docs.flatpak.org/en/latest/basic-concepts.html; https://docs.flatpak.org/en/latest/sandbox-permissions.html; https://docs.flatpak.org/en/latest/under-the-hood.html

## Slide 10 — Snap: imagem e regras de execução.

**Integrante 4 · 6:10–7:00**

O Snapcraft produz o pacote a partir de snapcraft.yaml. O snapd administra instalação e revisões. SquashFS armazena o pacote numa imagem comprimida e somente leitura, montada ao instalar a revisão. Não se monta toda a imagem de novo a cada lançamento. AppArmor participa da aplicação das políticas; interfaces concedem acessos. cgroups agrupam processos e apoiam controles: quotas configuradas para serviços não significam um limite automático de CPU ou memória para todo editor. Strict, classic e devmode têm alcances diferentes, e o suporte do hospedeiro precisa ser conferido. A consulta ao catálogo para amd64 registrou editor 48.3, revisão 53, base core24 e metadado strict; isso não comprova confinamento efetivo numa máquina. Não houve execução de Snap neste ambiente.

Fontes: https://snapcraft.io/docs/reference/system-architecture/; https://snapcraft.io/docs/explanation/security/snap-confinement/; https://snapcraft.io/docs/how-to-guides/manage-snaps/use-resource-quotas/

## Slide 11 — Quatro VMs para os testes.

**Integrante 1 · 7:00–8:00**

Apresentar a organização planejada: as VMs ainda precisam ser preparadas e validadas. VM 1: Debian com APT/dpkg para instalar pacotes, consultar dependências e observar os arquivos. VM 2: FreeBSD com Ports para escolher uma opção e acompanhar a construção do software. VM 3: a mesma base Debian com Nix para selecionar ambientes e testar a recuperação de perfis. A validação anterior de Nix ocorreu em NixOS; ela não comprova execução nessa nova VM. VM 4: Debian com dois estados separados, um para Flatpak e outro para Snap, para observar permissões e acesso ao mesmo documento. Restaurar a base limpa antes de preparar o outro cenário e preservar um estado anterior à instalação da aplicação em cada um. Usar o mesmo computador, hipervisor e orçamento de hardware virtual, executando uma VM por vez. Registrar as diferenças de sistema e versões: o cenário Ports também inclui as diferenças entre FreeBSD e Linux. Restaurar um snapshot organiza o experimento; não é uma evidência de rollback oferecido pelo gerenciador. Quatro VMs cobrem os cinco representantes porque Flatpak e Snap serão testados separadamente na quarta VM.

Fontes: https://nix.dev/install-nix.html; https://docs.freebsd.org/en/books/handbook/ports/; https://docs.flatpak.org/en/latest/sandbox-permissions.html; https://snapcraft.io/docs/explanation/security/snap-confinement/

## Slide 12 — Como organizar a comparação prática?

**Integrante 2 · 8:00–9:00**

A tarefa comum proposta usa GNOME Text Editor: abrir comparacao.txt, editar, salvar outro arquivo e reabrir. A disponibilidade foi pesquisada para os cinco representantes, mas a execução precisa ser validada em cada ambiente. No FreeBSD, a dependência de uma sessão gráfica e o custo de construir bibliotecas podem dificultar o piloto. Os materiais de Debian e Ports já propõem tmux e hello: eles permanecem como ilustrações dos mecanismos. É possível comparar estrutura com programas diferentes, mas não usar os seus tempos ou tamanhos como ranking direto. Se o editor não for viável, registrar a limitação e definir exemplos comuns por comparação antes das medidas. Comparar preparação, compilação e ativação como etapas distintas.

## Slide 13 — Pesquisa, validação e pendências.

**Integrante 3 · 9:00–10:00**

Relatar o estado do material, não afirmar que o grupo terminou os testes. Debian e Ports: os PDFs forneceram fundamentação e exemplos planejados, sem registros suficientes para confirmar execução. Nix: há validação pelo terminal no ambiente de preparação; tarefa gráfica e outro computador pendentes. Flatpak e Snap: receitas, catálogo e documentação conferidos; ferramentas ausentes e nenhuma execução neste ambiente. A checagem documental não é um teste de permissões. Ainda não existe uma bateria comparativa de tempo, CPU, RAM ou disco entre os gerenciadores. As versões de editor também diferem nas fontes consultadas.

## Slide 14 — Da preparação às conclusões.

**Integrante 4 · 10:00–11:00**

Semana 2: fundamentação e plano consolidados nesta entrega. Na semana 3, ensaiar e demonstrar os exemplos das quatro famílias, registrar ambiente e versões e guardar saídas reais. Na semana 4, executar as comparações definidas em condições registradas e interpretar custos por etapa. Na semana 5, reunir resultados, limites e recomendações por necessidade. Cada integrante executa seu piloto e outro revisa as instruções. Não é necessário acrescentar ferramentas ao recorte. Se um ambiente ficar indisponível, declarar a parte documental e limitar a conclusão prática.

## Slide 15 — A escolha depende da tarefa.

**Integrante 4 · 11:00–11:30**

Concluir que as decisões dos gerenciadores afetam armazenamento, compatibilidade, manutenção e proteção. O trabalho já possui fundamentação e exemplos definidos, mas ainda precisa completar os pilotos e a comparação controlada. Para quem desenvolve software, distinguir preparar ferramentas de um projeto e distribuir uma aplicação. Uma recomendação deve indicar necessidade, benefício e custo, apoiada em fontes e evidências. Encerrar e abrir para perguntas; os dois slides seguintes são de apoio e não fazem parte do tempo principal.

## Slide 16 — Como registrar cada teste?

**Apoio · Fora do tempo principal**

Um registro útil permite repetir o procedimento: responsável, data, sistema, arquitetura, versões, fontes e revisões, comandos com saída e interpretação. Para medir, registrar estado inicial, caches, dependências já presentes e acesso à rede. Separar download, compilação, instalação e execução. Guardar valores individuais antes de resumir. Não confundir fechamento de dependências com crescimento exclusivo do disco. Em Nix, o fechamento consultado incluía componentes compartilhados já existentes; ele não representa todo o espaço novo causado pela instalação.

## Slide 17 — Recuperar software e recuperar dados.

**Apoio · Fora do tempo principal**

Detalhar o alcance de recuperação. Nix: retornar um perfil seleciona uma geração preservada e não reverte documentos. Flatpak: selecionar um commit anterior exige sua disponibilidade e não desfaz automaticamente alterações em documentos. Snap: revert pode recuperar uma revisão preservada e dados/configuração associados à revisão; common e documentos externos não são automaticamente revertidos. Debian/Ports não oferecem, por esse fluxo básico de instalação, uma restauração completa de todos os dados: disponibilidade de versões, compatibilidade e backups precisam ser avaliados. Não há teste comparativo de recuperação entre todos os gerenciadores nesta preparação.

Fontes: https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-profile-rollback.html; https://docs.flatpak.org/en/latest/flatpak-command-reference.html#flatpak-update; https://snapcraft.io/docs/how-to-guides/manage-snaps/manage-updates/

## Fontes

- [Debian: APT e dpkg — Papéis das ferramentas e instalação.](https://www.debian.org/doc/manuals/debian-faq/pkgtools.en.html)
- [Debian: consultas — Arquivos instalados e metadados.](https://manpages.debian.org/trixie/dpkg/dpkg-query.1.en.html)
- [Debian: versões — Escolha de versões e prioridades.](https://manpages.debian.org/trixie/apt/apt_preferences.5.en.html)
- [FreeBSD Ports — Construção, configuração e instalação.](https://docs.freebsd.org/en/books/handbook/ports/)
- [FreeBSD: etapas — Fluxo de construção do port.](https://docs.freebsd.org/en/books/porters-handbook/slow-porting/)
- [FreeBSD: hello — Receita e opção NLS.](https://cgit.freebsd.org/ports/tree/misc/hello/Makefile)
- [Nix — Perfis e gerações.](https://nix.dev/manual/nix/2.34/package-management/profiles.html)
- [Flatpak — Dependências e runtimes.](https://docs.flatpak.org/en/latest/basic-concepts.html)
- [Flatpak: permissões — Acesso a arquivos e portais.](https://docs.flatpak.org/en/latest/sandbox-permissions.html)
- [Snap — Arquitetura e armazenamento.](https://snapcraft.io/docs/reference/system-architecture/)
- [Snap: confinamento — Modos e interfaces.](https://snapcraft.io/docs/explanation/security/snap-confinement/)
- [Snap: recursos — Quotas configuráveis para serviços.](https://snapcraft.io/docs/how-to-guides/manage-snaps/use-resource-quotas/)
