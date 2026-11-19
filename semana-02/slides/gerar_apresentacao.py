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


def card(s, x, y, w, h, heading, body, label=None, dark=False, body_size=21):
    box(s, x, y, w, h, SOFT, rounded=False)
    offset = .25
    if label:
        text(s, label, x+.25, y+.22, w-.5, .27, 12, TEAL, True)
        offset = .68
    text(s, heading, x+.25, y+offset, w-.5, .75, 24, INK, True)
    text(s, body, x+.25, y+offset+.94, w-.5, h-offset-1.05, body_size, MUTED)


# Conteúdo da apresentação. Fontes e detalhes permanecem nas notas.
LEFT, WIDTH = .58, 10.70
MAIN_COUNT = 15

refs = [
    ('Debian: APT e dpkg', 'Papéis das ferramentas e instalação.', 'https://www.debian.org/doc/manuals/debian-faq/pkgtools.en.html'),
    ('Debian: consultas', 'Arquivos instalados e metadados.', 'https://manpages.debian.org/trixie/dpkg/dpkg-query.1.en.html'),
    ('Debian: versões', 'Escolha de versões e prioridades.', 'https://manpages.debian.org/trixie/apt/apt_preferences.5.en.html'),
    ('FreeBSD Ports', 'Construção, configuração e instalação.', 'https://docs.freebsd.org/en/books/handbook/ports/'),
    ('FreeBSD: etapas', 'Fluxo de construção do port.', 'https://docs.freebsd.org/en/books/porters-handbook/slow-porting/'),
    ('FreeBSD: hello', 'Receita e opção NLS.', 'https://cgit.freebsd.org/ports/tree/misc/hello/Makefile'),
    ('Nix', 'Perfis e gerações.', 'https://nix.dev/manual/nix/2.34/package-management/profiles.html'),
    ('Flatpak', 'Dependências e runtimes.', 'https://docs.flatpak.org/en/latest/basic-concepts.html'),
    ('Flatpak: permissões', 'Acesso a arquivos e portais.', 'https://docs.flatpak.org/en/latest/sandbox-permissions.html'),
    ('Snap', 'Arquitetura e armazenamento.', 'https://snapcraft.io/docs/reference/system-architecture/'),
    ('Snap: confinamento', 'Modos e interfaces.', 'https://snapcraft.io/docs/explanation/security/snap-confinement/'),
    ('Snap: recursos', 'Quotas configuráveis para serviços.', 'https://snapcraft.io/docs/how-to-guides/manage-snaps/use-resource-quotas/'),
]


def panel(s, x, y, w, h, title):
    box(s, x, y, w, h, SOFT, rounded=False)
    text(s, title, x+.24, y+.22, w-.48, .67, 30, TEAL, True)


def rows(s, data, y=1.90, step=.96, label_w=3.15, size=26):
    for i, (label, body) in enumerate(data):
        top = y+i*step
        box(s, LEFT, top, WIDTH, step-.08, SOFT if i % 2 == 0 else WHITE, rounded=False)
        text(s, label, .80, top+.06, label_w, step-.12, size, TEAL, True)
        text(s, body, .80+label_w+.20, top+.06, WIDTH-label_w-.64, step-.12, size, INK)


def takeaway(s, content, y=6.30):
    text(s, content, LEFT, y, WIDTH, .83, 26, TEAL, True)


def number(s, i):
    text(s, str(i), 12.88, 7.03, .36, .32, 14, WHITE if s['theme']=='secao' else INK, True)


s = new('Gerenciadores de pacotes em Unix/Linux', 'Capa', 'Integrante 1', '0:00–0:15',
    'Apresentar a etapa: fundamentação e preparação dos exemplos da semana 2. O recorte permanece Debian com APT/dpkg, FreeBSD Ports, Nix, Flatpak e Snap. Esta apresentação consolida os materiais dos quatro integrantes. Há uma validação de Nix pelo terminal no ambiente de preparação; os demais procedimentos ainda exigem pilotos. A data dos registros é 5 de novembro de 2026. Os nomes do grupo não foram fornecidos, por isso a divisão aparece apenas nas notas como Integrante 1–4.')
s['theme']='capa'; s['elements']=[]
text(s, 'Gerenciadores de pacotes\nem Unix/Linux', .85, .70, 11.5, 1.85, 48, INK, True, align='center')
text(s, 'Semana 2\nFundamentação e plano de testes', 1.05, 2.80, 10.9, 1.16, 30, INK, align='center')
text(s, 'Debian · FreeBSD Ports · Nix · Flatpak · Snap', .95, 4.35, 11.1, .58, 26, INK, align='center')

s = new('O que muda para o sistema operacional?', 'Pergunta', 'Integrante 1', '0:15–0:50',
    'Explicar as perguntas comuns sem entrar em mecanismos internos. Instalar um programa envolve escolher componentes, colocar arquivos em locais conhecidos e definir como o processo será executado. A comparação vai observar arquivos, dependências, atualizações e recuperação, proteção e uso de recursos. Perguntar pela situação de uso é mais útil do que antecipar uma ferramenta vencedora.')
rows(s, [('Arquivos', 'Onde ficam os arquivos?'),
         ('Dependências', 'Como manter a compatibilidade?'),
         ('Atualizações', 'O que muda e pode ser recuperado?'),
         ('Proteção', 'Quais recursos o processo acessa?'),
         ('Recursos', 'Quanto custa preparar e manter?')], step=.94, label_w=2.95)

s = new('Debian: duas funções complementares.', 'Debian', 'Integrante 1', '0:50–1:35',
    'APT consulta repositórios, calcula uma solução para dependências e obtém os arquivos necessários. dpkg desempacota, configura e mantém o registro dos pacotes. APT/dpkg formam um único representante do trabalho. O dpkg verifica dependências, mas não vai buscá-las e instalá-las sozinho. apt update atualiza índices e é uma operação separada de apt install. APT pode usar fontes em sources.list e arquivos de sources.list.d. Uma atualização altera o conjunto instalado; escolher uma versão ou definir pinning não cria, por si só, ambientes separados por projeto.',
    sources=refs[0][2]+'; '+refs[2][2])
panel(s, LEFT, 1.95, 5.20, 3.96, 'APT')
panel(s, 6.06, 1.95, 5.20, 3.96, 'dpkg')
text(s, 'Consulta repositórios.\nResolve dependências.\nObtém os pacotes.', .84, 3.02, 4.66, 2.32, 28, INK)
text(s, 'Instala e configura.\nRegistra pacotes.\nPermite consultar arquivos.', 6.32, 3.02, 4.66, 2.32, 28, INK)
takeaway(s, 'O pacote instalado passa a compor o sistema.')

s = new('Debian: arquivos e dependências.', 'Piloto Debian', 'Integrante 1', '1:35–2:15',
    'O material do integrante 1 escolheu tmux como exemplo. O estado de execução estava em aberto no PDF; não foram fornecidos logs ou a versão do Debian. O piloto está planejado. Instalar o programa, consultar dependências e observar os arquivos registrados. Em dpkg -l, interpretar o estado, não apenas a presença do nome. dpkg -L lista arquivos do pacote; dpkg -S permite consultar a qual pacote um arquivo pertence. Mostrar duas ou três linhas e explicar seu significado. Não é necessário colocar todas as saídas no slide. Para projetos incompatíveis, o controle de versões do pacote não substitui uma solução de ambiente independente.',
    sources=refs[1][2]+'; '+refs[2][2])
rows(s, [('Instalar', 'sudo apt install tmux'),
         ('Dependências', 'apt-cache depends tmux'),
         ('Arquivos', 'dpkg -L tmux'),
         ('Versão e estado', 'dpkg -l tmux')], step=1.02, label_w=3.35)
takeaway(s, 'Piloto planejado: registrar ambiente e saídas reais.')

s = new('Ports: da receita ao programa instalado.', 'FreeBSD Ports', 'Integrante 2', '2:15–3:00',
    'O port é a receita, e não o programa já compilado. O framework coordena obtenção e verificação das fontes, extração, patches, configuração, construção, staging, geração e instalação do pacote. A sequência no slide agrupa fases para facilitar a explicação. Os arquivos de trabalho são temporários; o pacote instalado e os distfiles têm outros ciclos de vida. make install clean encadeia os alvos necessários e limpa a área de trabalho. FreeBSD utiliza seu próprio ambiente: uma VM com FreeBSD é uma opção para o piloto. O uso de pkg como ferramenta de registro ou instalação não adiciona outro representante ao recorte.',
    sources=refs[3][2]+'; '+refs[4][2])
for i, (title, body) in enumerate([
    ('Obter', 'Fontes e integridade.'), ('Configurar', 'Patches e opções.'), ('Construir', 'Compilação e dependências.'),
    ('Preparar', 'Árvore temporária.'), ('Empacotar', 'Arquivos instaláveis.'), ('Instalar', 'Registro pelo pkg.')]):
    x = LEFT+(i%3)*3.67; y = 1.95+(i//3)*2.12
    panel(s, x, y, 3.36, 1.91, title)
    text(s, body, x+.23, y+.99, 2.90, .83, 26, INK)
takeaway(s, 'A receita define como o software será construído.')

s = new('Ports: personalizar tem um custo.', 'Piloto Ports', 'Integrante 2', '3:00–3:45',
    'O material do integrante 2 escolheu misc/hello, um programa pequeno. A receita consultada oferece NLS, suporte a idiomas. O piloto deve verificar a opção na árvore de Ports utilizada, registrar seu estado e acompanhar uma construção. A escolha fornece um exemplo concreto de personalização sem exigir detalhes de ABI, hardening, poudriere ou jails na apresentação. Registrar FreeBSD, arquitetura, revisão da árvore e opções. O custo envolve fontes, dependências, CPU, memória e arquivos temporários. A obtenção de um binário pronto evita a construção local, mas não permite concluir menor manutenção em todas as situações. Nenhum resultado medido de Ports foi fornecido.',
    sources=refs[3][2]+'; '+refs[5][2])
panel(s, LEFT, 1.95, 5.20, 3.96, 'Exemplo: misc/hello')
panel(s, 6.06, 1.95, 5.20, 3.96, 'O que registrar')
text(s, 'NLS: suporte a idiomas.\nEscolher a opção.\nConstruir e executar.', .84, 3.02, 4.66, 2.32, 28, INK)
text(s, 'Tempo e dependências.\nCPU, memória e disco.\nReceita e configuração.', 6.32, 3.02, 4.66, 2.32, 28, INK)
takeaway(s, 'Piloto planejado em um ambiente FreeBSD.')

s = new('Nix: armazenar, selecionar e recuperar.', 'Nix', 'Integrante 3', '3:45–4:30',
    'O store guarda resultados de construção em caminhos próprios. Os perfis selecionam referências aos programas; gerações registram estados de um perfil. O modelo permite coexistência de variantes, mas ter dois perfis não comprova duas versões diferentes. Arquivos de configuração e revisão fixa ajudam a repetir um ambiente. O exemplo inclui flake.nix e flake.lock. Nix pode obter binários em cache; não é obrigatório compilar tudo localmente. A imutabilidade dos resultados do store não torna documentos do usuário imutáveis nem confina automaticamente o editor.',
    sources=refs[6][2]+'; https://nix.dev/tutorials/first-steps/towards-reproducibility-pinning-nixpkgs')
for i, (title, body) in enumerate([
    ('Store', 'Componentes em\ncaminhos próprios.'),
    ('Perfil', 'Seleciona quais\nprogramas utilizar.'),
    ('Geração', 'Preserva uma\nseleção anterior.')]):
    x = LEFT+i*3.67
    panel(s, x, 2.02, 3.36, 3.02, title)
    text(s, body, x+.23, 3.24, 2.90, 1.48, 26, INK)
text(s, 'A configuração registra as escolhas\npara repetir o ambiente.', LEFT, 5.58, WIDTH, 1.11, 30, TEAL, True)

s = new('Nix: o que foi validado pelo terminal.', 'Piloto Nix', 'Integrante 3', '4:30–5:20',
    'Validação de preparação feita pelo assistente em 5 de novembro de 2026, não apresentação executada pelos integrantes. Nix 2.34.9 no NixOS x86_64-linux, GNOME Text Editor 50.1 e revisão fixa da coleção de pacotes. Os perfis A e B selecionaram o mesmo executável. Remover de A não alterou B. O retorno à geração anterior recuperou a seleção de A. Um documento alterado por Python permaneceu alterado; a edição não foi realizada pela janela. Foi repetida a obtenção numa cópia em outra pasta da mesma máquina. Não foram demonstradas duas versões diferentes, atualização entre versões, abertura gráfica ou repetição em outro computador. Evidências: semana-02/nix/evidencias/validacao.md.',
    sources=refs[6][2])
rows(s, [('Dois perfis', 'A e B selecionam o mesmo editor 50.1.'),
         ('Remoção em A', 'B continua com o editor disponível.'),
         ('Retorno de A', 'A geração anterior recupera a seleção.'),
         ('Documento', 'O texto alterado permanece alterado.')], step=1.02, label_w=3.25)
takeaway(s, 'Pendentes: janela gráfica e repetição em outra máquina.')

s = new('Flatpak: dependências e acesso.', 'Flatpak', 'Integrante 4', '5:20–6:10',
    'O manifesto descreve como construir a aplicação, suas dependências e permissões. O runtime oferece uma base compartilhável; componentes adicionais podem acompanhar a aplicação. O SDK fornece ferramentas de construção. OSTree administra conteúdo versionado, e Bubblewrap participa da criação do ambiente isolado. Os portais mediam operações como escolher um arquivo. O isolamento efetivo depende da política do pacote e das configurações locais. A receita consultada do GNOME Text Editor declara filesystem=host: não devemos presumir bloqueio da pasta pessoal. A fonte 51.0 no manifesto não comprova a versão instalada ou disponível a todas as arquiteturas. Não houve instalação ou execução de Flatpak neste ambiente.',
    sources=refs[7][2]+'; '+refs[8][2]+'; https://docs.flatpak.org/en/latest/under-the-hood.html')
rows(s, [('Runtime', 'Bibliotecas que aplicações podem compartilhar.'),
         ('OSTree', 'Organiza e distribui conteúdo versionado.'),
         ('Bubblewrap', 'Monta o ambiente isolado do processo.'),
         ('Permissões', 'Definem e mediam o acesso aos recursos.')], step=1.02, label_w=3.15)
takeaway(s, 'Um pacote pode conceder acesso amplo aos arquivos.')

s = new('Snap: imagem e regras de execução.', 'Snap', 'Integrante 4', '6:10–7:00',
    'O Snapcraft produz o pacote a partir de snapcraft.yaml. O snapd administra instalação e revisões. SquashFS armazena o pacote numa imagem comprimida e somente leitura, montada ao instalar a revisão. Não se monta toda a imagem de novo a cada lançamento. AppArmor participa da aplicação das políticas; interfaces concedem acessos. cgroups agrupam processos e apoiam controles: quotas configuradas para serviços não significam um limite automático de CPU ou memória para todo editor. Strict, classic e devmode têm alcances diferentes, e o suporte do hospedeiro precisa ser conferido. A consulta ao catálogo para amd64 registrou editor 48.3, revisão 53, base core24 e metadado strict; isso não comprova confinamento efetivo numa máquina. Não houve execução de Snap neste ambiente.',
    sources=refs[9][2]+'; '+refs[10][2]+'; '+refs[11][2])
rows(s, [('SquashFS', 'Imagem comprimida e somente leitura.'),
         ('AppArmor', 'Participa das políticas de acesso.'),
         ('Interfaces', 'Conectam a aplicação aos recursos.'),
         ('cgroups', 'Agrupam processos para controle de recursos.')], step=1.02, label_w=3.15)
takeaway(s, 'A proteção depende do modo e do suporte do SO.')

s = new('Quatro VMs para os testes.', 'Plano das VMs', 'Integrante 1', '7:00–8:00',
    'Apresentar a organização planejada: as VMs ainda precisam ser preparadas e validadas. VM 1: Debian com APT/dpkg para instalar pacotes, consultar dependências e observar os arquivos. VM 2: FreeBSD com Ports para escolher uma opção e acompanhar a construção do software. VM 3: a mesma base Debian com Nix para selecionar ambientes e testar a recuperação de perfis. A validação anterior de Nix ocorreu em NixOS; ela não comprova execução nessa nova VM. VM 4: Debian com dois estados separados, um para Flatpak e outro para Snap, para observar permissões e acesso ao mesmo documento. Restaurar a base limpa antes de preparar o outro cenário e preservar um estado anterior à instalação da aplicação em cada um. Usar o mesmo computador, hipervisor e orçamento de hardware virtual, executando uma VM por vez. Registrar as diferenças de sistema e versões: o cenário Ports também inclui as diferenças entre FreeBSD e Linux. Restaurar um snapshot organiza o experimento; não é uma evidência de rollback oferecido pelo gerenciador. Quatro VMs cobrem os cinco representantes porque Flatpak e Snap serão testados separadamente na quarta VM.',
    sources='https://nix.dev/install-nix.html; '+refs[3][2]+'; '+refs[8][2]+'; '+refs[10][2])
for i, (title, body) in enumerate([
    ('VM 1 · Debian', 'APT/dpkg: instalar pacotes\ne consultar dependências.'),
    ('VM 2 · FreeBSD', 'Ports: configurar opções\ne compilar o software.'),
    ('VM 3 · Debian + Nix', 'Nix: selecionar ambientes\ne recuperar perfis.'),
    ('VM 4 · Debian', 'Flatpak e Snap: permissões\nem snapshots separados.')]):
    x = LEFT+(i%2)*5.48
    y = 1.85+(i//2)*2.27
    panel(s, x, y, 5.20, 2.05, title)
    text(s, body, x+.24, y+1.03, 4.72, .92, 26, INK)
takeaway(s, 'Mesmo hardware virtual; uma VM em teste por vez.', y=6.40)

s = new('Como organizar a comparação prática?', 'Método', 'Integrante 2', '8:00–9:00',
    'A tarefa comum proposta usa GNOME Text Editor: abrir comparacao.txt, editar, salvar outro arquivo e reabrir. A disponibilidade foi pesquisada para os cinco representantes, mas a execução precisa ser validada em cada ambiente. No FreeBSD, a dependência de uma sessão gráfica e o custo de construir bibliotecas podem dificultar o piloto. Os materiais de Debian e Ports já propõem tmux e hello: eles permanecem como ilustrações dos mecanismos. É possível comparar estrutura com programas diferentes, mas não usar os seus tempos ou tamanhos como ranking direto. Se o editor não for viável, registrar a limitação e definir exemplos comuns por comparação antes das medidas. Comparar preparação, compilação e ativação como etapas distintas.')
panel(s, LEFT, 1.95, WIDTH, 2.16, 'Tarefa comum proposta: editor de texto')
text(s, 'Abrir → editar → salvar → reabrir.', .84, 3.00, 10.17, .84, 30, INK)
text(s, 'tmux e hello ilustram mecanismos específicos.', LEFT, 4.55, WIDTH, .90, 28, INK)
text(s, 'Medir exige tarefa e condições comparáveis.', LEFT, 5.68, WIDTH, 1.00, 30, TEAL, True)

s = new('Pesquisa, validação e pendências.', 'Estado atual', 'Integrante 3', '9:00–10:00',
    'Relatar o estado do material, não afirmar que o grupo terminou os testes. Debian e Ports: os PDFs forneceram fundamentação e exemplos planejados, sem registros suficientes para confirmar execução. Nix: há validação pelo terminal no ambiente de preparação; tarefa gráfica e outro computador pendentes. Flatpak e Snap: receitas, catálogo e documentação conferidos; ferramentas ausentes e nenhuma execução neste ambiente. A checagem documental não é um teste de permissões. Ainda não existe uma bateria comparativa de tempo, CPU, RAM ou disco entre os gerenciadores. As versões de editor também diferem nas fontes consultadas.')
rows(s, [('Debian', 'Material integrado; piloto ainda sem evidências.'),
         ('FreeBSD Ports', 'Material integrado; construção por validar.'),
         ('Nix', 'Terminal validado; etapa gráfica pendente.'),
         ('Flatpak / Snap', 'Checagem documental; execução pendente.')], step=1.02, label_w=3.25)
takeaway(s, 'Ainda não há medidas comparativas de desempenho.')

s = new('Da preparação às conclusões.', 'Próximos passos', 'Integrante 4', '10:00–11:00',
    'Semana 2: fundamentação e plano consolidados nesta entrega. Na semana 3, ensaiar e demonstrar os exemplos das quatro famílias, registrar ambiente e versões e guardar saídas reais. Na semana 4, executar as comparações definidas em condições registradas e interpretar custos por etapa. Na semana 5, reunir resultados, limites e recomendações por necessidade. Cada integrante executa seu piloto e outro revisa as instruções. Não é necessário acrescentar ferramentas ao recorte. Se um ambiente ficar indisponível, declarar a parte documental e limitar a conclusão prática.')
for i, (title, body) in enumerate([
    ('Semana 3', 'Demonstrar e\nguardar evidências.'),
    ('Semana 4', 'Comparar e medir\nas etapas definidas.'),
    ('Semana 5', 'Concluir com\nresultados e limites.')]):
    x=LEFT+i*3.67
    panel(s, x, 2.02, 3.36, 3.30, title)
    text(s, body, x+.23, 3.25, 2.90, 1.72, 26, INK)
text(s, 'Registrar sempre ambiente, versão\ne procedimento realizado.', LEFT, 5.78, WIDTH, 1.10, 28, TEAL, True)

s = new('A escolha depende da tarefa.', 'Encerramento', 'Integrante 4', '11:00–11:30',
    'Concluir que as decisões dos gerenciadores afetam armazenamento, compatibilidade, manutenção e proteção. O trabalho já possui fundamentação e exemplos definidos, mas ainda precisa completar os pilotos e a comparação controlada. Para quem desenvolve software, distinguir preparar ferramentas de um projeto e distribuir uma aplicação. Uma recomendação deve indicar necessidade, benefício e custo, apoiada em fontes e evidências. Encerrar e abrir para perguntas; os dois slides seguintes são de apoio e não fazem parte do tempo principal.')
s['theme']='secao'; s['elements']=[]
text(s, 'A escolha depende\nda tarefa.', 4.72, 2.46, 7.76, 1.90, 44, WHITE, True)
text(s, 'Arquivos, compatibilidade,\nmanutenção e proteção.', 4.75, 4.65, 7.35, 1.35, 30, WHITE)

s = new('Como registrar cada teste?', 'Apoio', 'Apoio', 'Fora do tempo principal',
    'Um registro útil permite repetir o procedimento: responsável, data, sistema, arquitetura, versões, fontes e revisões, comandos com saída e interpretação. Para medir, registrar estado inicial, caches, dependências já presentes e acesso à rede. Separar download, compilação, instalação e execução. Guardar valores individuais antes de resumir. Não confundir fechamento de dependências com crescimento exclusivo do disco. Em Nix, o fechamento consultado incluía componentes compartilhados já existentes; ele não representa todo o espaço novo causado pela instalação.')
rows(s, [('Ambiente', 'SO, arquitetura e versões.'),
         ('Procedimento', 'Comandos e configuração utilizados.'),
         ('Estado inicial', 'Dependências, cache e rede.'),
         ('Evidência', 'Saída real, captura e resultado.'),
         ('Interpretação', 'O que demonstra e quais são os limites.')], step=.94, label_w=3.15)

s = new('Recuperar software e recuperar dados.', 'Apoio', 'Apoio', 'Fora do tempo principal',
    'Detalhar o alcance de recuperação. Nix: retornar um perfil seleciona uma geração preservada e não reverte documentos. Flatpak: selecionar um commit anterior exige sua disponibilidade e não desfaz automaticamente alterações em documentos. Snap: revert pode recuperar uma revisão preservada e dados/configuração associados à revisão; common e documentos externos não são automaticamente revertidos. Debian/Ports não oferecem, por esse fluxo básico de instalação, uma restauração completa de todos os dados: disponibilidade de versões, compatibilidade e backups precisam ser avaliados. Não há teste comparativo de recuperação entre todos os gerenciadores nesta preparação.',
    sources='https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-profile-rollback.html; https://docs.flatpak.org/en/latest/flatpak-command-reference.html#flatpak-update; https://snapcraft.io/docs/how-to-guides/manage-snaps/manage-updates/')
rows(s, [('Nix', 'Perfil anterior; documentos fora do retorno.'),
         ('Flatpak', 'Commit disponível; documentos preservados.'),
         ('Snap', 'Revisão e dados associados; common fica fora.')], step=1.13, label_w=2.65)
text(s, 'O alcance depende do estado recuperado\ne da localização dos dados.', LEFT, 5.70, WIDTH, 1.13, 30, TEAL, True)

for i, spec in enumerate(slides, 1):
    if i != 1:
        number(spec, i)


# PowerPoint: texto e diagramas editáveis sobre os fundos institucionais.
prs=Presentation()
prs.slide_width=Inches(W)
prs.slide_height=Inches(H)
prs.core_properties.title='Gerenciadores de pacotes em Unix/Linux — Semana 02'
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
pptx_path=ROOT/'apresentacao-semana-02.pptx'
prs.save(pptx_path)

# PDF vetorial com fontes incorporadas, usando os mesmos elementos.
pdfmetrics.registerFont(TTFont('DeckRegular', FONTS[False]))
pdfmetrics.registerFont(TTFont('DeckBold', FONTS[True]))
pdf=pdfcanvas.Canvas(str(ROOT/'apresentacao-semana-02.pdf'),pagesize=(W*72,H*72))
pdf.setTitle('Gerenciadores de pacotes em Unix/Linux — Semana 02')
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
html='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gerenciadores de pacotes — Semana 02</title>
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
(ROOT/'apresentacao-semana-02.html').write_text(html)

notes=['# Roteiro de fala — Semana 02','', 'Apresentação em grupo de quatro pessoas. Quinze slides principais, com duração estimada de 11 minutos e 30 segundos, e dois slides de apoio. Os tempos devem ser confirmados em ensaio. A divisão usa Integrante 1–4 porque os nomes não foram fornecidos.','', 'PowerPoint: as notas também estão no modo do apresentador. HTML: tecla N exibe as notas. Para apresentar sem notas, mantenha-as fechadas e use tela cheia.','']
for i,s in enumerate(slides):
    notes.extend([f'## Slide {i+1} — {s["title"] or "Gerenciadores de pacotes em Unix/Linux"}', '', f'**{s["who"]} · {s["timing"]}**', '', s['notes'], ''])
notes.extend(['## Fontes', '']+[f'- [{a} — {b}]({url})' for a,b,url in refs])
(ROOT/'roteiro-de-fala.md').write_text('\n'.join(notes)+'\n')
loaded=Presentation(pptx_path)
assert len(loaded.slides)==17
assert all(slide.has_notes_slide for slide in loaded.slides)
print(f'Gerados {len(slides)} slides: PowerPoint, PDF vetorial, HTML offline e roteiro.')
print(f'PowerPoint: {pptx_path.stat().st_size:,} bytes. Textos dentro das caixas e elementos dentro dos slides.')
