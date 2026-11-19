"""Gera PowerPoint editável, PDF vetorial, apresentação HTML e roteiro da Semana 04.

Executar: uv run --with python-pptx --with Pillow --with reportlab python gerar_apresentacao.py
"""
from pathlib import Path
from html import escape
import json
import subprocess
import base64

from PIL import ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
W, H = 13.333333, 7.5
BG, INK, MUTED = 'FFFFFF', '212121', '404040'
TEAL, SOFT, WHITE, LINE = '0076B8', 'EDF5FA', 'FFFFFF', 'D6E5EF'
GOLD, DARKCARD = '0076B8', 'EDF5FA'
TEMPLATE = ROOT.parents[1]/'semana-01'/'slides'/'assets'
BACKGROUNDS = {name: TEMPLATE/f'fundo-{name}.png' for name in ('capa', 'conteudo', 'secao')}
slides = []


def font_path(bold=False):
    pattern = 'Liberation Sans:style=Bold' if bold else 'Liberation Sans:style=Regular'
    return subprocess.check_output(['fc-match', '-f', '%{file}', pattern], text=True).strip()


FONTS = {False: font_path(), True: font_path(True)}


def wrap(text, width, size, bold=False):
    font = ImageFont.truetype(FONTS[bold], round(size * 96 / 72))
    result = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split():
            candidate = (line + ' ' + word).strip()
            if line and font.getlength(candidate) > width * 96:
                result.append(line)
                line = word
            else:
                line = candidate
        result.append(line)
    return '\n'.join(result)


def box(s, x, y, w, h, color, stroke=None, rounded=True):
    s['elements'].append(dict(kind='box', x=x, y=y, w=w, h=h, color=color, stroke=stroke, rounded=rounded))


def text(s, content, x, y, w, h, size=22, color=INK, bold=False, link=None, align='left'):
    content = wrap(content, w, size, bold)
    lines = len(content.split('\n'))
    required = lines * size / 72 * 1.15
    if required > h + .03:
        raise ValueError(f"Slide {len(slides)}: texto não cabe ({required:.2f} > {h}): {content}")
    s['elements'].append(dict(kind='text', text=content, x=x, y=y, w=w, h=h, size=size, color=color, bold=bold, link=link, align=align))


def new(title, tag, who, timing, notes, dark=False, sources=''):
    s = dict(title=title, tag=tag, who=who, timing=timing, notes=notes + ('\n\nFontes: ' + sources if sources else ''), dark=False, theme='conteudo', elements=[])
    slides.append(s)
    if title:
        text(s, title, .58, .43, 10.70, 1.20, 36, INK, True)
    return s


LEFT, WIDTH = .58, 10.70
MAIN_COUNT = 15

refs = [
    ('Debian: APT e dpkg', 'Papéis das ferramentas e instalação.', 'https://www.debian.org/doc/manuals/debian-faq/pkgtools.en.html'),
    ('Debian: formato deb(5)', 'Estrutura interna de pacotes binários Debian.', 'https://manpages.debian.org/trixie/dpkg-dev/deb.5.en.html'),
    ('Debian: consultas dpkg-query', 'Arquivos instalados, status e metadados.', 'https://manpages.debian.org/trixie/dpkg/dpkg-query.1.en.html'),
    ('FreeBSD Ports', 'Construção, configuração e instalação.', 'https://docs.freebsd.org/en/books/handbook/ports/'),
    ('FreeBSD: etapas do port', 'Fluxo fetch, extract, patch, configure, build e stage.', 'https://docs.freebsd.org/en/books/porters-handbook/slow-porting/'),
    ('FreeBSD: misc/hello', 'Receita oficial e opção NLS.', 'https://cgit.freebsd.org/ports/tree/misc/hello/Makefile'),
    ('Nix: perfis e gerações', 'Seleção por links simbólicos e rollback.', 'https://nix.dev/manual/nix/2.34/package-management/profiles.html'),
    ('Nix: caminhos do store', 'Endereçamento por hash e isolamento de dependências.', 'https://nix.dev/manual/nix/2.34/store/store-path.html'),
    ('Flatpak: arquitetura interna', 'OSTree, deduplicação por hardlinks e Bubblewrap.', 'https://docs.flatpak.org/en/latest/under-the-hood.html'),
    ('Flatpak: permissões da sandbox', 'Acesso a arquivos, overrides e portais.', 'https://docs.flatpak.org/en/latest/sandbox-permissions.html'),
    ('Snap: arquitetura e formato SquashFS', 'Imagens somente leitura, revisões e canais.', 'https://snapcraft.io/docs/reference/system-architecture/'),
    ('Snap: confinamento e segurança', 'Políticas AppArmor, interfaces e suporte do kernel.', 'https://snapcraft.io/docs/explanation/security/snap-confinement/'),
]


def panel(s, x, y, w, h, title):
    box(s, x, y, w, h, SOFT, rounded=False)
    text(s, title, x+.24, y+.22, w-.48, .67, 30, TEAL, True)


def rows(s, data, y=1.90, step=.96, label_w=3.25, size=26):
    for i, (label, body) in enumerate(data):
        top = y+i*step
        box(s, LEFT, top, WIDTH, step-.08, SOFT if i % 2 == 0 else WHITE, rounded=False)
        text(s, label, .80, top+.06, label_w, step-.12, size, TEAL, True)
        text(s, body, .80+label_w+.20, top+.06, WIDTH-label_w-.64, step-.12, size, INK)


def takeaway(s, content, y=6.30):
    text(s, content, LEFT, y, WIDTH, .83, 26, TEAL, True)


def number(s, i):
    text(s, str(i), 12.88, 7.03, .36, .32, 14, WHITE if s['theme']=='secao' else INK, True)


# Slide 1 — Capa
s = new('Gerenciadores de pacotes em Unix/Linux', 'Capa', 'Integrante 1', '0:00–0:20',
    'Apresentar a entrega da Semana 4: consolidação das demonstrações práticas das quatro famílias e resultados da bateria experimental. Todas as medidas foram coletadas em 18 de novembro de 2026 na mesma máquina física e registradas na pasta semana-04/evidencias/. Mantemos o recorte com Debian (APT/dpkg), FreeBSD Ports, Nix, Flatpak e Snap.')
s['theme']='capa'; s['elements']=[]
text(s, 'Gerenciadores de pacotes\nem Unix/Linux', .85, .70, 11.5, 1.85, 48, INK, True, align='center')
text(s, 'Semana 4\nComparações, demonstrações e medidas', 1.05, 2.80, 10.9, 1.16, 30, INK, align='center')
text(s, 'Debian · FreeBSD Ports · Nix · Flatpak · Snap', .95, 4.35, 11.1, .58, 26, INK, align='center')

# Slide 2 — Ambiente e controle experimental
s = new('Ambiente e controle experimental.', 'Método', 'Integrante 1', '0:20–1:05',
    'Explicar as condições de teste registradas em 18 de novembro de 2026. O hospedeiro utiliza processador AMD Ryzen 5 2600 de 6 núcleos e 12 threads, 15 GiB de RAM, armazenamento NVMe e kernel Linux 7.3.4 no NixOS 26.11. Para evitar distorções de rede, pacotes .deb, código-fonte, caminhos do store e o pacote .snap foram pré-carregados localmente antes das medições. Cada operação de tempo teve três repetições em estado limpo, e o rastreamento com strace foi executado em passagem separada para não inflar o tempo medido.')
rows(s, [('Hardware e SO', 'Ryzen 5 2600 · 15 GiB RAM · NVMe · Linux 7.3.4.'),
         ('Sem variação de rede', 'Arquivos em cache local antes de medir o tempo.'),
         ('Três repetições', 'Média, mediana e desvio-padrão por operação.'),
         ('strace separado', 'Contagem de syscalls fora da tomada de tempo.')], step=1.02, label_w=3.55)
takeaway(s, 'Mesma máquina física e etapas medidas separadamente.')

# Slide 3 — Debian: pacotes, arquivos e dependências
s = new('Debian: pacotes .deb e dependências.', 'Debian', 'Integrante 1', '1:05–1:55',
    'Apresentar a validação prática do representante Debian em container oficial debian:trixie-slim (Debian 13.7, APT 3.0.4 e dpkg 1.22.22). A inspeção com dpkg-deb mostrou o formato ar contendo o arquivo de controle (control, md5sums, postinst) e a árvore de dados extraída em /usr. Na base enxuta, hello exigiu apenas 1 pacote .deb (52,0 KiB), tmux exigiu 3 pacotes .deb (876,5 KiB totais, incluindo libevent e libjemalloc2) e a simulação do gnome-text-editor apontou 211 pacotes novos para compor a pilha gráfica.',
    sources=refs[0][2]+'; '+refs[1][2]+'; '+refs[2][2])
rows(s, [('hello 2.10-5', '1 pacote .deb · 52,0 KiB download · 280 KiB final.'),
         ('tmux 3.5a-3', '3 pacotes .deb · 876,5 KiB download · 2.455 KiB final.'),
         ('gnome-text-editor', '48.3-3 · requer 211 pacotes novos na base limpa.'),
         ('Registro dpkg', 'Lista em /var/lib/dpkg/info/*.list e *.md5sums.')], step=1.02, label_w=3.35)
takeaway(s, 'O pacote extrai arquivos diretamente sobre a árvore FHS.')

# Slide 4 — Debian: medidas de instalação e syscalls
s = new('Debian: tempo local e chamadas de sistema.', 'Medidas Debian', 'Integrante 1', '1:55–2:45',
    'Detalhar os números medidos no dpkg -i a partir do cache local, sem rede. A instalação de hello levou 37,33 ms em média (desvio de 0,58 ms) e realizou 2.478 syscalls, destacando-se 146 chamadas rename e 21 fsync. Já a instalação de tmux com suas duas dependências levou 161,67 ms (desvio de 0,58 ms) e executou 7.904 syscalls, incluindo 81 fsync, 77 rename, 192 fcntl para travas de banco de dados e 100 execve para processos auxiliares e script postinst. A atomicidade ocorre por arquivo via rename, não na árvore inteira.',
    sources=refs[1][2]+'; '+refs[2][2])
panel(s, LEFT, 1.95, 5.20, 3.96, 'hello (1 pacote .deb)')
panel(s, 6.06, 1.95, 5.20, 3.96, 'tmux + 2 deps (3 .deb)')
text(s, 'Tempo: 37,3 ± 0,6 ms.\n2.478 syscalls totais.\n146 rename · 21 fsync.\n44 fcntl · 21 execve.', .84, 2.95, 4.66, 2.60, 27, INK)
text(s, 'Tempo: 161,7 ± 0,6 ms.\n7.904 syscalls totais.\n77 rename · 81 fsync.\n192 fcntl · 100 execve.', 6.32, 2.95, 4.66, 2.60, 27, INK)
takeaway(s, 'Segurança de escrita usa rename() por arquivo e fsync().')

# Slide 5 — FreeBSD Ports: receita misc/hello e fases
s = new('FreeBSD Ports: receita de misc/hello.', 'FreeBSD Ports', 'Integrante 2', '2:45–3:35',
    'Apresentar a verificação da receita oficial misc/hello na árvore do FreeBSD Ports. O Makefile declara versão 2.12.3, USES=charsetfix gmake perl5, GNU_CONFIGURE=yes e a opção OPTIONS_DEFINE=NLS, que habilita suporte a traduções via gettext. O distinfo fixa o arquivo hello-2.12.3.tar.gz com 1.189.208 bytes e hash SHA-256 verificado. Explicar com transparência: a receita oficial é do FreeBSD Ports, e a medição experimental das fases configure, build e stage foi executada sobre esse mesmo tarball no hospedeiro Linux.',
    sources=refs[3][2]+'; '+refs[4][2]+'; '+refs[5][2])
rows(s, [('Receita oficial', 'misc/hello 2.12.3 · USES=charsetfix gmake perl5.'),
         ('Fonte verificada', 'hello-2.12.3.tar.gz · 1,13 MiB · SHA-256 exato.'),
         ('Opção declarada', 'OPTIONS_DEFINE=NLS (--enable-nls + gettext).'),
         ('Fases medidas', 'extract → configure → build → stage/install.')], step=1.02, label_w=3.35)
takeaway(s, 'A receita governa dependências, opções e fases de compilação.')

# Slide 6 — Efeito da opção NLS na compilação
s = new('Construção do fonte: efeito da opção NLS.', 'Medidas Compilação', 'Integrante 2', '3:35–4:30',
    'Comparar as duas variantes de compilação de hello-2.12.3 em três repetições. Com NLS ativado (--enable-nls), o tempo total foi de 19,84 segundos, sendo 17,03 s no configure, 2,03 s no make e 755,3 ms na fase de stage/install, instalando 50 arquivos (400,8 KiB, incluindo 46 catálogos .mo). Sem NLS (--disable-nls), a fase de stage caiu para 258,3 ms (quase 3 vezes mais rápida) e o resultado instalado caiu para 4 arquivos e 193,8 KiB (redução de 51,6%). Em ambas, a área temporária WRKDIR ocupou mais de 10 MiB e 810 arquivos.',
    sources=refs[4][2]+'; '+refs[5][2])
panel(s, LEFT, 1.95, 5.20, 3.96, 'Com NLS (--enable-nls)')
panel(s, 6.06, 1.95, 5.20, 3.96, 'Sem NLS (--disable-nls)')
text(s, 'Total: 19.840 ± 155 ms.\nStage: 755,3 ± 14,3 ms.\nFinal: 400,8 KiB (50 arqs).\n2.467.256 syscalls.', .84, 2.95, 4.66, 2.60, 27, INK)
text(s, 'Total: 19.288 ± 61 ms.\nStage: 258,3 ± 3,5 ms.\nFinal: 193,8 KiB (4 arqs).\n2.382.742 syscalls.', 6.32, 2.95, 4.66, 2.60, 27, INK)
takeaway(s, 'Desativar NLS corta 46 catálogos .mo e 51,6% do espaço final.')

# Slide 7 — Binário pronto vs código-fonte
s = new('Instalar binário pronto vs. compilar fonte.', 'Contraste de SO', 'Integrante 2', '4:30–5:15',
    'Confrontar diretamente o custo de SO para disponibilizar o programa hello por pacote binário Debian versus compilação a partir do código-fonte. O tempo passa de 37,3 ms para 19.840 ms (531 vezes maior); o total de chamadas de sistema salta de 2.478 para 2,47 milhões (995 vezes maior, com 4.261 chamadas execve durante os testes do configure); e o disco exige 10,17 MiB temporários em WRKDIR. Isso demonstra por que compilar do fonte só se justifica quando a personalização de opções ou arquitetura é necessária.',
    sources=refs[0][2]+'; '+refs[3][2])
rows(s, [('Tempo local', '37,3 ms (dpkg -i) vs. 19.840,4 ms (fonte): 531x.'),
         ('Syscalls totais', '2.478 vs. 2.467.256 chamadas ao kernel: 995x.'),
         ('Processos (execve)', '21 execuções vs. 4.261 processos na construção.'),
         ('Disco temporário', 'Sem área de build vs. 10,17 MiB no WRKDIR.')], step=1.02, label_w=3.55)
takeaway(s, 'O controle de compilação cobra alto custo de CPU, VFS e processos.')

# Slide 8 — Nix: tamanho próprio vs fechamento
s = new('Nix: tamanho próprio vs. fechamento.', 'Nix Store', 'Integrante 3', '5:15–6:05',
    'Apresentar as medidas de armazenamento no /nix/store obtidas com nix path-info -s -S. O pacote hello-2.12.3 tem 273,0 KiB de tamanho próprio (NAR), mas seu fechamento soma 36,73 MiB por incluir a glibc. O tmux-3.8 tem 1,59 MiB próprio e 58,12 MiB de fechamento. Já o gnome-text-editor-50.1 possui apenas 2,73 MiB próprios, mas seu fechamento atinge 957,19 MiB com toda a pilha GTK4 e bibliotecas gráficas. Como o store é compartilhado, o fechamento não é duplicado a cada perfil.',
    sources=refs[6][2]+'; '+refs[7][2])
rows(s, [('hello 2.12.3', '273,0 KiB próprio (NAR) · 36,73 MiB fechamento.'),
         ('tmux 3.8', '1,59 MiB próprio (NAR) · 58,12 MiB fechamento.'),
         ('Text Editor 50.1', '2,73 MiB próprio (NAR) · 957,19 MiB fechamento.'),
         ('Compartilhamento', 'Bibliotecas em /nix/store servem a vários perfis.')], step=1.02, label_w=3.35)
takeaway(s, 'Fechamento mede dependências totais, não custo exclusivo novo.')

# Slide 9 — Nix: perfis, gerações e rollback
s = new('Nix: ativação de perfis e rollback atômico.', 'Medidas Nix', 'Integrante 3', '6:05–6:55',
    'Mostrar os tempos medidos em três repetições com os pacotes já presentes no /nix/store. O comando nix profile add levou 37,61 ms para hello, 37,53 ms para tmux e 37,66 ms para o gnome-text-editor. O tempo independe do fechamento de 957 MiB porque o Nix apenas cria links simbólicos para o store (3.617 syscalls, sem fsync). O retorno à geração anterior com nix profile rollback levou 31,80 ms (desvio de 0,33 ms), trocando o link simbólico da geração ativa com 1 symlink e 1 rename, sem alterar documentos do usuário.',
    sources=refs[6][2])
rows(s, [('profile add (hello)', '37,6 ± 0,8 ms · 3.617 syscalls · 4 symlink.'),
         ('profile add (editor)', '37,7 ± 1,7 ms · tempo constante para 957 MiB.'),
         ('profile rollback', '31,8 ± 0,3 ms · 3.525 syscalls · 1 rename.'),
         ('Coexistência real', 'Perfil A (editor+hello) e B (editor+tmux) ativos.')], step=1.02, label_w=3.55)
takeaway(s, 'Ativar ou reverter um perfil altera symlinks, não os pacotes.')

# Slide 10 — Vinculação dinâmica ELF
s = new('Vinculação dinâmica ELF nos binários.', 'ELF e RUNPATH', 'Integrante 3', '6:55–7:50',
    'Explicar a diferença estrutural observada com readelf -d e ldd nos binários instalados. No Debian, /usr/bin/tmux declara apenas bibliotecas NEEDED e não possui RUNPATH, dependendo de /lib/x86_64-linux-gnu. No Nix, cada binário ELF traz gravado no cabeçalho o campo RUNPATH com todos os diretórios /nix/store/<hash>-.../lib exatos, e o gnome-text-editor usa um binário wrapper compilado que exporta variáveis gráficas antes de chamar .gnome-text-editor-wrapped. No Snap, o binário não usa RUNPATH de store e depende de LD_LIBRARY_PATH e montagens bind.',
    sources=refs[1][2]+'; '+refs[7][2]+'; '+refs[10][2])
rows(s, [('Debian (FHS)', 'Sem RUNPATH · resolve em /lib/x86_64-linux-gnu.'),
         ('Nix (Store)', 'RUNPATH no ELF aponta para /nix/store/<hash>/lib.'),
         ('Nix (Wrapper)', 'Wrapper configura esquemas GTK e chama o ELF real.'),
         ('Snap (Container)', 'Sem RUNPATH · usa LD_LIBRARY_PATH e bind mounts.')], step=1.02, label_w=3.35)
takeaway(s, 'O RUNPATH por hash permite coexistência de versões sem container.')

# Slide 11 — Flatpak e Snap: armazenamento e OSTree
s = new('Flatpak e Snap: runtimes e deduplicação.', 'Flatpak e Snap', 'Integrante 4', '7:50–8:45',
    'Comparar a estrutura de armazenamento do GNOME Text Editor no Flathub e na Snap Store e o experimento prático com OSTree 2026.2. Nos dois formatos, o pacote da aplicação é pequeno (1,4 MB no Flatpak; 1,07 MiB no Snap rev 53), mas exige runtimes ou snaps de conteúdo grandes no primeiro uso (432,8 MB para org.gnome.Platform 51; 66,84 MiB para core24 mais 616,03 MiB para gnome-46-2404). No teste prático com OSTree, dois commits consecutivos compartilharam exatamente o mesmo inode (10495777, com 3 hardlinks) para o arquivo inalterado.',
    sources=refs[8][2]+'; '+refs[10][2])
panel(s, LEFT, 1.95, 5.20, 3.96, 'Flatpak + OSTree')
panel(s, 6.06, 1.95, 5.20, 3.96, 'Snap + SquashFS')
text(s, 'App: 1,4 MB (2,5 MB inst.).\nRuntime GNOME 51: 432,8 MB.\nOSTree: mesmo inode (10495777)\nentre os commits v1 e v2.', .84, 2.88, 4.66, 2.75, 26, INK)
text(s, 'App rev 53: 1,07 MiB (2,98 MiB).\ncore24: 66,8 MiB.\nGNOME 46: 616,0 MiB.\nImagem SquashFS somente leitura.', 6.32, 2.88, 4.66, 2.75, 26, INK)
takeaway(s, 'OSTree deduplica por hardlinks; Snap mantém imagens comprimidas.')

# Slide 12 — Bubblewrap e SquashFS: isolamento e compressão
s = new('Bubblewrap e SquashFS: proteção e custo.', 'Isolamento e Imagem', 'Integrante 4', '8:45–9:40',
    'Apresentar os resultados práticos de confinamento com Bubblewrap 0.13.1 e o teste de compressão SquashFS sobre o pacote oficial gnome-text-editor_53.snap. No Bubblewrap, omitir a pasta bloqueou a leitura (exit 1); expor com --ro-bind permitiu ler comparacao.txt mas bloqueou escrita com Read-only file system (exit 1); expor com --bind permitiu salvar resultado-bwrap.txt. A sobrecarga de criar namespaces foi de apenas 4,5 ms (7,78 ms vs 3,28 ms, 963 syscalls). Na recompressão SquashFS da árvore do editor, zstd ficou 9,1% maior que xz, mas extraiu 42,9% mais rápido.',
    sources=refs[9][2]+'; '+refs[10][2]+'; '+refs[11][2])
rows(s, [('bwrap sem bind', 'Leitura negada: No such file or directory (exit 1).'),
         ('bwrap --ro-bind', 'Leitura OK (exit 0) · escrita negada: Read-only FS.'),
         ('Custo do sandbox', '7,78 ms vs. 3,28 ms (+4,5 ms · 963 syscalls).'),
         ('SquashFS xz vs zstd', 'xz: 832 KiB (29,1 ms) · zstd: 908 KiB (16,6 ms).')], step=1.02, label_w=3.55)
takeaway(s, 'O isolamento é leve (~4,5 ms), mas depende da política configurada.')

# Slide 13 — Síntese quantitativa das quatro famílias
s = new('Comparação transversal das medidas.', 'Síntese', 'Integrante 3', '9:40–10:25',
    'Reunir lado a lado os indicadores verificados no mesmo hardware para ilustrar as escolhas de projeto de Sistemas Operacionais. O dpkg realiza extração direta e sincronização em disco (37,3 ms e 2.478 syscalls para hello). A compilação do fonte exige 19,84 s e 2,47 milhões de syscalls, mas permite remover catálogos NLS (-51,6% de tamanho). O Nix ativa ou reverte perfis em 32 a 38 ms apenas trocando symlinks e isolando bibliotecas via RUNPATH. O Bubblewrap isola a visão de arquivos do processo em 7,8 ms com 17 montagens e pivot_root.')
rows(s, [('Debian (dpkg -i)', '37,3 ms (hello) · 2.478 syscalls · FHS global.'),
         ('Fonte (compilação)', '19.840 ms · 2,47M syscalls · -51,6% disco sem NLS.'),
         ('Nix (perfil/rollback)', '37,6 ms add / 31,8 ms rollback · RUNPATH no store.'),
         ('Flatpak / Snap', 'bwrap +4,5 ms (963 syscalls) · OSTree / SquashFS.')], step=1.02, label_w=3.55)
takeaway(s, 'Os números refletem mecanismos distintos de VFS, linker e processos.')

# Slide 14 — Limites metodológicos e Semana 5
s = new('Limites registrados e etapa final.', 'Limites e Semana 5', 'Integrante 4', '10:25–11:05',
    'Explicar com transparência o alcance do que foi medido e o que resta para a consolidação final da Semana 5. O ambiente Debian rodou em container sobre o kernel Linux 7.3.4; a receita misc/hello foi verificada no FreeBSD Ports e sua compilação medida sobre o tarball oficial no Linux; o pacote gnome-text-editor_53.snap foi inspecionado diretamente e verificamos que o kernel NixOS local não inclui apparmor em /sys/kernel/security/lsm, comprovando que o confinamento estrito do Snap exige suporte do hospedeiro. Na Semana 5 consolidaremos o relatório e a defesa final.')
rows(s, [('Alcance Debian', 'Container oficial Debian 13 sobre kernel Linux 7.3.4.'),
         ('Alcance Ports', 'Receita oficial FreeBSD + compilação medida em Linux.'),
         ('Suporte do kernel', 'Host sem AppArmor em /sys/kernel/security/lsm.'),
         ('Rumo à Semana 5', 'Unificar teoria, medidas e guia de decisão final.')], step=1.02, label_w=3.35)
takeaway(s, 'Rigor experimental exige declarar o ambiente exato de cada medida.')

# Slide 15 — Encerramento
s = new('Cada mecanismo otimiza uma prioridade.', 'Encerramento', 'Integrante 4', '11:05–11:30',
    'Encerrar destacando que as medições confirmam na prática a tese do trabalho: não existe um gerenciador universalmente superior porque cada família resolve um problema diferente de Sistemas Operacionais. O modelo FHS prioriza simplicidade e compartilhamento imediato; Ports prioriza adaptabilidade na construção; Nix prioriza reprodutibilidade, coexistência por RUNPATH e rollback atômico de perfis; Flatpak e Snap priorizam desacoplamento do sistema base e controle de acesso do processo. Agradecer e abrir para perguntas.')
s['theme']='secao'; s['elements']=[]
text(s, 'Cada mecanismo otimiza\numa prioridade de SO.', 4.72, 2.35, 7.76, 1.95, 44, WHITE, True)
text(s, 'Compartilhamento FHS, compilação sob medida,\nreprodutibilidade no store ou sandbox.', 4.75, 4.55, 7.55, 1.45, 28, WHITE)

# Slide 16 — Apoio: Detalhamento de syscalls
s = new('Apoio: perfil de syscalls por operação.', 'Apoio', 'Apoio', 'Fora do tempo principal',
    'Slide de apoio para perguntas sobre chamadas de sistema. No dpkg -i do tmux (7.904 chamadas), destacam-se 81 chamadas fsync, 77 rename e 192 fcntl para garantir atomicidade por arquivo e bloqueio do banco de dados. Na compilação de hello com NLS (2.467.256 chamadas), 790.471 são openat e 4.261 são execve gerados pelo script configure e pelo compilador. No nix profile rollback (3.525 chamadas), há apenas 1 symlink, 1 rename e 1 flock, sem fsync de pacotes. No Bubblewrap (963 chamadas), aparecem 1 unshare, 17 mount, 8 mount_setattr e 2 pivot_root.')
rows(s, [('dpkg -i tmux', '7.904 total · 81 fsync · 77 rename · 192 fcntl.'),
         ('Build hello (NLS)', '2.467.256 total · 790.471 openat · 4.261 execve.'),
         ('nix rollback', '3.525 total · 1 symlink · 1 rename · 1 flock.'),
         ('bwrap sandbox', '963 total · 1 unshare · 17 mount · 2 pivot_root.')], step=1.02, label_w=3.35)
takeaway(s, 'As chamadas ao kernel revelam onde cada ferramenta gasta tempo.')

# Slide 17 — Apoio: Compressão SquashFS e metadados do Snap
s = new('Apoio: SquashFS e metadados do Snap.', 'Apoio', 'Apoio', 'Fora do tempo principal',
    'Slide de apoio com os dados extraídos do pacote oficial gnome-text-editor_53.snap (1.118.208 bytes, SHA3-384 verificado). A árvore extraída possui 3.124.861 bytes (2,98 MiB) em 338 arquivos. Reempacotando essa mesma árvore com mksquashfs em 3 repetições: xz gerou 832,0 KiB (compressão em 145,6 ms, extração em 29,1 ms); zstd gerou 908,0 KiB (compressão em 104,7 ms, extração em 16,6 ms, 42,9% mais rápida); gzip gerou 1.036,0 KiB (compressão em 76,9 ms, extração em 17,2 ms). O meta/snap.yaml define GTK_USE_PORTAL=1 e cinco interfaces content.',
    sources=refs[10][2]+'; '+refs[11][2])
rows(s, [('SquashFS xz', '832,0 KiB (razão 0,273) · extração em 29,1 ± 3,5 ms.'),
         ('SquashFS zstd', '908,0 KiB (razão 0,298) · extração em 16,6 ± 0,4 ms.'),
         ('SquashFS gzip', '1.036,0 KiB (razão 0,339) · extração em 17,2 ± 0,3 ms.'),
         ('meta/snap.yaml', 'base core24 · strict · GTK_USE_PORTAL=1 · 5 content.')], step=1.02, label_w=3.35)
takeaway(s, 'zstd acelera a descompressão em 42,9% com +9,1% de tamanho ante xz.')

for i, spec in enumerate(slides, 1):
    if i != 1:
        number(spec, i)


# PowerPoint: texto e diagramas editáveis sobre os fundos institucionais.
prs=Presentation()
prs.slide_width=Inches(W)
prs.slide_height=Inches(H)
prs.core_properties.title='Gerenciadores de pacotes em Unix/Linux — Semana 04'
prs.core_properties.subject='Gerenciadores de pacotes em Unix/Linux'
prs.core_properties.author=''
prs.core_properties.keywords='Unix, Linux, FreeBSD, Debian, Ports, Nix, Flatpak, Snap, Benchmarks, Syscalls'
for index, spec in enumerate(slides):
    slide=prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb=RGBColor.from_string(BG)
    slide.shapes.add_picture(str(BACKGROUNDS[spec['theme']]),0,0,width=Inches(W),height=Inches(H))
    for e in spec['elements']:
        x,y,w,h=(Inches(e[k]) for k in ['x','y','w','h'])
        if min(e['x'],e['y']) < 0 or e['x']+e['w']>W+.01 or e['y']+e['h']>H+.01:
            raise ValueError(f'Elemento fora do slide {index+1}: {e}')
        if e['kind']=='box':
            shape=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if e['rounded'] else MSO_SHAPE.RECTANGLE,x,y,w,h)
            if e['rounded']:
                shape.adjustments[0]=.12
            shape.fill.solid(); shape.fill.fore_color.rgb=RGBColor.from_string(e['color'])
            shape.line.fill.background()
        else:
            shape=slide.shapes.add_textbox(x,y,w,h)
            tf=shape.text_frame
            tf.clear();tf.word_wrap=False
            tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
            for j,line in enumerate(e['text'].split('\n')):
                p=tf.paragraphs[0] if j==0 else tf.add_paragraph()
                p.space_before=Pt(0);p.space_after=Pt(0);p.line_spacing=1.12
                if e.get('align')=='center': p.alignment=PP_ALIGN.CENTER
                run=p.add_run();run.text=line
                run.font.name='Arial';run.font.size=Pt(e['size']);run.font.bold=e['bold']
                run.font.color.rgb=RGBColor.from_string(e['color'])
                if e.get('link'):run.hyperlink.address=e['link']
    slide.notes_slide.notes_text_frame.text=f"{spec['who']} · {spec['timing']}\n\n{spec['notes']}"
pptx_path=ROOT/'apresentacao-semana-04.pptx'
prs.save(pptx_path)

# PDF vetorial com fontes incorporadas, usando os mesmos elementos.
pdfmetrics.registerFont(TTFont('DeckRegular', FONTS[False]))
pdfmetrics.registerFont(TTFont('DeckBold', FONTS[True]))
pdf=pdfcanvas.Canvas(str(ROOT/'apresentacao-semana-04.pdf'),pagesize=(W*72,H*72))
pdf.setTitle('Gerenciadores de pacotes em Unix/Linux — Semana 04')
pdf.setAuthor('')
for spec in slides:
    pdf.drawImage(str(BACKGROUNDS[spec['theme']]),0,0,width=W*72,height=H*72)
    for e in spec['elements']:
        pdf.setFillColorRGB(*(int(e['color'][i:i+2],16)/255 for i in (0,2,4)))
        if e['kind']=='box':
            if e['rounded']:
                pdf.roundRect(e['x']*72,(H-e['y']-e['h'])*72,e['w']*72,e['h']*72,min(7,e['h']*18),fill=1,stroke=0)
            else:
                pdf.rect(e['x']*72,(H-e['y']-e['h'])*72,e['w']*72,e['h']*72,fill=1,stroke=0)
        else:
            fontname='DeckBold' if e['bold'] else 'DeckRegular'
            pdf.setFont(fontname,e['size'])
            baseline=(H-e['y'])*72-pdfmetrics.getAscent(fontname)/1000*e['size']
            for j,line in enumerate(e['text'].split('\n')):
                if e.get('align')=='center':
                    pdf.drawCentredString((e['x']+e['w']/2)*72,baseline-j*e['size']*1.12,line)
                else:
                    pdf.drawString(e['x']*72,baseline-j*e['size']*1.12,line)
            if e.get('link'):
                pdf.linkURL(e['link'],(e['x']*72,(H-e['y']-e['h'])*72,(e['x']+e['w'])*72,(H-e['y'])*72),relative=0,thickness=0)
    pdf.showPage()
pdf.save()

# HTML offline: mesma geometria e texto do PowerPoint, com teclado e tela cheia.
html_slides=[]
for i,s in enumerate(slides):
    parts=[]
    for e in s['elements']:
        style=f"left:{e['x']*96:.2f}px;top:{e['y']*96:.2f}px;width:{e['w']*96:.2f}px;height:{e['h']*96:.2f}px;"
        if e['kind']=='box':
            parts.append(f'<div class="shape" style="{style}background:#{e["color"]};border-radius:{10 if e["rounded"] else 0}px"></div>')
        else:
            style+=f'font-size:{e["size"]*96/72:.2f}px;color:#{e["color"]};font-weight:{700 if e["bold"] else 400};text-align:{e.get("align","left")};'
            content=escape(e['text'])
            if e.get('link'):content=f'<a href="{escape(e["link"])}" target="_blank" rel="noreferrer">{content}</a>'
            parts.append(f'<div class="txt" style="{style}">{content}</div>')
    html_slides.append(f'<section class="page" data-slide="{i}" aria-label="Slide {i+1}: {escape(s["title"] or "Capa")}"><div class="canvas" style="background-image:var(--bg-{s["theme"]});background-size:100% 100%">'+''.join(parts)+'</div></section>')
metadata=json.dumps([dict(who=s['who'],timing=s['timing'],notes=s['notes']) for s in slides],ensure_ascii=False)
html='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gerenciadores de pacotes — Semana 04</title>
<style>*{box-sizing:border-box}body{margin:0;color:var(--foreground,#24343a);font:14px/1.5 system-ui,sans-serif}.toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:12px 0}button{font:inherit;color:inherit;background:var(--secondary,#e9eeeb);border:1px solid var(--border,#cbd9d2);border-radius:6px;padding:7px 12px;cursor:pointer}button:focus-visible{outline:3px solid #128d8a;outline-offset:2px}button:disabled{opacity:.4;cursor:default}#counter{margin-right:auto;font-variant-numeric:tabular-nums}.page{position:relative;overflow:hidden;display:none;width:100%}.page.active{display:block}.canvas{position:relative;width:1280px;height:720px;transform-origin:top left}.shape,.txt{position:absolute}.txt{font-family:'Liberation Sans',Arial,sans-serif;line-height:1.12;white-space:pre;overflow:visible}a{color:inherit;text-decoration:none}a:hover{text-decoration:underline}#notes{border-top:1px solid var(--border,#cbd9d2);margin-top:14px;padding:16px 0;line-height:1.7;white-space:pre-wrap}#notes[hidden]{display:none}#stage:fullscreen{background:#0c1d24;display:flex;align-items:center;justify-content:center}.hint{font-size:12px;opacity:.7;margin:0 0 10px}@media print{@page{size:13.333333in 7.5in;margin:0}html,body{width:13.333333in}.toolbar,.hint,#notes{display:none!important}.page{display:block!important;width:13.333333in!important;height:7.5in!important;break-after:page;print-color-adjust:exact;-webkit-print-color-adjust:exact}.page:last-child{break-after:auto}.canvas{transform:none!important}body{background:white}}
</style></head><body><div class="toolbar"><span id="counter" aria-live="polite"></span><button type="button" id="prev" aria-label="Slide anterior">← Anterior</button><button type="button" id="next" aria-label="Próximo slide">Próximo →</button><button type="button" id="toggle" aria-expanded="false" aria-controls="notes">Notas de fala</button><button type="button" id="full">Tela cheia</button><button type="button" id="print">Imprimir / PDF</button></div><p class="hint">Setas: navegar · F: tela cheia · N: notas · 15 slides principais + 2 de apoio</p><main id="stage">'''+''.join(html_slides)+'''</main><aside id="notes" hidden></aside><script>
const meta='''+metadata+''';const pages=[...document.querySelectorAll('.page')];let current=0;
function resize(){const fullscreen=!!document.fullscreenElement;const width=fullscreen?Math.min(innerWidth,innerHeight*16/9):document.getElementById('stage').clientWidth;for(const page of pages){page.style.width=width+'px';page.style.height=(width*9/16)+'px';page.firstElementChild.style.transform='scale('+(width/1280)+')';}}
function show(index){current=Math.max(0,Math.min(pages.length-1,index));pages.forEach((p,i)=>p.classList.toggle('active',i===current));document.getElementById('counter').textContent=(current+1)+' / '+pages.length+(current<15?' · Principal':' · Apoio');document.getElementById('prev').disabled=current===0;document.getElementById('next').disabled=current===pages.length-1;const m=meta[current];document.getElementById('notes').textContent=m.who+' · '+m.timing+'\\n\\n'+m.notes;resize();}
function toggleNotes(){const n=document.getElementById('notes');n.hidden=!n.hidden;document.getElementById('toggle').setAttribute('aria-expanded',String(!n.hidden));}
async function full(){try{if(document.fullscreenElement)await document.exitFullscreen();else await document.getElementById('stage').requestFullscreen();}catch(error){document.querySelector('.hint').textContent='Tela cheia indisponível neste visualizador. Abra o arquivo HTML no navegador.';}}
document.getElementById('prev').onclick=()=>show(current-1);document.getElementById('next').onclick=()=>show(current+1);document.getElementById('toggle').onclick=toggleNotes;document.getElementById('full').onclick=full;document.getElementById('print').onclick=()=>window.print();window.addEventListener('resize',resize);document.addEventListener('fullscreenchange',resize);document.addEventListener('keydown',event=>{if(event.altKey||event.ctrlKey||event.metaKey)return;if(['ArrowRight','PageDown',' '].includes(event.key)){event.preventDefault();show(current+1);}if(['ArrowLeft','PageUp'].includes(event.key)){event.preventDefault();show(current-1);}if(event.key==='Home')show(0);if(event.key==='End')show(pages.length-1);if(event.key.toLowerCase()==='n')toggleNotes();if(event.key.toLowerCase()==='f')full();});show(0);
</script></body></html>'''
bg_styles=':root{'+''.join('--bg-'+name+':url("data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'");' for name,path in BACKGROUNDS.items())+'}'
html=html.replace('<style>','<style>'+bg_styles,1)
(ROOT/'apresentacao-semana-04.html').write_text(html)

notes=['# Roteiro de fala — Semana 04','', 'Apresentação em grupo de quatro pessoas. Quinze slides principais, com duração estimada de 11 minutos e 30 segundos, e dois slides de apoio. Os tempos devem ser confirmados em ensaio. A divisão usa Integrante 1–4 porque os nomes não foram fornecidos.','', 'PowerPoint: as notas também estão no modo do apresentador. HTML: tecla N exibe as notas. Para apresentar sem notas, mantenha-as fechadas e use tela cheia.','']
for i,s in enumerate(slides):
    notes.extend([f'## Slide {i+1} — {s["title"] or "Gerenciadores de pacotes em Unix/Linux"}', '', f'**{s["who"]} · {s["timing"]}**', '', s['notes'], ''])
notes.extend(['## Fontes', '']+[f'- [{a} — {b}]({url})' for a,b,url in refs])
(ROOT/'roteiro-de-fala.md').write_text('\n'.join(notes)+'\n')
loaded=Presentation(pptx_path)
assert len(loaded.slides)==17
assert all(slide.has_notes_slide for slide in loaded.slides)
print(f'Gerados {len(slides)} slides: PowerPoint, PDF vetorial, HTML offline e roteiro.')
print(f'PowerPoint: {pptx_path.stat().st_size:,} bytes. Textos dentro das caixas e elementos dentro dos slides.')
