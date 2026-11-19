# Roteiro de fala — Semana 01

Apresentação em grupo de quatro pessoas. Dez slides principais, com duração estimada de oito minutos, e um slide de apoio. Os tempos devem ser confirmados em ensaio. A divisão usa Pessoa 1–4 porque os nomes não foram fornecidos.

PowerPoint: as notas também estão no modo do apresentador. HTML: tecla N exibe as notas. Para apresentar sem notas, mantenha-as fechadas e use tela cheia.

## Slide 1 — Gerenciadores de pacotes em Unix/Linux

**Pessoa 1 · 0:00–0:15**

Apresentar o tema e o grupo. Somos quatro integrantes e vamos estudar como gerenciadores de pacotes organizam o software em Unix/Linux, incluindo Debian e FreeBSD. O foco será explicar decisões relacionadas a Sistemas Operacionais por meio de comparações e exemplos. Esta apresentação descreve a proposta; ainda não apresenta resultados de experimentos.

## Slide 2 — Instalar um programa muda o sistema.

**Pessoa 1 · 0:15–1:05**

Começar com uma situação conhecida: instalamos um programa e ele precisa de componentes que não vieram sozinhos. Imagine que dois programas dependam de versões diferentes de uma biblioteca. Precisamos manter ambos funcionando. E, se a atualização for interrompida, precisamos entender o estado que restou. Isso conecta o tema a arquivos, execução de programas e recuperação. Não é necessário usar nomes de chamadas do kernel para explicar esse problema.

## Slide 3 — Cinco representantes, quatro famílias.

**Pessoa 1 · 1:05–1:50**

O recorte passa a ter cinco representantes em quatro famílias. Para binários tradicionais mutáveis, usaremos apenas APT e dpkg no Debian. Para código-fonte, a coleção de Ports do FreeBSD, que orienta a construção do software. No modelo funcional e imutável, apenas Nix. Na distribuição com sandbox, Flatpak e Snap. Os nomes entre parênteses indicam tecnologias que serão explicadas por sua função. Como incluímos FreeBSD, o tema agora abrange Unix/Linux; não vamos presumir que todos os exemplos compartilham o kernel Linux.

## Slide 4 — Pacote pronto ou código-fonte?

**Pessoa 2 · 1:50–2:50**

No Debian, APT e dpkg obtêm e instalam pacotes binários já preparados. No FreeBSD Ports, receitas coordenam obtenção do código-fonte, configuração, compilação e instalação. Isso permite discutir escolhas de construção e o trabalho adicional de CPU, memória e arquivos temporários. Não significa que compilar sempre deixe o programa mais rápido. APT/dpkg e Ports são os representantes escolhidos; o FreeBSD também possui distribuição binária, mas ela não é um representante adicional deste trabalho. Comparar esses tempos exige cuidado: construir e extrair um binário são operações diferentes, executadas em sistemas distintos.

## Slide 5 — Nix: versões e recuperação.

**Pessoa 2 · 2:50–3:50**

Nix organiza resultados de construção em caminhos próprios e os trata como imutáveis. Diferentes variantes podem coexistir, e os perfis selecionam um conjunto de software. Isso favorece ambientes controlados e permite voltar a uma geração preservada. Imutabilidade não significa que todo o computador se tornou somente leitura. A construção pode usar fontes ou aproveitar binários em cache. A comparação com Debian é a organização das versões e o alcance da recuperação. Se uma aplicação alterou um banco de dados, retornar ao perfil anterior não desfaz automaticamente essa mudança.

## Slide 6 — Flatpak e Snap: controle de acesso.

**Pessoa 3 · 3:50–4:55**

Usar o exemplo de um editor: ele precisa do documento escolhido, mas não necessariamente de todos os arquivos do usuário. No Flatpak, OSTree organiza e distribui árvores de arquivos; Bubblewrap monta o ambiente isolado, com permissões e portais mediando o acesso. No Snap, SquashFS armazena a aplicação em uma imagem comprimida e somente para leitura; AppArmor aplica políticas de acesso, enquanto cgroups permitem contabilizar e, quando configurado, limitar recursos. O confinamento depende do modo e do suporte do ambiente. Armazenar arquivos e proteger processos são funções distintas; não precisamos detalhar as chamadas internas para explicá-las.

## Slide 7 — Critérios da comparação.

**Pessoa 3 · 4:55–5:50**

As mesmas perguntas orientarão os cinco representantes. Debian versus Ports permite discutir instalação binária e construção local. Debian versus Nix ajuda a discutir versões e recuperação. Flatpak versus Snap permite discutir distribuição e permissões. Recursos entram como uma consequência a observar: o primeiro aplicativo pode precisar de dependências extras que outro reaproveita. Não estabelecer um ranking antecipado nem atribuir toda diferença ao gerenciador.

## Slide 8 — Quatro famílias, quatro exemplos.

**Pessoa 4 · 5:50–6:50**

O estudo documental abrange os cinco representantes. A prática organiza um exemplo por família: arquivos e dependências no Debian; etapas de construção de um port pequeno no FreeBSD; perfis no Nix; e permissões no Flatpak, contrastadas com o modelo Snap. São exemplos planejados, sujeitos a validação. FreeBSD requer ambiente próprio, como uma máquina virtual; não roda como um container Linux comum. Se o ambiente não estiver disponível, o exemplo Ports pode ser explicado documentalmente. Tempo e disco serão apoio, sem comparar diretamente compilação, extração e ativação de perfil como se fossem a mesma tarefa.

## Slide 9 — Entregas previstas por semana.

**Pessoa 4 · 6:50–7:35**

Apresentar apenas as entregas previstas. Semana 1: apresentação oral da proposta com tema, escopo e objetivos. Semana 2: relatório parcial 1 e slides com revisão e plano de testes. Semana 3: apresentação oral 2 com demonstrações das quatro famílias. Semana 4: relatório parcial 2 e slides com comparações e medidas. Semana 5: relatório final e slides com resultados, limites e conclusões. Estes são os marcos do cronograma do projeto. A divisão de tarefas entre integrantes não aparece neste slide.

## Slide 10 — Que escolhas fazem sentido em cada contexto?

**Pessoa 4 · 7:35–8:00**

Encerrar retomando o objetivo: construir uma comparação fundamentada que ajude a entender como o software é organizado, atualizado e executado sob as regras do sistema operacional. Esperamos entregar fichas comparativas, exemplos das quatro famílias e uma discussão de vantagens, custos e limites em contextos específicos. Não há um vencedor universal proposto. A contribuição é relacionar as decisões dos gerenciadores aos conceitos da disciplina. Agradecer e abrir espaço para perguntas.

## Slide 11 — Panorama dos cinco representantes.

**Apoio · Fora dos 8 minutos**

Este slide é de apoio. Cada linha corresponde a um representante selecionado. Debian representa binários tradicionais mutáveis; FreeBSD Ports, construção a partir de fontes; Nix, organização funcional e imutável; Flatpak e Snap, distribuição de aplicações com mecanismos de isolamento. O foco é relacionar decisões a custos e garantias de SO, sem tratar famílias como equivalentes nem apresentar um ranking. A coleção de Ports utiliza receitas: não confundi-la com o gerenciador binário do FreeBSD.

## Fontes

- [[1] Debian — Pacotes binários, arquivos e dependências.](https://www.debian.org/doc/manuals/debian-handbook/sect.package-meta-information.en.html)
- [[2] FreeBSD Ports — Receitas, configuração e compilação de software.](https://docs.freebsd.org/en/books/handbook/ports/)
- [[3] Nix — Variantes, imutabilidade e perfis.](https://nix.dev/manual/nix/latest/introduction)
- [[4] Flatpak — OSTree, distribuição e tecnologias utilizadas.](https://docs.flatpak.org/en/latest/under-the-hood.html)
- [[5] Bubblewrap — Ferramenta de isolamento usada pelo Flatpak.](https://github.com/containers/bubblewrap)
- [[6] Snap: arquitetura — Imagens SquashFS e revisões da aplicação.](https://snapcraft.io/docs/reference/system-architecture/)
- [[7] Snap: segurança — Políticas de acesso e mecanismos de proteção.](https://snapcraft.io/docs/explanation/security/security-policies/)
- [[8] Snap: recursos — Quotas e limites configuráveis de recursos.](https://snapcraft.io/docs/how-to-guides/manage-snaps/use-resource-quotas/)
