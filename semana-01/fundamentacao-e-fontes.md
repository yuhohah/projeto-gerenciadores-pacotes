# Fundamentação e fontes

Este documento consolida os conceitos e as ressalvas úteis ao recorte atual. As [fontes da apresentação](./slides/roteiro-de-fala.md#fontes) também estão disponíveis no roteiro.

## Instalação, dependências e arquivos

Um pacote reúne software e metadados para sua administração. No Debian, APT coordena seleção e obtenção; dpkg realiza operações locais sobre pacotes Debian. Dependências indicam componentes necessários e restrições de compatibilidade. A escolha dos pacotes durante a instalação e a procura das bibliotecas durante a execução são etapas diferentes.

O FHS é uma convenção de organização de diretórios; não é um componente do kernel. O gerenciador funciona em espaço de usuário e solicita serviços ao sistema operacional.

Fontes: [Debian: metadados dos pacotes](https://www.debian.org/doc/manuals/debian-handbook/sect.package-meta-information.en.html), [Debian Policy](https://www.debian.org/doc/debian-policy/), [FHS 3.0](https://refspecs.linuxfoundation.org/FHS_3.0/fhs-3.0.pdf).

## Construção a partir de fontes

A coleção de Ports do FreeBSD utiliza receitas para configurar, construir e instalar software. Compilar acrescenta trabalho de CPU, memória e arquivos temporários, e não garante que o programa resultante seja mais rápido. Comparar esse processo com a instalação de um binário exige distinguir as tarefas realizadas.

Fonte: [FreeBSD Handbook: Packages and Ports](https://docs.freebsd.org/en/books/handbook/ports/).

## Nix e recuperação

Nix organiza resultados em caminhos próprios e trata os objetos válidos como imutáveis. Variantes podem coexistir, e perfis selecionam um ambiente. O modelo pode aproveitar fontes ou binários previamente construídos.

Imutabilidade dos resultados não torna todo o computador somente para leitura. O controle das entradas favorece reprodutibilidade, mas não garante identidade binária em qualquer construção. Retornar a uma geração preservada não desfaz automaticamente alterações em documentos ou bancos de dados das aplicações.

Fontes: [introdução ao Nix](https://nix.dev/manual/nix/latest/introduction), [perfis e gerações](https://nix.dev/manual/nix/2.34/package-management/profiles.html), [NixOS Reproducible Builds](https://reproducible.nixos.org/).

## Distribuição de aplicações e proteção

No Flatpak, OSTree participa da organização e distribuição dos arquivos; Bubblewrap prepara o ambiente isolado. Permissões e portais mediam interações com recursos externos.

No Snap, SquashFS fornece imagens comprimidas e somente para leitura; AppArmor aplica políticas de acesso. cgroups permitem contabilizar e, quando configurado, limitar recursos. O confinamento depende do modo usado e do suporte do ambiente. Não se deve atribuir a cada lançamento uma nova montagem completa da imagem.

Formato de armazenamento, isolamento de construção e proteção durante a execução são propriedades distintas. A organização do Nix não equivale à sandbox de execução do Flatpak. Retornar a um commit ou revisão não significa restaurar todos os dados mutáveis.

Fontes: [Flatpak: tecnologias utilizadas](https://docs.flatpak.org/en/latest/under-the-hood.html), [permissões Flatpak](https://docs.flatpak.org/en/latest/sandbox-permissions.html), [Bubblewrap](https://github.com/containers/bubblewrap), [arquitetura Snap](https://snapcraft.io/docs/reference/system-architecture/), [confinamento Snap](https://snapcraft.io/docs/explanation/security/snap-confinement/), [quotas de recursos Snap](https://snapcraft.io/docs/how-to-guides/manage-snaps/use-resource-quotas/).

## Consistência e medições

Atomicidade de uma substituição de caminho não implica uma instalação inteira atômica nem persistência após queda de energia. É preciso definir qual estado está sendo protegido ou recuperado. Da mesma forma, entrar no kernel por uma syscall não equivale necessariamente a trocar o processo em execução.

O número de syscalls, sozinho, não estabelece desempenho. Instrumentação também interfere na execução; medições de um cliente podem excluir trabalho de daemons externos. Conclusões devem se limitar aos cenários observados.

Fontes: [rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html), [fsync(2)](https://man7.org/linux/man-pages/man2/fsync.2.html), [getrusage(2)](https://man7.org/linux/man-pages/man2/getrusage.2.html), [strace(1)](https://man7.org/linux/man-pages/man1/strace.1.html).

## Referências acadêmicas preservadas

- DOLSTRA, Eelco; DE JONGE, Merijn; VISSER, Eelco. [Nix: A Safe and Policy-Free System for Software Deployment](https://www.usenix.org/conference/lisa-04/nix-safe-and-policy-free-system-software-deployment). LISA, 2004, p. 79–92.
- DOLSTRA, Eelco. [The Purely Functional Software Deployment Model](https://edolstra.github.io/pubs/phd-thesis.pdf). Tese de doutorado, Utrecht University, 2006.
