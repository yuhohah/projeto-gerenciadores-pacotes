"""Gera PowerPoint editável, apresentação HTML e roteiro a partir do mesmo conteúdo.

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
BACKGROUNDS = {name: ROOT/'assets'/f'fundo-{name}.png' for name in ('capa', 'conteudo', 'secao')}
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
    s = dict(title=title, tag=tag, who=who, timing=timing, notes=notes, dark=False, theme='conteudo', elements=[])
    slides.append(s)
    if title:
        text(s, title, .58, .43, 10.70, 1.20, 36, INK, True)
    return s


def card(s, x, y, w, h, heading, body, label=None, dark=False, body_size=21):
    box(s, x, y, w, h, SOFT, rounded=False)
    offset = .25
    if label:
        text(s, label, x+.25, y+.22, w-.5, .27, 12, TEAL, True)
        offset = .68
    text(s, heading, x+.25, y+offset, w-.5, .75, 24, INK, True)
    text(s, body, x+.25, y+offset+.94, w-.5, h-offset-1.05, body_size, MUTED)


NOTES = ['Apresentar o tema e o grupo. Somos quatro integrantes e vamos estudar como gerenciadores de pacotes organizam o software em Unix/Linux, incluindo Debian e FreeBSD. O foco será explicar decisões relacionadas a Sistemas Operacionais por meio de comparações e exemplos. Esta apresentação descreve a proposta; ainda não apresenta resultados de experimentos.', 'Começar com uma situação conhecida: instalamos um programa e ele precisa de componentes que não vieram sozinhos. Imagine que dois programas dependam de versões diferentes de uma biblioteca. Precisamos manter ambos funcionando. E, se a atualização for interrompida, precisamos entender o estado que restou. Isso conecta o tema a arquivos, execução de programas e recuperação. Não é necessário usar nomes de chamadas do kernel para explicar esse problema.', 'O recorte passa a ter cinco representantes em quatro famílias. Para binários tradicionais mutáveis, usaremos apenas APT e dpkg no Debian. Para código-fonte, a coleção de Ports do FreeBSD, que orienta a construção do software. No modelo funcional e imutável, apenas Nix. Na distribuição com sandbox, Flatpak e Snap. Os nomes entre parênteses indicam tecnologias que serão explicadas por sua função. Como incluímos FreeBSD, o tema agora abrange Unix/Linux; não vamos presumir que todos os exemplos compartilham o kernel Linux.', 'No Debian, APT e dpkg obtêm e instalam pacotes binários já preparados. No FreeBSD Ports, receitas coordenam obtenção do código-fonte, configuração, compilação e instalação. Isso permite discutir escolhas de construção e o trabalho adicional de CPU, memória e arquivos temporários. Não significa que compilar sempre deixe o programa mais rápido. APT/dpkg e Ports são os representantes escolhidos; o FreeBSD também possui distribuição binária, mas ela não é um representante adicional deste trabalho. Comparar esses tempos exige cuidado: construir e extrair um binário são operações diferentes, executadas em sistemas distintos.', 'Nix organiza resultados de construção em caminhos próprios e os trata como imutáveis. Diferentes variantes podem coexistir, e os perfis selecionam um conjunto de software. Isso favorece ambientes controlados e permite voltar a uma geração preservada. Imutabilidade não significa que todo o computador se tornou somente leitura. A construção pode usar fontes ou aproveitar binários em cache. A comparação com Debian é a organização das versões e o alcance da recuperação. Se uma aplicação alterou um banco de dados, retornar ao perfil anterior não desfaz automaticamente essa mudança.', 'Usar o exemplo de um editor: ele precisa do documento escolhido, mas não necessariamente de todos os arquivos do usuário. No Flatpak, OSTree organiza e distribui árvores de arquivos; Bubblewrap monta o ambiente isolado, com permissões e portais mediando o acesso. No Snap, SquashFS armazena a aplicação em uma imagem comprimida e somente para leitura; AppArmor aplica políticas de acesso, enquanto cgroups permitem contabilizar e, quando configurado, limitar recursos. O confinamento depende do modo e do suporte do ambiente. Armazenar arquivos e proteger processos são funções distintas; não precisamos detalhar as chamadas internas para explicá-las.', 'As mesmas perguntas orientarão os cinco representantes. Debian versus Ports permite discutir instalação binária e construção local. Debian versus Nix ajuda a discutir versões e recuperação. Flatpak versus Snap permite discutir distribuição e permissões. Recursos entram como uma consequência a observar: o primeiro aplicativo pode precisar de dependências extras que outro reaproveita. Não estabelecer um ranking antecipado nem atribuir toda diferença ao gerenciador.', 'O estudo documental abrange os cinco representantes. A prática organiza um exemplo por família: arquivos e dependências no Debian; etapas de construção de um port pequeno no FreeBSD; perfis no Nix; e permissões no Flatpak, contrastadas com o modelo Snap. São exemplos planejados, sujeitos a validação. FreeBSD requer ambiente próprio, como uma máquina virtual; não roda como um container Linux comum. Se o ambiente não estiver disponível, o exemplo Ports pode ser explicado documentalmente. Tempo e disco serão apoio, sem comparar diretamente compilação, extração e ativação de perfil como se fossem a mesma tarefa.', 'Apresentar apenas as entregas previstas. Semana 1: apresentação oral da proposta com tema, escopo e objetivos. Semana 2: relatório parcial 1 e slides com revisão e plano de testes. Semana 3: apresentação oral 2 com demonstrações das quatro famílias. Semana 4: relatório parcial 2 e slides com comparações e medidas. Semana 5: relatório final e slides com resultados, limites e conclusões. Estes são os marcos do cronograma do projeto. A divisão de tarefas entre integrantes não aparece neste slide.', 'Encerrar retomando o objetivo: construir uma comparação fundamentada que ajude a entender como o software é organizado, atualizado e executado sob as regras do sistema operacional. Esperamos entregar fichas comparativas, exemplos das quatro famílias e uma discussão de vantagens, custos e limites em contextos específicos. Não há um vencedor universal proposto. A contribuição é relacionar as decisões dos gerenciadores aos conceitos da disciplina. Agradecer e abrir espaço para perguntas.', 'Este slide é de apoio. Cada linha corresponde a um representante selecionado. Debian representa binários tradicionais mutáveis; FreeBSD Ports, construção a partir de fontes; Nix, organização funcional e imutável; Flatpak e Snap, distribuição de aplicações com mecanismos de isolamento. O foco é relacionar decisões a custos e garantias de SO, sem tratar famílias como equivalentes nem apresentar um ranking. A coleção de Ports utiliza receitas: não confundi-la com o gerenciador binário do FreeBSD.']

refs=[
('[1] Debian','Pacotes binários, arquivos e dependências.','https://www.debian.org/doc/manuals/debian-handbook/sect.package-meta-information.en.html'),
('[2] FreeBSD Ports','Receitas, configuração e compilação de software.','https://docs.freebsd.org/en/books/handbook/ports/'),
('[3] Nix','Variantes, imutabilidade e perfis.','https://nix.dev/manual/nix/latest/introduction'),
('[4] Flatpak','OSTree, distribuição e tecnologias utilizadas.','https://docs.flatpak.org/en/latest/under-the-hood.html'),
('[5] Bubblewrap','Ferramenta de isolamento usada pelo Flatpak.','https://github.com/containers/bubblewrap'),
('[6] Snap: arquitetura','Imagens SquashFS e revisões da aplicação.','https://snapcraft.io/docs/reference/system-architecture/'),
('[7] Snap: segurança','Políticas de acesso e mecanismos de proteção.','https://snapcraft.io/docs/explanation/security/security-policies/'),
('[8] Snap: recursos','Quotas e limites configuráveis de recursos.','https://snapcraft.io/docs/how-to-guides/manage-snaps/use-resource-quotas/'),
]

# Geometria final, sem reduzir as fontes: área útil à esquerda da faixa do INF.
LEFT, WIDTH = .58, 10.70

def heading(slide, title):
    text(slide,title,LEFT,.43,WIDTH,1.20,36,INK,True)


def panel(slide,x,y,w,h,name):
    box(slide,x,y,w,h,SOFT,rounded=False)
    text(slide,name,x+.24,y+.22,w-.48,.65,30,TEAL,True)


def page_number(slide, number, color=INK):
    text(slide,str(number),12.88,7.03,.36,.32,14,color,True)


s=new('Gerenciadores de pacotes em Unix/Linux','Capa','Pessoa 1','0:00–0:15',NOTES[0])
s['theme']='capa'
s['elements']=[]
text(s,'Gerenciadores de pacotes\nem Unix/Linux',.85,.70,11.5,1.85,48,INK,True,align='center')
text(s,'Arquivos, dependências,\natualizações e segurança',1.05,2.82,10.9,1.08,30,INK,align='center')
text(s,'Debian · FreeBSD Ports · Nix · Flatpak · Snap',.95,4.32,11.1,.58,26,INK,align='center')

s=new('Instalar um programa muda o sistema.','O problema','Pessoa 1','0:15–1:05',NOTES[1])
text(s,'Dois programas precisam de versões diferentes.',LEFT,1.77,WIDTH,.90,28,MUTED)
panel(s,LEFT,2.78,4.68,2.48,'Programa A')
panel(s,6.60,2.78,4.68,2.48,'Programa B')
text(s,'Biblioteca X\nVersão 1',.88,3.83,4.08,1.12,30,INK)
text(s,'Biblioteca X\nVersão 2',6.90,3.83,4.08,1.12,30,INK)
text(s,'≠',5.60,3.35,.70,.94,52,TEAL,True)
text(s,'Como manter os dois funcionando?',LEFT,5.86,WIDTH,.95,30,TEAL,True)

s=new('Cinco representantes, quatro famílias.','O recorte','Pessoa 1','1:05–1:50',NOTES[2])
for i,(name,family) in enumerate([
    ('Debian · APT/dpkg','Binários tradicionais mutáveis (FHS).'),
    ('FreeBSD Ports','Construção a partir do código-fonte.'),
    ('Nix','Modelo funcional e imutável.'),
    ('Flatpak e Snap','Aplicações com sandbox.')]):
    y=1.90+i*1.10
    box(s,LEFT,y,WIDTH,.97,SOFT if i%2==0 else WHITE,rounded=False)
    text(s,name,.80,y+.20,3.35,.82,27,TEAL,True)
    text(s,family,4.38,y+.16,6.58,.84,26,INK)

s=new('Pacote pronto ou código-fonte?','Debian e Ports','Pessoa 2','1:50–2:50',NOTES[3])
panel(s,LEFT,1.95,5.20,3.95,'Debian · APT/dpkg')
panel(s,6.06,1.95,5.20,3.95,'FreeBSD Ports')
text(s,'Instalar binários',.84,3.00,4.68,.97,30,INK,True)
text(s,'Baixar e instalar\nos arquivos.',.84,4.17,4.64,1.28,28,INK)
text(s,'Construir o software',6.32,3.00,4.68,.97,30,INK,True)
text(s,'Configurar, compilar\ne instalar.',6.32,4.17,4.64,1.28,28,INK)
text(s,'Compilar utiliza CPU, memória e arquivos temporários.',LEFT,6.20,WIDTH,.86,26,TEAL,True)

s=new('Nix: versões e recuperação.','Nix','Pessoa 2','2:50–3:50',NOTES[4])
for i,(name,body) in enumerate([
    ('Coexistir','Versões em\ncaminhos próprios.'),
    ('Selecionar','Perfil escolhe o\nambiente ativo.'),
    ('Recuperar','Retorno a uma\ngeração preservada.')]):
    x=LEFT+i*3.67
    panel(s,x,2.02,3.36,3.02,name)
    text(s,body,x+.23,3.25,2.90,1.48,26,INK)
text(s,'Voltar ao programa não significa\nvoltar a todos os dados.',LEFT,5.57,WIDTH,1.12,30,TEAL,True)

s=new('Flatpak e Snap: controle de acesso.','Proteção','Pessoa 3','3:50–4:55',NOTES[5])
panel(s,LEFT,1.95,5.20,4.14,'Flatpak')
panel(s,6.06,1.95,5.20,4.14,'Snap')
text(s,'OSTree',.84,2.98,4.68,.52,28,INK,True)
text(s,'Organiza e distribui arquivos.',.84,3.58,4.64,.92,26,INK)
text(s,'Bubblewrap',.84,4.58,4.68,.52,28,INK,True)
text(s,'Cria o ambiente isolado.',.84,5.18,4.64,.84,26,INK)
for y,name,desc in [(2.90,'SquashFS','Imagem comprimida.'),(3.96,'AppArmor','Políticas de acesso.'),(5.02,'cgroups','Limites configuráveis.')]:
    text(s,name,6.32,y,4.68,.52,27,INK,True)
    text(s,desc,6.32,y+.51,4.64,.47,26,INK)
text(s,'Acesso e limites dependem da configuração.',LEFT,6.38,WIDTH,.86,26,TEAL,True)

s=new('Critérios da comparação.','Comparação','Pessoa 3','4:55–5:50',NOTES[6])
for i,(label,desc) in enumerate([
    ('Arquivos','Local e registro dos arquivos.'),
    ('Dependências','Compatibilidade entre versões.'),
    ('Atualizações','Retorno a um estado utilizável.'),
    ('Proteção','Recursos que o aplicativo acessa.'),
    ('Recursos','Custo inicial e reaproveitamento.')]):
    y=1.91+i*.91
    box(s,LEFT,y,WIDTH,.80,SOFT if i%2==0 else WHITE,rounded=False)
    text(s,label,.80,y+.17,2.88,.47,26,TEAL,True)
    text(s,desc,3.87,y+.17,7.10,.47,26,INK)

s=new('Quatro famílias, quatro exemplos.','Método','Pessoa 4','5:50–6:50',NOTES[7])
for i,(label,desc) in enumerate([
    ('Debian','Consultar arquivos e dependências.'),
    ('FreeBSD Ports','Acompanhar uma compilação.'),
    ('Nix','Observar perfis e versões.'),
    ('Flatpak / Snap','Comparar acesso a recursos.')]):
    y=1.92+i*.98
    box(s,LEFT,y,WIDTH,.88,SOFT if i%2==0 else WHITE,rounded=False)
    text(s,label,.80,y+.17,3.42,.52,28,TEAL,True)
    text(s,desc,4.48,y+.19,6.46,.82,26,INK)
text(s,'FreeBSD: ambiente próprio para compilar.',LEFT,6.20,WIDTH,.86,26,TEAL,True)

s=new('Entregas previstas por semana.','Entregas','Pessoa 4','6:50–7:35',NOTES[8])
for i,(week,delivery) in enumerate([
    ('Semana 1','Apresentação oral: tema, escopo e objetivos.'),
    ('Semana 2','Relatório parcial 1 + slides: revisão e plano de testes.'),
    ('Semana 3','Apresentação oral 2: demonstrações das quatro famílias.'),
    ('Semana 4','Relatório parcial 2 + slides: comparação e medidas.'),
    ('Semana 5','Relatório final + slides: resultados, limites e conclusões.')]):
    y=1.70+i*.99
    box(s,LEFT,y,WIDTH,.91,SOFT if i%2==0 else WHITE,rounded=False)
    text(s,week,.80,y+.17,1.75,.52,26,TEAL,True)
    text(s,delivery,2.72,y+.06,8.25,.87,26,INK)

s=new('Que escolhas fazem sentido em cada contexto?','Encerramento','Pessoa 4','7:35–8:00',NOTES[9])
s['theme']='secao'
s['elements']=[]
text(s,'Que escolhas fazem\nsentido em cada contexto?',4.72,2.46,7.76,1.90,40,WHITE,True)
text(s,'Relacionar arquivos, dependências e proteção às escolhas dos gerenciadores.',4.75,4.68,7.35,1.45,28,WHITE)

s=new('Panorama dos cinco representantes.','Apoio','Apoio','Fora dos 8 minutos',NOTES[10])
box(s,LEFT,1.88,WIDTH,.65,TEAL,rounded=False)
text(s,'Representante',.80,2.02,3.55,.47,25,WHITE,True)
text(s,'O que comparar',4.43,2.02,6.43,.47,25,WHITE,True)
for i,(name,comparison) in enumerate([
    ('Debian · APT/dpkg','Arquivos, dependências e atualização.'),
    ('FreeBSD Ports','Compilação e uso de recursos.'),
    ('Nix','Versões e gerações de perfis.'),
    ('Flatpak','OSTree + Bubblewrap: distribuição e isolamento.'),
    ('Snap','SquashFS + AppArmor/cgroups: imagens, acesso e recursos.')]):
    y=2.55+i*.80
    box(s,LEFT,y,WIDTH,.80,SOFT if i%2==0 else WHITE,rounded=False)
    text(s,name,.80,y+.08,3.39,.77,24,INK,True)
    text(s,comparison,4.43,y+.06,6.56,.78,24,INK)

for i,spec in enumerate(slides,1):
    if i!=1:page_number(spec,i,WHITE if spec['theme']=='secao' else INK)

# PowerPoint: texto e diagramas editáveis sobre os fundos institucionais.
prs=Presentation()
prs.slide_width=Inches(W)
prs.slide_height=Inches(H)
prs.core_properties.title='Gerenciadores de pacotes em Unix/Linux — Semana 01'
prs.core_properties.subject='Gerenciadores de pacotes em Unix/Linux'
prs.core_properties.author=''
prs.core_properties.keywords='Unix, Linux, FreeBSD, Debian, Ports, Nix, Flatpak, Snap'
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
pptx_path=ROOT/'apresentacao-semana-01.pptx'
prs.save(pptx_path)

# PDF vetorial com fontes incorporadas, usando os mesmos elementos.
pdfmetrics.registerFont(TTFont('DeckRegular', FONTS[False]))
pdfmetrics.registerFont(TTFont('DeckBold', FONTS[True]))
pdf=pdfcanvas.Canvas(str(ROOT/'apresentacao-semana-01.pdf'),pagesize=(W*72,H*72))
pdf.setTitle('Gerenciadores de pacotes em Unix/Linux — Semana 01')
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
html='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gerenciadores de pacotes — Semana 01</title>
<style>*{box-sizing:border-box}body{margin:0;color:var(--foreground,#24343a);font:14px/1.5 system-ui,sans-serif}.toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:12px 0}button{font:inherit;color:inherit;background:var(--secondary,#e9eeeb);border:1px solid var(--border,#cbd9d2);border-radius:6px;padding:7px 12px;cursor:pointer}button:focus-visible{outline:3px solid #128d8a;outline-offset:2px}button:disabled{opacity:.4;cursor:default}#counter{margin-right:auto;font-variant-numeric:tabular-nums}.page{position:relative;overflow:hidden;display:none;width:100%}.page.active{display:block}.canvas{position:relative;width:1280px;height:720px;transform-origin:top left}.shape,.txt{position:absolute}.txt{font-family:'Liberation Sans',Arial,sans-serif;line-height:1.12;white-space:pre;overflow:visible}a{color:inherit;text-decoration:none}a:hover{text-decoration:underline}#notes{border-top:1px solid var(--border,#cbd9d2);margin-top:14px;padding:16px 0;line-height:1.7;white-space:pre-wrap}#notes[hidden]{display:none}#stage:fullscreen{background:#0c1d24;display:flex;align-items:center;justify-content:center}.hint{font-size:12px;opacity:.7;margin:0 0 10px}@media print{@page{size:13.333333in 7.5in;margin:0}html,body{width:13.333333in}.toolbar,.hint,#notes{display:none!important}.page{display:block!important;width:13.333333in!important;height:7.5in!important;break-after:page;print-color-adjust:exact;-webkit-print-color-adjust:exact}.page:last-child{break-after:auto}.canvas{transform:none!important}body{background:white}}
</style></head><body><div class="toolbar"><span id="counter" aria-live="polite"></span><button type="button" id="prev" aria-label="Slide anterior">← Anterior</button><button type="button" id="next" aria-label="Próximo slide">Próximo →</button><button type="button" id="toggle" aria-expanded="false" aria-controls="notes">Notas de fala</button><button type="button" id="full">Tela cheia</button><button type="button" id="print">Imprimir / PDF</button></div><p class="hint">Setas: navegar · F: tela cheia · N: notas · 10 slides principais + 1 de apoio</p><main id="stage">'''+''.join(html_slides)+'''</main><aside id="notes" hidden></aside><script>
const meta='''+metadata+''';const pages=[...document.querySelectorAll('.page')];let current=0;
function resize(){const fullscreen=!!document.fullscreenElement;const width=fullscreen?Math.min(innerWidth,innerHeight*16/9):document.getElementById('stage').clientWidth;for(const page of pages){page.style.width=width+'px';page.style.height=(width*9/16)+'px';page.firstElementChild.style.transform='scale('+(width/1280)+')';}}
function show(index){current=Math.max(0,Math.min(pages.length-1,index));pages.forEach((p,i)=>p.classList.toggle('active',i===current));document.getElementById('counter').textContent=(current+1)+' / '+pages.length+(current<10?' · Principal':' · Apoio');document.getElementById('prev').disabled=current===0;document.getElementById('next').disabled=current===pages.length-1;const m=meta[current];document.getElementById('notes').textContent=m.who+' · '+m.timing+'\\n\\n'+m.notes;resize();}
function toggleNotes(){const n=document.getElementById('notes');n.hidden=!n.hidden;document.getElementById('toggle').setAttribute('aria-expanded',String(!n.hidden));}
async function full(){try{if(document.fullscreenElement)await document.exitFullscreen();else await document.getElementById('stage').requestFullscreen();}catch(error){document.querySelector('.hint').textContent='Tela cheia indisponível neste visualizador. Abra o arquivo HTML no navegador.';}}
document.getElementById('prev').onclick=()=>show(current-1);document.getElementById('next').onclick=()=>show(current+1);document.getElementById('toggle').onclick=toggleNotes;document.getElementById('full').onclick=full;document.getElementById('print').onclick=()=>window.print();window.addEventListener('resize',resize);document.addEventListener('fullscreenchange',resize);document.addEventListener('keydown',event=>{if(event.altKey||event.ctrlKey||event.metaKey)return;if(['ArrowRight','PageDown',' '].includes(event.key)){event.preventDefault();show(current+1);}if(['ArrowLeft','PageUp'].includes(event.key)){event.preventDefault();show(current-1);}if(event.key==='Home')show(0);if(event.key==='End')show(pages.length-1);if(event.key.toLowerCase()==='n')toggleNotes();if(event.key.toLowerCase()==='f')full();});show(0);
</script></body></html>'''
bg_styles=':root{'+''.join('--bg-'+name+':url("data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'");' for name,path in BACKGROUNDS.items())+'}'
html=html.replace('<style>','<style>'+bg_styles,1)
(ROOT/'apresentacao-semana-01.html').write_text(html)

notes=['# Roteiro de fala — Semana 01','', 'Apresentação em grupo de quatro pessoas. Dez slides principais, com duração estimada de oito minutos, e um slide de apoio. Os tempos devem ser confirmados em ensaio. A divisão usa Pessoa 1–4 porque os nomes não foram fornecidos.','', 'PowerPoint: as notas também estão no modo do apresentador. HTML: tecla N exibe as notas. Para apresentar sem notas, mantenha-as fechadas e use tela cheia.','']
for i,s in enumerate(slides):
    notes.extend([f'## Slide {i+1} — {s["title"] or "Gerenciadores de pacotes em Unix/Linux"}', '', f'**{s["who"]} · {s["timing"]}**', '', s['notes'], ''])
notes.extend(['## Fontes', '']+[f'- [{a} — {b}]({url})' for a,b,url in refs])
(ROOT/'roteiro-de-fala.md').write_text('\n'.join(notes)+'\n')
loaded=Presentation(pptx_path)
assert len(loaded.slides)==11
assert all(slide.has_notes_slide for slide in loaded.slides)
print(f'Gerados {len(slides)} slides: PowerPoint, PDF vetorial, HTML offline e roteiro.')
print(f'PowerPoint: {pptx_path.stat().st_size:,} bytes. Textos dentro das caixas e elementos dentro dos slides.')
