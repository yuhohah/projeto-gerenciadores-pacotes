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
ACCENT_BG = 'DCECF7'
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
MAIN_COUNT = 12

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


def rows(s, data, y=1.85, step=1.02, label_w=3.40, size=25):
    for i, (label, body) in enumerate(data):
        top = y + i * step
        box(s, LEFT, top, WIDTH, step - .09, SOFT if i % 2 == 0 else WHITE, rounded=False)
        text(s, label, .80, top + .08, label_w, step - .14, size, TEAL, True)
        text(s, body, .80 + label_w + .20, top + .08, WIDTH - label_w - .64, step - .14, size, INK)


def compare_grid(s, items, y=1.82, h=4.22):
    """4 cartões verticais simples lado a lado para comparar os métodos."""
    gap = .22
    cw = (WIDTH - 3 * gap) / 4
    for i, (head, metric, detail) in enumerate(items):
        x = LEFT + i * (cw + gap)
        box(s, x, y, cw, h, SOFT, rounded=False)
        box(s, x, y, cw, .74, ACCENT_BG, rounded=False)
        text(s, head, x + .14, y + .12, cw - .28, .56, 21, TEAL, True, align='center')
        text(s, metric, x + .14, y + .94, cw - .28, 1.25, 21, INK, True, align='center')
        text(s, detail, x + .14, y + 2.26, cw - .28, h - 2.38, 19, MUTED)


def takeaway(s, content, y=6.30):
    text(s, content, LEFT, y, WIDTH, .83, 25, TEAL, True)


def number(s, i):
    text(s, str(i), 12.88, 7.03, .36, .32, 14, WHITE if s['theme'] == 'secao' else INK, True)


# ==============================================================================
# BLOCO 1 — CAPA, METODOLOGIA E VALIDADE (Slides 1 a 4)
# ==============================================================================

# Slide 1 — Capa
s = new('Gerenciadores de pacotes em Unix/Linux', 'Capa', 'Integrante 1', '0:00–0:20',
    'Apresentar a entrega da Semana 4: primeiro explicaremos a metodologia experimental no NixOS e a validade de cada medição usando um único programa (GNU hello); em seguida mostraremos o vídeo prático dos testes; por fim, apresentaremos os resultados simplificados em comparações diretas entre os métodos de instalar e executar um programa.')
s['theme'] = 'capa'; s['elements'] = []
text(s, 'Gerenciadores de pacotes\nem Unix/Linux', .85, .70, 11.5, 1.85, 48, INK, True, align='center')
text(s, 'Semana 4\nMetodologia, validade e comparação entre métodos', 1.05, 2.80, 10.9, 1.16, 30, INK, align='center')
text(s, 'Debian · FreeBSD Ports · Nix · Flatpak · Snap', .95, 4.35, 11.1, .58, 26, INK, align='center')

# Slide 2 — Metodologia: protocolo controlado com um único programa
s = new('Metodologia: um programa único sob controle.', 'Metodologia', 'Integrante 1', '0:20–1:10',
    'Explicar o desenho experimental. Para comparar gerenciadores sem misturar diferenças de tamanho ou bibliotecas gráficas, fixamos um único programa de referência: o GNU hello, que depende apenas da libc.so.6 e possui 46 traduções (.mo). Todas as medições rodam no mesmo computador (Ryzen 5 2600, 15 GiB RAM, NVMe, NixOS 26.11, Linux 7.3.4), com arquivos já em cache local para zerar efeito de rede, 3 repetições por operação e rastreamento de syscalls (strace -fc) em passe separado.')
rows(s, [
    ('Programa único', 'GNU hello em todos os métodos · depende só da libc.so.6.'),
    ('Mesmo hardware', 'Ryzen 5 2600 · 15 GiB RAM · SSD NVMe · Linux 7.3.4.'),
    ('Sem rede no tempo', 'Pacotes e fontes em cache local antes de cronometrar.'),
    ('Repetições e trace', '3 repetições por teste · strace -fc medido em passe separado.'),
])
takeaway(s, 'Controlar pelo mesmo programa isola o custo puro de cada método.')

# Slide 3 — Como testar os 4 métodos no mesmo NixOS?
s = new('Como testar os quatro métodos no mesmo NixOS?', 'Execução', 'Integrante 1', '1:10–2:00',
    'Responder se tudo rodou em container: não. Apenas o Debian rodou em container Linux (debian:trixie-slim), pois o NixOS não possui /usr/bin nem /var/lib/dpkg globais; o container fornece apenas a árvore FHS sobre o mesmo kernel Linux 7.3.4, sem VM. Já o Nix (2.35.6), OSTree (Flatpak), Bubblewrap e SquashFS (Snap) rodam 100% nativos no host. Para o FreeBSD Ports, inspecionamos a receita oficial misc/hello e compilamos o mesmo tarball oficial nativamente no host.')
rows(s, [
    ('Nix (100% nativo)', 'Opera direto no /nix/store e perfis reais do host NixOS.'),
    ('Flatpak/Snap (nativo)', 'ostree, bwrap e squashfs chamam direto o kernel 7.3.4.'),
    ('Debian (container)', 'Container debian:trixie-slim só cria o FHS no mesmo kernel.'),
    ('Ports (receita + build)', 'Receita oficial misc/hello + build nativo do mesmo fonte.'),
], label_w=3.65)
takeaway(s, 'Só o Debian usa container FHS; sem máquina virtual em nenhum teste.')

# Slide 4 — Validade experimental e ressalvas honestas
s = new('Validade das medições e limites conhecidos.', 'Validade', 'Integrante 1', '2:00–2:50',
    'Explicar o que cada teste prova com 100% de rigor e onde existem ressalvas metodológicas. Propriedades estáticas (.deb, árvores de arquivos, cabeçalhos ELF e receita misc/hello) têm validade 100% exata. Nix, OSTree, Bubblewrap e SquashFS têm validade 100% nativa sobre ext4 e NVMe. No container Debian, as 2.478 syscalls do dpkg vão direto ao kernel 7.3.4, com a ressalva de a raiz usar OverlayFS. No build do hello, a economia de 51,6% ao desativar NLS é idêntica ao port, mas o tempo de compilação pertence ao toolchain Linux/GCC.')
rows(s, [
    ('100% exato (estático)', 'Estrutura .deb/.snap, arquivos e cabeçalhos ELF (readelf).'),
    ('100% nativo (host)', 'Nix, OSTree (inodes), bwrap (namespaces) e SquashFS.'),
    ('Ressalva no Debian', 'Syscalls reais no kernel 7.3.4, mas raiz em OverlayFS.'),
    ('Ressalva Ports/Snap', 'Build no Linux/GCC; host sem AppArmor impede daemon Snap.'),
], label_w=3.65)
takeaway(s, 'Declarar o que é nativo e o que é condicionado dá rigor ao experimento.')


# ==============================================================================
# BLOCO 2 — SLIDE EM BRANCO PARA O VÍDEO (Slide 5)
# ==============================================================================

s = new('', 'Vídeo', 'Todos', '2:50–4:20',
    '[Slide em branco reservado para inserção do vídeo demonstrativo dos testes práticos.]')


# ==============================================================================
# BLOCO 3 — RESULTADOS SIMPLIFICADOS EM COMPARAÇÕES ENTRE MÉTODOS (Slides 6 a 12)
# ==============================================================================

# Slide 6 — Comparação 1: Onde o programa fica e como acha bibliotecas?
s = new('Onde o programa fica e como acha a libc?', 'Organização', 'Integrante 2', '4:20–5:15',
    'Primeira comparação após o vídeo: como cada método guarda o GNU hello no disco e resolve a libc.so.6. No Debian (FHS), o binário vai para /usr/bin/hello e o ELF não tem RUNPATH, buscando a biblioteca global do sistema. Na compilação tipo Ports, vai para um prefixo local (/usr/local) e usa a libc do sistema. No Nix, o programa fica isolado em /nix/store/<hash>-hello e grava um RUNPATH fixo no ELF apontando para sua glibc exata. No Flatpak e Snap, versões iguais compartilham inodes via OSTree (10495848) ou ficam compactadas em uma imagem .snap isolada.',
    sources=refs[0][2]+'; '+refs[7][2]+'; '+refs[8][2])
compare_grid(s, [
    ('Debian (FHS)', '/usr/bin/hello\n(global)', 'Mistura arquivos no /usr.\nELF sem RUNPATH usa /lib do sistema.'),
    ('Ports (Fonte)', 'STAGEDIR →\n/usr/local', 'Prefixo separado do sistema base.\nPermite escolher o que instalar.'),
    ('Nix (Store)', '/nix/store/\n<hash>-hello', 'Diretório imutável por hash.\nELF fixa RUNPATH para sua glibc.'),
    ('Flatpak / Snap', 'OSTree / .snap\n(isolados)', 'OSTree compartilha inode 10495848.\nSnap empacota tudo numa imagem.'),
])
takeaway(s, 'Debian e Ports usam caminhos compartilhados; Nix, Flatpak e Snap isolam.')

# Slide 7 — Comparação 2: Quanto tempo e esforço custa instalar?
s = new('Quanto custa instalar ou preparar o programa?', 'Tempo e Syscalls', 'Integrante 2', '5:15–6:10',
    'Segunda comparação: o custo em tempo e chamadas de sistema para disponibilizar o GNU hello. Instalar o pacote binário pronto no Debian (dpkg -i) levou 37,3 ms com 2.478 syscalls. Ativar o pacote já existente no store do Nix (nix profile add) levou 41,3 ms e 3.617 syscalls. Empacotar em imagem .snap com zstd levou 37,7 ms (e 10,1 ms para extrair). Já compilar o mesmo hello do código-fonte exigiu 19.840 ms (cerca de 530x mais lento) e 2.467.256 syscalls (~1.000x mais chamadas, incluindo 4.261 execve).',
    sources=refs[1][2]+'; '+refs[4][2]+'; '+refs[6][2])
rows(s, [
    ('Binário pronto (Debian)', '37,3 ms (dpkg -i) · 2.478 syscalls (fsync + rename no FHS).'),
    ('Ativação no Nix', '41,3 ms (profile add) · 3.617 syscalls (symlinks do perfil).'),
    ('Imagem .snap (SquashFS)', '37,7 ms p/ gerar (zstd) ou 50,1 ms (xz) · extração em 10,1 ms.'),
    ('Compilar do fonte (Ports)', '19.840 ms (~530x mais lento) · 2,47M syscalls · 4.261 execve.'),
], label_w=3.75)
takeaway(s, 'Pronto ou por symlink leva ~40 ms; compilar custa ~530x mais tempo.')

# Slide 8 — Comparação 3: Espaço em disco e personalização
s = new('Quanto espaço ocupa e dá para enxugar?', 'Espaço em Disco', 'Integrante 3', '6:10–7:05',
    'Terceira comparação: tamanho em disco e flexibilidade de personalização. O .deb pronto instala 188 KiB fixos no FHS (51,4 KiB baixados). Compilar do fonte gasta 7,45 MiB temporários e gera 400,8 KiB em 50 arquivos com NLS, mas permite desativar NLS e cortar para 193,8 KiB em 4 arquivos (-51,6% de espaço). No Nix, o pacote hello tem 273,0 KiB próprios (NAR) e closure de 36,7 MiB com glibc compartilhada. No OSTree, duas versões dividem o mesmo inode (0 B extra no binário) e o SquashFS comprime a árvore de 246,7 KiB para 64,0 KiB (xz).',
    sources=refs[5][2]+'; '+refs[7][2]+'; '+refs[8][2]+'; '+refs[10][2])
compare_grid(s, [
    ('Debian (.deb)', '188 KiB fixos\n(51,4 KiB .deb)', 'Pacote binário fechado.\nInstala todas as traduções.'),
    ('Fonte (Ports)', '400,8 → 193,8\nKiB (-51,6%)', 'Sem NLS: 50 → 4 arquivos.\nExige 7,45 MiB temp. no build.'),
    ('Nix (Store)', '273 KiB NAR\n36,7 MiB total', 'Closure inclui a glibc.\nCompartilhada entre pacotes.'),
    ('Flatpak / Snap', '0 B extra (OSTree)\n64 KiB (.snap)', 'OSTree deduplica binário igual.\nSnap comprime 246,7 → 64 KiB.'),
])
takeaway(s, 'Compilar personaliza o tamanho (-52%); OSTree evita duplicar; Snap comprime.')

# Slide 9 — Comparação 4: Rodar direto no sistema ou isolado (sandbox)?
s = new('Rodar direto no sistema vs. isolado em sandbox.', 'Execução e Isolamento', 'Integrante 3', '7:05–8:00',
    'Quarta comparação: o custo e os requisitos de executar o programa. Executar o hello diretamente no Debian levou 2,00 ms, e no NixOS levou 3,28 ms — com acesso normal ao usuário. Executá-lo isolado via Bubblewrap (motor do Flatpak, com --unshare-all) levou 7,78 ms: apenas +4,50 ms e 963 syscalls (1 unshare, 17 mount, 2 pivot_root), bloqueando leituras sem bind e bloqueando escrita sob --ro-bind. Já a leitura de /sys/kernel/security/lsm revelou ausência de AppArmor no host, mostrando que o confinamento do Snap depende desse módulo no kernel.',
    sources=refs[9][2]+'; '+refs[11][2])
rows(s, [
    ('Direto (Debian / Nix)', '2,00 ms (Debian) · 3,28 ms (Nix) · sem isolamento de pastas.'),
    ('Sandbox bwrap (Flatpak)', '7,78 ms (+4,50 ms de sobrecarga) · 963 syscalls de namespace.'),
    ('Controle de acesso', 'Sem bind: bloqueado · --ro-bind: só lê · --bind: lê e grava.'),
    ('Dependência do Snap', 'Exige AppArmor no kernel (ausente no host NixOS testado).'),
], label_w=3.65)
takeaway(s, 'Namespaces isolam o programa por +4,5 ms; o Snap exige AppArmor no kernel.')

# Slide 10 — Comparação 5: Como atualizar ou desfazer uma falha?
s = new('Atualização e rollback: como voltar atrás?', 'Reversibilidade', 'Integrante 4', '8:00–8:50',
    'Quinta comparação: o que acontece ao atualizar ou desfazer uma instalação. No Debian, o dpkg altera o FHS in-place com travas fcntl, fsync e rename; voltar atrás exige reinstalar a versão anterior. Na compilação via Ports, uma nova versão sobrescreve ou reconstrói arquivos sem histórico nativo de gerações. No Nix, o rollback do hello levou 34,7 ms e 3.525 syscalls, trocando apenas 1 symlink e 1 rename sem tocar nos binários nem chamar fsync de pacote. No Flatpak (OSTree) e no Snap, versões antigas ficam preservadas por commits ou imagens anteriores.',
    sources=refs[1][2]+'; '+refs[6][2]+'; '+refs[8][2]+'; '+refs[10][2])
compare_grid(s, [
    ('Debian (dpkg)', 'Mutação\nin-place', 'Grava direto no FHS.\nDesfazer exige reinstalar .deb.'),
    ('Ports (Fonte)', 'Substitui ou\nrecompila', 'Sem gerações automáticas.\nVoltar exige refazer pacote.'),
    ('Nix (Perfil)', 'Rollback em\n34,7 ms', 'Só 1 symlink + 1 rename.\n0 fsync em arquivos do pacote.'),
    ('Flatpak / Snap', 'Commits ou\nimagens .snap', 'OSTree reverte commit inteiro.\nSnap aponta revisão anterior.'),
])
takeaway(s, 'Modelos imutáveis (Nix, OSTree, Snap) desfazem em ms sem reescrever arquivos.')

# Slide 11 — Quadro síntese: qual método escolher?
s = new('Síntese: o que cada método troca na prática.', 'Síntese', 'Integrante 4', '8:50–9:45',
    'Fechar a comparação dos resultados resumindo a troca de Sistemas Operacionais de cada método de usar um programa. O Debian prioriza rapidez e simplicidade (37,3 ms, 188 KiB), abrindo mão de isolamento e rollback atômico. O modelo Ports/Fonte prioriza controle fino do binário (-51,6% sem NLS), pagando o alto custo de compilação local (19,8 s). O Nix prioriza reprodutibilidade e rollback instantâneo (34,7 ms) via store imutável e RUNPATH. O Flatpak e o Snap priorizam isolamento e entrega autocontida (+4,5 ms no sandbox), diferenciando-se pela portabilidade de namespaces no Flatpak contra a exigência de AppArmor no Snap.')
rows(s, [
    ('Debian (APT/dpkg)', 'Mais leve e rápido no FHS (37,3 ms), mas mutável e sem sandbox.'),
    ('Ports (Código-fonte)', 'Customiza recursos (-51,6% s/ NLS), porém custa ~19,8 s de build.'),
    ('Nix (Store + Perfil)', 'Coexistência por RUNPATH e rollback em 34,7 ms, mas closure maior.'),
    ('Flatpak / Snap', 'Isolamento (+4,5 ms bwrap) e deduplicação/compressão (64 KiB).'),
], label_w=3.45)
takeaway(s, 'Não há método único ideal: cada um otimiza velocidade, controle ou isolamento.')

# Slide 12 — Encerramento
s = new('Metodologia validada e comparações claras.', 'Encerramento', 'Integrante 4', '9:45–10:15',
    'Encerrar reforçando que fixar o GNU hello, explicitar o papel do NixOS como hospedeiro único e colocar os resultados em comparações diretas após a demonstração em vídeo deixa nítido o impacto real de cada método de SO. A bateria com pacotes maiores já está reservada para a apresentação final da Semana 5. Abrir para perguntas.')
s['theme'] = 'secao'; s['elements'] = []
text(s, 'Cada método troca custo\npor controle ou segurança.', 4.72, 2.35, 7.76, 1.95, 42, WHITE, True)
text(s, 'Metodologia validada no NixOS\ne base pronta para a Semana 5.', 4.75, 4.55, 7.55, 1.45, 28, WHITE)


# ==============================================================================
# APOIO (Slide 13 — fora do tempo principal)
# ==============================================================================

s = new('Apoio: números exatos e syscalls (GNU hello).', 'Apoio', 'Apoio', 'Fora do tempo principal',
    'Slide de apoio para eventuais perguntas da banca com todas as médias (3 repetições) e totais de syscalls (strace -fc) medidos no GNU hello: Debian dpkg -i (37,33 ms; 2.478 syscalls), Build com/sem NLS (19.840 ms / 2.467.256 vs. 19.288 ms / 2.382.742 syscalls), Nix add/rollback (41,28 ms / 3.617 vs. 34,70 ms / 3.525 syscalls) e Bubblewrap bwrap (7,78 ms; 963 syscalls).')
rows(s, [
    ('Debian (dpkg -i)', '37,33 ± 0,47 ms · 2.478 syscalls · 188 KiB no FHS · exec 2,00 ms.'),
    ('Build NLS / sem NLS', '19.840 / 19.288 ms · 2,47M / 2,38M syscalls · 400,8 / 193,8 KiB.'),
    ('Nix add / rollback', '41,28 / 34,70 ms · 3.617 / 3.525 syscalls · 1 symlink + 1 rename.'),
    ('Flatpak / Snap', 'bwrap 7,78 ms (+4,50 ms · 963 syscalls) · SquashFS xz 64 KiB.'),
], label_w=3.45)
takeaway(s, 'Todas as médias vêm de 3 repetições independentes em cache local.')


for i, spec in enumerate(slides, 1):
    if i != 1 and spec.get('tag') != 'Vídeo':
        number(spec, i)


# PowerPoint: texto e diagramas editáveis sobre os fundos institucionais.
prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)
prs.core_properties.title = 'Gerenciadores de pacotes em Unix/Linux — Semana 04'
prs.core_properties.subject = 'Gerenciadores de pacotes em Unix/Linux'
prs.core_properties.author = ''
prs.core_properties.keywords = 'Unix, Linux, FreeBSD, Debian, Ports, Nix, Flatpak, Snap, Benchmarks, Syscalls'
for index, spec in enumerate(slides):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string(BG)
    slide.shapes.add_picture(str(BACKGROUNDS[spec['theme']]), 0, 0, width=Inches(W), height=Inches(H))
    for e in spec['elements']:
        x, y, w, h = (Inches(e[k]) for k in ['x', 'y', 'w', 'h'])
        if min(e['x'], e['y']) < 0 or e['x'] + e['w'] > W + .01 or e['y'] + e['h'] > H + .01:
            raise ValueError(f'Elemento fora do slide {index + 1}: {e}')
        if e['kind'] == 'box':
            shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if e['rounded'] else MSO_SHAPE.RECTANGLE, x, y, w, h)
            if e['rounded']:
                shape.adjustments[0] = .12
            shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor.from_string(e['color'])
            shape.line.fill.background()
        else:
            shape = slide.shapes.add_textbox(x, y, w, h)
            tf = shape.text_frame
            tf.clear(); tf.word_wrap = False
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            for j, line in enumerate(e['text'].split('\n')):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                p.space_before = Pt(0); p.space_after = Pt(0); p.line_spacing = 1.12
                if e.get('align') == 'center':
                    p.alignment = PP_ALIGN.CENTER
                run = p.add_run(); run.text = line
                run.font.name = 'Arial'; run.font.size = Pt(e['size']); run.font.bold = e['bold']
                run.font.color.rgb = RGBColor.from_string(e['color'])
                if e.get('link'):
                    run.hyperlink.address = e['link']
    slide.notes_slide.notes_text_frame.text = f"{spec['who']} · {spec['timing']}\n\n{spec['notes']}"
pptx_path = ROOT / 'apresentacao-semana-04.pptx'
prs.save(pptx_path)

# PDF vetorial com fontes incorporadas, usando os mesmos elementos.
pdfmetrics.registerFont(TTFont('DeckRegular', FONTS[False]))
pdfmetrics.registerFont(TTFont('DeckBold', FONTS[True]))
pdf = pdfcanvas.Canvas(str(ROOT / 'apresentacao-semana-04.pdf'), pagesize=(W * 72, H * 72))
pdf.setTitle('Gerenciadores de pacotes em Unix/Linux — Semana 04')
pdf.setAuthor('')
for spec in slides:
    pdf.drawImage(str(BACKGROUNDS[spec['theme']]), 0, 0, width=W * 72, height=H * 72)
    for e in spec['elements']:
        pdf.setFillColorRGB(*(int(e['color'][i:i + 2], 16) / 255 for i in (0, 2, 4)))
        if e['kind'] == 'box':
            if e['rounded']:
                pdf.roundRect(e['x'] * 72, (H - e['y'] - e['h']) * 72, e['w'] * 72, e['h'] * 72, min(7, e['h'] * 18), fill=1, stroke=0)
            else:
                pdf.rect(e['x'] * 72, (H - e['y'] - e['h']) * 72, e['w'] * 72, e['h'] * 72, fill=1, stroke=0)
        else:
            fontname = 'DeckBold' if e['bold'] else 'DeckRegular'
            pdf.setFont(fontname, e['size'])
            baseline = (H - e['y']) * 72 - pdfmetrics.getAscent(fontname) / 1000 * e['size']
            for j, line in enumerate(e['text'].split('\n')):
                if e.get('align') == 'center':
                    pdf.drawCentredString((e['x'] + e['w'] / 2) * 72, baseline - j * e['size'] * 1.12, line)
                else:
                    pdf.drawString(e['x'] * 72, baseline - j * e['size'] * 1.12, line)
            if e.get('link'):
                pdf.linkURL(e['link'], (e['x'] * 72, (H - e['y'] - e['h']) * 72, (e['x'] + e['w']) * 72, (H - e['y']) * 72), relative=0, thickness=0)
    pdf.showPage()
pdf.save()

# HTML offline: mesma geometria e texto do PowerPoint, com teclado e tela cheia.
html_slides = []
for i, s in enumerate(slides):
    parts = []
    for e in s['elements']:
        style = f"left:{e['x'] * 96:.2f}px;top:{e['y'] * 96:.2f}px;width:{e['w'] * 96:.2f}px;height:{e['h'] * 96:.2f}px;"
        if e['kind'] == 'box':
            parts.append(f'<div class="shape" style="{style}background:#{e["color"]};border-radius:{10 if e["rounded"] else 0}px"></div>')
        else:
            style += f'font-size:{e["size"] * 96 / 72:.2f}px;color:#{e["color"]};font-weight:{700 if e["bold"] else 400};text-align:{e.get("align", "left")};'
            content = escape(e['text'])
            if e.get('link'):
                content = f'<a href="{escape(e["link"])}" target="_blank" rel="noreferrer">{content}</a>'
            parts.append(f'<div class="txt" style="{style}">{content}</div>')
    label = s['title'] or ('Vídeo (slide em branco)' if s['tag'] == 'Vídeo' else 'Capa')
    html_slides.append(f'<section class="page" data-slide="{i}" aria-label="Slide {i + 1}: {escape(label)}"><div class="canvas" style="background-image:var(--bg-{s["theme"]});background-size:100% 100%">' + ''.join(parts) + '</div></section>')
metadata = json.dumps([dict(who=s['who'], timing=s['timing'], notes=s['notes']) for s in slides], ensure_ascii=False)
support_count = len(slides) - MAIN_COUNT
html = '''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gerenciadores de pacotes — Semana 04</title>
<style>*{box-sizing:border-box}body{margin:0;color:var(--foreground,#24343a);font:14px/1.5 system-ui,sans-serif}.toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:12px 0}button{font:inherit;color:inherit;background:var(--secondary,#e9eeeb);border:1px solid var(--border,#cbd9d2);border-radius:6px;padding:7px 12px;cursor:pointer}button:focus-visible{outline:3px solid #128d8a;outline-offset:2px}button:disabled{opacity:.4;cursor:default}#counter{margin-right:auto;font-variant-numeric:tabular-nums}.page{position:relative;overflow:hidden;display:none;width:100%}.page.active{display:block}.canvas{position:relative;width:1280px;height:720px;transform-origin:top left}.shape,.txt{position:absolute}.txt{font-family:'Liberation Sans',Arial,sans-serif;line-height:1.12;white-space:pre;overflow:visible}a{color:inherit;text-decoration:none}a:hover{text-decoration:underline}#notes{border-top:1px solid var(--border,#cbd9d2);margin-top:14px;padding:16px 0;line-height:1.7;white-space:pre-wrap}#notes[hidden]{display:none}#stage:fullscreen{background:#0c1d24;display:flex;align-items:center;justify-content:center}.hint{font-size:12px;opacity:.7;margin:0 0 10px}@media print{@page{size:13.333333in 7.5in;margin:0}html,body{width:13.333333in}.toolbar,.hint,#notes{display:none!important}.page{display:block!important;width:13.333333in!important;height:7.5in!important;break-after:page;print-color-adjust:exact;-webkit-print-color-adjust:exact}.page:last-child{break-after:auto}.canvas{transform:none!important}body{background:white}}
</style></head><body><div class="toolbar"><span id="counter" aria-live="polite"></span><button type="button" id="prev" aria-label="Slide anterior">← Anterior</button><button type="button" id="next" aria-label="Próximo slide">Próximo →</button><button type="button" id="toggle" aria-expanded="false" aria-controls="notes">Notas de fala</button><button type="button" id="full">Tela cheia</button><button type="button" id="print">Imprimir / PDF</button></div><p class="hint">Setas: navegar · F: tela cheia · N: notas · ''' + f'{MAIN_COUNT} slides principais + {support_count} de apoio' + '''</p><main id="stage">''' + ''.join(html_slides) + '''</main><aside id="notes" hidden></aside><script>
const meta=''' + metadata + ''';const MAIN_COUNT=''' + str(MAIN_COUNT) + ''';const pages=[...document.querySelectorAll('.page')];let current=0;
function resize(){const fullscreen=!!document.fullscreenElement;const width=fullscreen?Math.min(innerWidth,innerHeight*16/9):document.getElementById('stage').clientWidth;for(const page of pages){page.style.width=width+'px';page.style.height=(width*9/16)+'px';page.firstElementChild.style.transform='scale('+(width/1280)+')';}}
function show(index){current=Math.max(0,Math.min(pages.length-1,index));pages.forEach((p,i)=>p.classList.toggle('active',i===current));document.getElementById('counter').textContent=(current+1)+' / '+pages.length+(current<MAIN_COUNT?' · Principal':' · Apoio');document.getElementById('prev').disabled=current===0;document.getElementById('next').disabled=current===pages.length-1;const m=meta[current];document.getElementById('notes').textContent=m.who+' · '+m.timing+'\\n\\n'+m.notes;resize();}
function toggleNotes(){const n=document.getElementById('notes');n.hidden=!n.hidden;document.getElementById('toggle').setAttribute('aria-expanded',String(!n.hidden));}
async function full(){try{if(document.fullscreenElement)await document.exitFullscreen();else await document.getElementById('stage').requestFullscreen();}catch(error){document.querySelector('.hint').textContent='Tela cheia indisponível neste visualizador. Abra o arquivo HTML no navegador.';}}
document.getElementById('prev').onclick=()=>show(current-1);document.getElementById('next').onclick=()=>show(current+1);document.getElementById('toggle').onclick=toggleNotes;document.getElementById('full').onclick=full;document.getElementById('print').onclick=()=>window.print();window.addEventListener('resize',resize);document.addEventListener('fullscreenchange',resize);document.addEventListener('keydown',event=>{if(event.altKey||event.ctrlKey||event.metaKey)return;if(['ArrowRight','PageDown',' '].includes(event.key)){event.preventDefault();show(current+1);}if(['ArrowLeft','PageUp'].includes(event.key)){event.preventDefault();show(current-1);}if(event.key==='Home')show(0);if(event.key==='End')show(pages.length-1);if(event.key.toLowerCase()==='n')toggleNotes();if(event.key.toLowerCase()==='f')full();});show(0);
</script></body></html>'''
bg_styles = ':root{' + ''.join('--bg-' + name + ':url("data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode() + '");' for name, path in BACKGROUNDS.items()) + '}'
html = html.replace('<style>', '<style>' + bg_styles, 1)
(ROOT / 'apresentacao-semana-04.html').write_text(html)

notes = ['# Roteiro de fala — Semana 04', '', f'Apresentação em grupo de quatro pessoas. {MAIN_COUNT} slides principais (incluindo o Slide 5 em branco reservado para o vídeo), com duração estimada de ~10 minutos e 15 segundos, e {support_count} slide de apoio. Os tempos devem ser confirmados em ensaio. A divisão usa Integrante 1–4 porque os nomes não foram fornecidos.', '', 'PowerPoint: as notas também estão no modo do apresentador. HTML: tecla N exibe as notas. Para apresentar sem notas, mantenha-as fechadas e use tela cheia.', '']
for i, s in enumerate(slides):
    label = s['title'] or ('Slide em branco — Vídeo demonstrativo' if s['tag'] == 'Vídeo' else 'Gerenciadores de pacotes em Unix/Linux')
    notes.extend([f'## Slide {i + 1} — {label}', '', f'**{s["who"]} · {s["timing"]}**', '', s['notes'], ''])
notes.extend(['## Fontes', ''] + [f'- [{a} — {b}]({url})' for a, b, url in refs])
(ROOT / 'roteiro-de-fala.md').write_text('\n'.join(notes) + '\n')
loaded = Presentation(pptx_path)
assert len(loaded.slides) == len(slides)
assert all(slide.has_notes_slide for slide in loaded.slides)
print(f'Gerados {len(slides)} slides: PowerPoint, PDF vetorial, HTML offline e roteiro.')
print(f'PowerPoint: {pptx_path.stat().st_size:,} bytes. Textos dentro das caixas e elementos dentro dos slides.')
