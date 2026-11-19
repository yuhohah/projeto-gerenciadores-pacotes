# Roteiro de fala — Semana 04

Apresentação em grupo de quatro pessoas. 12 slides principais (incluindo o Slide 5 em branco reservado para o vídeo), com duração estimada de ~10 minutos e 15 segundos, e 1 slide de apoio. Os tempos devem ser confirmados em ensaio. A divisão usa Integrante 1–4 porque os nomes não foram fornecidos.

PowerPoint: as notas também estão no modo do apresentador. HTML: tecla N exibe as notas. Para apresentar sem notas, mantenha-as fechadas e use tela cheia.

## Slide 1 — Gerenciadores de pacotes em Unix/Linux

**Integrante 1 · 0:00–0:20**

Apresentar a entrega da Semana 4: primeiro explicaremos a metodologia experimental no NixOS e a validade de cada medição usando um único programa (GNU hello); em seguida mostraremos o vídeo prático dos testes; por fim, apresentaremos os resultados simplificados em comparações diretas entre os métodos de instalar e executar um programa.

## Slide 2 — Metodologia: um programa único sob controle.

**Integrante 1 · 0:20–1:10**

Explicar o desenho experimental. Para comparar gerenciadores sem misturar diferenças de tamanho ou bibliotecas gráficas, fixamos um único programa de referência: o GNU hello, que depende apenas da libc.so.6 e possui 46 traduções (.mo). Todas as medições rodam no mesmo computador (Ryzen 5 2600, 15 GiB RAM, NVMe, NixOS 26.11, Linux 7.3.4), com arquivos já em cache local para zerar efeito de rede, 3 repetições por operação e rastreamento de syscalls (strace -fc) em passe separado.

## Slide 3 — Como testar os quatro métodos no mesmo NixOS?

**Integrante 1 · 1:10–2:00**

Responder se tudo rodou em container: não. Apenas o Debian rodou em container Linux (debian:trixie-slim), pois o NixOS não possui /usr/bin nem /var/lib/dpkg globais; o container fornece apenas a árvore FHS sobre o mesmo kernel Linux 7.3.4, sem VM. Já o Nix (2.35.6), OSTree (Flatpak), Bubblewrap e SquashFS (Snap) rodam 100% nativos no host. Para o FreeBSD Ports, inspecionamos a receita oficial misc/hello e compilamos o mesmo tarball oficial nativamente no host.

## Slide 4 — Validade das medições e limites conhecidos.

**Integrante 1 · 2:00–2:50**

Explicar o que cada teste prova com 100% de rigor e onde existem ressalvas metodológicas. Propriedades estáticas (.deb, árvores de arquivos, cabeçalhos ELF e receita misc/hello) têm validade 100% exata. Nix, OSTree, Bubblewrap e SquashFS têm validade 100% nativa sobre ext4 e NVMe. No container Debian, as 2.478 syscalls do dpkg vão direto ao kernel 7.3.4, com a ressalva de a raiz usar OverlayFS. No build do hello, a economia de 51,6% ao desativar NLS é idêntica ao port, mas o tempo de compilação pertence ao toolchain Linux/GCC.

## Slide 5 — Slide em branco — Vídeo demonstrativo

**Todos · 2:50–4:20**

[Slide em branco reservado para inserção do vídeo demonstrativo dos testes práticos.]

## Slide 6 — Onde o programa fica e como acha a libc?

**Integrante 2 · 4:20–5:15**

Primeira comparação após o vídeo: como cada método guarda o GNU hello no disco e resolve a libc.so.6. No Debian (FHS), o binário vai para /usr/bin/hello e o ELF não tem RUNPATH, buscando a biblioteca global do sistema. Na compilação tipo Ports, vai para um prefixo local (/usr/local) e usa a libc do sistema. No Nix, o programa fica isolado em /nix/store/<hash>-hello e grava um RUNPATH fixo no ELF apontando para sua glibc exata. No Flatpak e Snap, versões iguais compartilham inodes via OSTree (10495848) ou ficam compactadas em uma imagem .snap isolada.

Fontes: https://www.debian.org/doc/manuals/debian-faq/pkgtools.en.html; https://nix.dev/manual/nix/2.34/store/store-path.html; https://docs.flatpak.org/en/latest/under-the-hood.html

## Slide 7 — Quanto custa instalar ou preparar o programa?

**Integrante 2 · 5:15–6:10**

Segunda comparação: o custo em tempo e chamadas de sistema para disponibilizar o GNU hello. Instalar o pacote binário pronto no Debian (dpkg -i) levou 37,3 ms com 2.478 syscalls. Ativar o pacote já existente no store do Nix (nix profile add) levou 41,3 ms e 3.617 syscalls. Empacotar em imagem .snap com zstd levou 37,7 ms (e 10,1 ms para extrair). Já compilar o mesmo hello do código-fonte exigiu 19.840 ms (cerca de 530x mais lento) e 2.467.256 syscalls (~1.000x mais chamadas, incluindo 4.261 execve).

Fontes: https://manpages.debian.org/trixie/dpkg-dev/deb.5.en.html; https://docs.freebsd.org/en/books/porters-handbook/slow-porting/; https://nix.dev/manual/nix/2.34/package-management/profiles.html

## Slide 8 — Quanto espaço ocupa e dá para enxugar?

**Integrante 3 · 6:10–7:05**

Terceira comparação: tamanho em disco e flexibilidade de personalização. O .deb pronto instala 188 KiB fixos no FHS (51,4 KiB baixados). Compilar do fonte gasta 7,45 MiB temporários e gera 400,8 KiB em 50 arquivos com NLS, mas permite desativar NLS e cortar para 193,8 KiB em 4 arquivos (-51,6% de espaço). No Nix, o pacote hello tem 273,0 KiB próprios (NAR) e closure de 36,7 MiB com glibc compartilhada. No OSTree, duas versões dividem o mesmo inode (0 B extra no binário) e o SquashFS comprime a árvore de 246,7 KiB para 64,0 KiB (xz).

Fontes: https://cgit.freebsd.org/ports/tree/misc/hello/Makefile; https://nix.dev/manual/nix/2.34/store/store-path.html; https://docs.flatpak.org/en/latest/under-the-hood.html; https://snapcraft.io/docs/reference/system-architecture/

## Slide 9 — Rodar direto no sistema vs. isolado em sandbox.

**Integrante 3 · 7:05–8:00**

Quarta comparação: o custo e os requisitos de executar o programa. Executar o hello diretamente no Debian levou 2,00 ms, e no NixOS levou 3,28 ms — com acesso normal ao usuário. Executá-lo isolado via Bubblewrap (motor do Flatpak, com --unshare-all) levou 7,78 ms: apenas +4,50 ms e 963 syscalls (1 unshare, 17 mount, 2 pivot_root), bloqueando leituras sem bind e bloqueando escrita sob --ro-bind. Já a leitura de /sys/kernel/security/lsm revelou ausência de AppArmor no host, mostrando que o confinamento do Snap depende desse módulo no kernel.

Fontes: https://docs.flatpak.org/en/latest/sandbox-permissions.html; https://snapcraft.io/docs/explanation/security/snap-confinement/

## Slide 10 — Atualização e rollback: como voltar atrás?

**Integrante 4 · 8:00–8:50**

Quinta comparação: o que acontece ao atualizar ou desfazer uma instalação. No Debian, o dpkg altera o FHS in-place com travas fcntl, fsync e rename; voltar atrás exige reinstalar a versão anterior. Na compilação via Ports, uma nova versão sobrescreve ou reconstrói arquivos sem histórico nativo de gerações. No Nix, o rollback do hello levou 34,7 ms e 3.525 syscalls, trocando apenas 1 symlink e 1 rename sem tocar nos binários nem chamar fsync de pacote. No Flatpak (OSTree) e no Snap, versões antigas ficam preservadas por commits ou imagens anteriores.

Fontes: https://manpages.debian.org/trixie/dpkg-dev/deb.5.en.html; https://nix.dev/manual/nix/2.34/package-management/profiles.html; https://docs.flatpak.org/en/latest/under-the-hood.html; https://snapcraft.io/docs/reference/system-architecture/

## Slide 11 — Síntese: o que cada método troca na prática.

**Integrante 4 · 8:50–9:45**

Fechar a comparação dos resultados resumindo a troca de Sistemas Operacionais de cada método de usar um programa. O Debian prioriza rapidez e simplicidade (37,3 ms, 188 KiB), abrindo mão de isolamento e rollback atômico. O modelo Ports/Fonte prioriza controle fino do binário (-51,6% sem NLS), pagando o alto custo de compilação local (19,8 s). O Nix prioriza reprodutibilidade e rollback instantâneo (34,7 ms) via store imutável e RUNPATH. O Flatpak e o Snap priorizam isolamento e entrega autocontida (+4,5 ms no sandbox), diferenciando-se pela portabilidade de namespaces no Flatpak contra a exigência de AppArmor no Snap.

## Slide 12 — Metodologia validada e comparações claras.

**Integrante 4 · 9:45–10:15**

Encerrar reforçando que fixar o GNU hello, explicitar o papel do NixOS como hospedeiro único e colocar os resultados em comparações diretas após a demonstração em vídeo deixa nítido o impacto real de cada método de SO. A bateria com pacotes maiores já está reservada para a apresentação final da Semana 5. Abrir para perguntas.

## Slide 13 — Apoio: números exatos e syscalls (GNU hello).

**Apoio · Fora do tempo principal**

Slide de apoio para eventuais perguntas da banca com todas as médias (3 repetições) e totais de syscalls (strace -fc) medidos no GNU hello: Debian dpkg -i (37,33 ms; 2.478 syscalls), Build com/sem NLS (19.840 ms / 2.467.256 vs. 19.288 ms / 2.382.742 syscalls), Nix add/rollback (41,28 ms / 3.617 vs. 34,70 ms / 3.525 syscalls) e Bubblewrap bwrap (7,78 ms; 963 syscalls).

## Fontes

- [Debian: APT e dpkg — Papéis das ferramentas e instalação.](https://www.debian.org/doc/manuals/debian-faq/pkgtools.en.html)
- [Debian: formato deb(5) — Estrutura interna de pacotes binários Debian.](https://manpages.debian.org/trixie/dpkg-dev/deb.5.en.html)
- [Debian: consultas dpkg-query — Arquivos instalados, status e metadados.](https://manpages.debian.org/trixie/dpkg/dpkg-query.1.en.html)
- [FreeBSD Ports — Construção, configuração e instalação.](https://docs.freebsd.org/en/books/handbook/ports/)
- [FreeBSD: etapas do port — Fluxo fetch, extract, patch, configure, build e stage.](https://docs.freebsd.org/en/books/porters-handbook/slow-porting/)
- [FreeBSD: misc/hello — Receita oficial e opção NLS.](https://cgit.freebsd.org/ports/tree/misc/hello/Makefile)
- [Nix: perfis e gerações — Seleção por links simbólicos e rollback.](https://nix.dev/manual/nix/2.34/package-management/profiles.html)
- [Nix: caminhos do store — Endereçamento por hash e isolamento de dependências.](https://nix.dev/manual/nix/2.34/store/store-path.html)
- [Flatpak: arquitetura interna — OSTree, deduplicação por hardlinks e Bubblewrap.](https://docs.flatpak.org/en/latest/under-the-hood.html)
- [Flatpak: permissões da sandbox — Acesso a arquivos, overrides e portais.](https://docs.flatpak.org/en/latest/sandbox-permissions.html)
- [Snap: arquitetura e formato SquashFS — Imagens somente leitura, revisões e canais.](https://snapcraft.io/docs/reference/system-architecture/)
- [Snap: confinamento e segurança — Políticas AppArmor, interfaces e suporte do kernel.](https://snapcraft.io/docs/explanation/security/snap-confinement/)
