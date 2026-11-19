# Roteiro de fala — Semana 04

Apresentação em grupo de quatro pessoas. Quinze slides principais, com duração estimada de 11 minutos e 30 segundos, e dois slides de apoio. Os tempos devem ser confirmados em ensaio. A divisão usa Integrante 1–4 porque os nomes não foram fornecidos.

PowerPoint: as notas também estão no modo do apresentador. HTML: tecla N exibe as notas. Para apresentar sem notas, mantenha-as fechadas e use tela cheia.

## Slide 1 — Gerenciadores de pacotes em Unix/Linux

**Integrante 1 · 0:00–0:20**

Apresentar a entrega da Semana 4: consolidação das demonstrações práticas das quatro famílias e resultados da bateria experimental. Todas as medidas foram coletadas em 18 de novembro de 2026 na mesma máquina física e registradas na pasta semana-04/evidencias/. Mantemos o recorte com Debian (APT/dpkg), FreeBSD Ports, Nix, Flatpak e Snap.

## Slide 2 — Ambiente e controle experimental.

**Integrante 1 · 0:20–1:05**

Explicar as condições de teste registradas em 18 de novembro de 2026. O hospedeiro utiliza processador AMD Ryzen 5 2600 de 6 núcleos e 12 threads, 15 GiB de RAM, armazenamento NVMe e kernel Linux 7.3.4 no NixOS 26.11. Para evitar distorções de rede, pacotes .deb, código-fonte, caminhos do store e o pacote .snap foram pré-carregados localmente antes das medições. Cada operação de tempo teve três repetições em estado limpo, e o rastreamento com strace foi executado em passagem separada para não inflar o tempo medido.

## Slide 3 — Debian: pacotes .deb e dependências.

**Integrante 1 · 1:05–1:55**

Apresentar a validação prática do representante Debian em container oficial debian:trixie-slim (Debian 13.7, APT 3.0.4 e dpkg 1.22.22). A inspeção com dpkg-deb mostrou o formato ar contendo o arquivo de controle (control, md5sums, postinst) e a árvore de dados extraída em /usr. Na base enxuta, hello exigiu apenas 1 pacote .deb (52,0 KiB), tmux exigiu 3 pacotes .deb (876,5 KiB totais, incluindo libevent e libjemalloc2) e a simulação do gnome-text-editor apontou 211 pacotes novos para compor a pilha gráfica.

Fontes: https://www.debian.org/doc/manuals/debian-faq/pkgtools.en.html; https://manpages.debian.org/trixie/dpkg-dev/deb.5.en.html; https://manpages.debian.org/trixie/dpkg/dpkg-query.1.en.html

## Slide 4 — Debian: tempo local e chamadas de sistema.

**Integrante 1 · 1:55–2:45**

Detalhar os números medidos no dpkg -i a partir do cache local, sem rede. A instalação de hello levou 37,33 ms em média (desvio de 0,58 ms) e realizou 2.478 syscalls, destacando-se 146 chamadas rename e 21 fsync. Já a instalação de tmux com suas duas dependências levou 161,67 ms (desvio de 0,58 ms) e executou 7.904 syscalls, incluindo 81 fsync, 77 rename, 192 fcntl para travas de banco de dados e 100 execve para processos auxiliares e script postinst. A atomicidade ocorre por arquivo via rename, não na árvore inteira.

Fontes: https://manpages.debian.org/trixie/dpkg-dev/deb.5.en.html; https://manpages.debian.org/trixie/dpkg/dpkg-query.1.en.html

## Slide 5 — FreeBSD Ports: receita de misc/hello.

**Integrante 2 · 2:45–3:35**

Apresentar a verificação da receita oficial misc/hello na árvore do FreeBSD Ports. O Makefile declara versão 2.12.3, USES=charsetfix gmake perl5, GNU_CONFIGURE=yes e a opção OPTIONS_DEFINE=NLS, que habilita suporte a traduções via gettext. O distinfo fixa o arquivo hello-2.12.3.tar.gz com 1.189.208 bytes e hash SHA-256 verificado. Explicar com transparência: a receita oficial é do FreeBSD Ports, e a medição experimental das fases configure, build e stage foi executada sobre esse mesmo tarball no hospedeiro Linux.

Fontes: https://docs.freebsd.org/en/books/handbook/ports/; https://docs.freebsd.org/en/books/porters-handbook/slow-porting/; https://cgit.freebsd.org/ports/tree/misc/hello/Makefile

## Slide 6 — Construção do fonte: efeito da opção NLS.

**Integrante 2 · 3:35–4:30**

Comparar as duas variantes de compilação de hello-2.12.3 em três repetições. Com NLS ativado (--enable-nls), o tempo total foi de 19,84 segundos, sendo 17,03 s no configure, 2,03 s no make e 755,3 ms na fase de stage/install, instalando 50 arquivos (400,8 KiB, incluindo 46 catálogos .mo). Sem NLS (--disable-nls), a fase de stage caiu para 258,3 ms (quase 3 vezes mais rápida) e o resultado instalado caiu para 4 arquivos e 193,8 KiB (redução de 51,6%). Em ambas, a área temporária WRKDIR ocupou mais de 10 MiB e 810 arquivos.

Fontes: https://docs.freebsd.org/en/books/porters-handbook/slow-porting/; https://cgit.freebsd.org/ports/tree/misc/hello/Makefile

## Slide 7 — Instalar binário pronto vs. compilar fonte.

**Integrante 2 · 4:30–5:15**

Confrontar diretamente o custo de SO para disponibilizar o programa hello por pacote binário Debian versus compilação a partir do código-fonte. O tempo passa de 37,3 ms para 19.840 ms (531 vezes maior); o total de chamadas de sistema salta de 2.478 para 2,47 milhões (995 vezes maior, com 4.261 chamadas execve durante os testes do configure); e o disco exige 10,17 MiB temporários em WRKDIR. Isso demonstra por que compilar do fonte só se justifica quando a personalização de opções ou arquitetura é necessária.

Fontes: https://www.debian.org/doc/manuals/debian-faq/pkgtools.en.html; https://docs.freebsd.org/en/books/handbook/ports/

## Slide 8 — Nix: tamanho próprio vs. fechamento.

**Integrante 3 · 5:15–6:05**

Apresentar as medidas de armazenamento no /nix/store obtidas com nix path-info -s -S. O pacote hello-2.12.3 tem 273,0 KiB de tamanho próprio (NAR), mas seu fechamento soma 36,73 MiB por incluir a glibc. O tmux-3.8 tem 1,59 MiB próprio e 58,12 MiB de fechamento. Já o gnome-text-editor-50.1 possui apenas 2,73 MiB próprios, mas seu fechamento atinge 957,19 MiB com toda a pilha GTK4 e bibliotecas gráficas. Como o store é compartilhado, o fechamento não é duplicado a cada perfil.

Fontes: https://nix.dev/manual/nix/2.34/package-management/profiles.html; https://nix.dev/manual/nix/2.34/store/store-path.html

## Slide 9 — Nix: ativação de perfis e rollback atômico.

**Integrante 3 · 6:05–6:55**

Mostrar os tempos medidos em três repetições com os pacotes já presentes no /nix/store. O comando nix profile add levou 37,61 ms para hello, 37,53 ms para tmux e 37,66 ms para o gnome-text-editor. O tempo independe do fechamento de 957 MiB porque o Nix apenas cria links simbólicos para o store (3.617 syscalls, sem fsync). O retorno à geração anterior com nix profile rollback levou 31,80 ms (desvio de 0,33 ms), trocando o link simbólico da geração ativa com 1 symlink e 1 rename, sem alterar documentos do usuário.

Fontes: https://nix.dev/manual/nix/2.34/package-management/profiles.html

## Slide 10 — Vinculação dinâmica ELF nos binários.

**Integrante 3 · 6:55–7:50**

Explicar a diferença estrutural observada com readelf -d e ldd nos binários instalados. No Debian, /usr/bin/tmux declara apenas bibliotecas NEEDED e não possui RUNPATH, dependendo de /lib/x86_64-linux-gnu. No Nix, cada binário ELF traz gravado no cabeçalho o campo RUNPATH com todos os diretórios /nix/store/<hash>-.../lib exatos, e o gnome-text-editor usa um binário wrapper compilado que exporta variáveis gráficas antes de chamar .gnome-text-editor-wrapped. No Snap, o binário não usa RUNPATH de store e depende de LD_LIBRARY_PATH e montagens bind.

Fontes: https://manpages.debian.org/trixie/dpkg-dev/deb.5.en.html; https://nix.dev/manual/nix/2.34/store/store-path.html; https://snapcraft.io/docs/reference/system-architecture/

## Slide 11 — Flatpak e Snap: runtimes e deduplicação.

**Integrante 4 · 7:50–8:45**

Comparar a estrutura de armazenamento do GNOME Text Editor no Flathub e na Snap Store e o experimento prático com OSTree 2026.2. Nos dois formatos, o pacote da aplicação é pequeno (1,4 MB no Flatpak; 1,07 MiB no Snap rev 53), mas exige runtimes ou snaps de conteúdo grandes no primeiro uso (432,8 MB para org.gnome.Platform 51; 66,84 MiB para core24 mais 616,03 MiB para gnome-46-2404). No teste prático com OSTree, dois commits consecutivos compartilharam exatamente o mesmo inode (10495777, com 3 hardlinks) para o arquivo inalterado.

Fontes: https://docs.flatpak.org/en/latest/under-the-hood.html; https://snapcraft.io/docs/reference/system-architecture/

## Slide 12 — Bubblewrap e SquashFS: proteção e custo.

**Integrante 4 · 8:45–9:40**

Apresentar os resultados práticos de confinamento com Bubblewrap 0.13.1 e o teste de compressão SquashFS sobre o pacote oficial gnome-text-editor_53.snap. No Bubblewrap, omitir a pasta bloqueou a leitura (exit 1); expor com --ro-bind permitiu ler comparacao.txt mas bloqueou escrita com Read-only file system (exit 1); expor com --bind permitiu salvar resultado-bwrap.txt. A sobrecarga de criar namespaces foi de apenas 4,5 ms (7,78 ms vs 3,28 ms, 963 syscalls). Na recompressão SquashFS da árvore do editor, zstd ficou 9,1% maior que xz, mas extraiu 42,9% mais rápido.

Fontes: https://docs.flatpak.org/en/latest/sandbox-permissions.html; https://snapcraft.io/docs/reference/system-architecture/; https://snapcraft.io/docs/explanation/security/snap-confinement/

## Slide 13 — Comparação transversal das medidas.

**Integrante 3 · 9:40–10:25**

Reunir lado a lado os indicadores verificados no mesmo hardware para ilustrar as escolhas de projeto de Sistemas Operacionais. O dpkg realiza extração direta e sincronização em disco (37,3 ms e 2.478 syscalls para hello). A compilação do fonte exige 19,84 s e 2,47 milhões de syscalls, mas permite remover catálogos NLS (-51,6% de tamanho). O Nix ativa ou reverte perfis em 32 a 38 ms apenas trocando symlinks e isolando bibliotecas via RUNPATH. O Bubblewrap isola a visão de arquivos do processo em 7,8 ms com 17 montagens e pivot_root.

## Slide 14 — Limites registrados e etapa final.

**Integrante 4 · 10:25–11:05**

Explicar com transparência o alcance do que foi medido e o que resta para a consolidação final da Semana 5. O ambiente Debian rodou em container sobre o kernel Linux 7.3.4; a receita misc/hello foi verificada no FreeBSD Ports e sua compilação medida sobre o tarball oficial no Linux; o pacote gnome-text-editor_53.snap foi inspecionado diretamente e verificamos que o kernel NixOS local não inclui apparmor em /sys/kernel/security/lsm, comprovando que o confinamento estrito do Snap exige suporte do hospedeiro. Na Semana 5 consolidaremos o relatório e a defesa final.

## Slide 15 — Cada mecanismo otimiza uma prioridade.

**Integrante 4 · 11:05–11:30**

Encerrar destacando que as medições confirmam na prática a tese do trabalho: não existe um gerenciador universalmente superior porque cada família resolve um problema diferente de Sistemas Operacionais. O modelo FHS prioriza simplicidade e compartilhamento imediato; Ports prioriza adaptabilidade na construção; Nix prioriza reprodutibilidade, coexistência por RUNPATH e rollback atômico de perfis; Flatpak e Snap priorizam desacoplamento do sistema base e controle de acesso do processo. Agradecer e abrir para perguntas.

## Slide 16 — Apoio: perfil de syscalls por operação.

**Apoio · Fora do tempo principal**

Slide de apoio para perguntas sobre chamadas de sistema. No dpkg -i do tmux (7.904 chamadas), destacam-se 81 chamadas fsync, 77 rename e 192 fcntl para garantir atomicidade por arquivo e bloqueio do banco de dados. Na compilação de hello com NLS (2.467.256 chamadas), 790.471 são openat e 4.261 são execve gerados pelo script configure e pelo compilador. No nix profile rollback (3.525 chamadas), há apenas 1 symlink, 1 rename e 1 flock, sem fsync de pacotes. No Bubblewrap (963 chamadas), aparecem 1 unshare, 17 mount, 8 mount_setattr e 2 pivot_root.

## Slide 17 — Apoio: SquashFS e metadados do Snap.

**Apoio · Fora do tempo principal**

Slide de apoio com os dados extraídos do pacote oficial gnome-text-editor_53.snap (1.118.208 bytes, SHA3-384 verificado). A árvore extraída possui 3.124.861 bytes (2,98 MiB) em 338 arquivos. Reempacotando essa mesma árvore com mksquashfs em 3 repetições: xz gerou 832,0 KiB (compressão em 145,6 ms, extração em 29,1 ms); zstd gerou 908,0 KiB (compressão em 104,7 ms, extração em 16,6 ms, 42,9% mais rápida); gzip gerou 1.036,0 KiB (compressão em 76,9 ms, extração em 17,2 ms). O meta/snap.yaml define GTK_USE_PORTAL=1 e cinco interfaces content.

Fontes: https://snapcraft.io/docs/reference/system-architecture/; https://snapcraft.io/docs/explanation/security/snap-confinement/

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
