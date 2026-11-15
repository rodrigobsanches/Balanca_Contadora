"""Pecas reaproveitadas pelas telas: botao grande, rotulo com papel, cartao, barra de taras
e o esqueleto comum das telas (cabecalho em cima, conteudo, barra de botoes embaixo).

Padrao de todas as telas (mudou aqui, muda em todas):
- cabecalho alinhado a esquerda: titulo + linha de apoio;
- rodape: Voltar/Cancelar na ESQUERDA, a acao principal na DIREITA, todos da mesma altura.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

MARGENS = (32, 16, 32, 16)       # esquerda, cima, direita, baixo (igual em todas as telas)
ESPACO = 16                      # entre cabecalho, conteudo e rodape
ALTURA_RODAPE = 80               # altura dos botoes da barra de baixo
LARGURA_RODAPE = 260             # largura minima dos botoes da barra de baixo


def botao(texto, tipo=None, ao_clicar=None, altura=90):
    """Botao de toque. tipo: None (azul), 'secundario', 'sucesso', 'perigo', 'produto', 'pequeno'."""
    b = QPushButton(texto)
    if tipo:
        b.setProperty("tipo", tipo)
    b.setMinimumHeight(altura)
    b.setCursor(Qt.PointingHandCursor)
    if ao_clicar:
        b.clicked.connect(ao_clicar)
    return b


def rotulo(texto="", papel=None, alinhamento=Qt.AlignCenter):
    """Texto. papel: 'titulo', 'subtitulo', 'gigante', 'peso', 'aviso', 'erro', 'ok', 'info'."""
    r = QLabel(texto)
    if papel:
        r.setProperty("papel", papel)
    r.setAlignment(alinhamento)
    r.setWordWrap(True)
    return r


def mudar_papel(r, papel):
    """Troca o estilo de um rotulo ja criado (ex.: de 'info' para 'erro')."""
    r.setProperty("papel", papel)
    r.style().unpolish(r)
    r.style().polish(r)


def cartao():
    f = QFrame()
    f.setObjectName("cartao")
    return f


class BarraTaras(QWidget):
    """Botoes de tara pre-programada (ex.: "Pote 26 g"), cadastrados no dashboard.
    Usada nas telas de contagem e de amostra; recarregar() a cada vez que a tela abre."""
    def __init__(self, balanca, altura=70):
        super().__init__()
        self.balanca = balanca
        self.altura = altura
        self.botoes = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def recarregar(self, taras):
        for b in self.botoes:
            self._layout.removeWidget(b)
            b.hide()                      # some na hora; o deleteLater apaga depois
            b.deleteLater()
        self.botoes = []
        for t in taras:
            g = t["g"]
            texto = "%s\n%s g" % (t["nome"], ("%g" % g).replace(".", ","))
            b = botao(texto, "pequeno", lambda _=False, g=g: self.balanca.tara_predefinida(g),
                      self.altura)
            self._layout.addWidget(b)
            self.botoes.append(b)
        self.setVisible(bool(self.botoes))


def cabecalho(titulo="", subtitulo=""):
    """Titulo grande + linha de apoio, alinhados a esquerda. Devolve (layout, titulo, subtitulo)."""
    t = rotulo(titulo, "titulo", Qt.AlignLeft | Qt.AlignVCenter)
    s = rotulo(subtitulo, "subtitulo", Qt.AlignLeft | Qt.AlignVCenter)
    caixa = QVBoxLayout()
    caixa.setSpacing(0)
    caixa.addWidget(t)
    caixa.addWidget(s)
    return caixa, t, s


def rodape(esquerda=(), direita=()):
    """Barra de botoes de baixo: 'esquerda' (Voltar/Cancelar) e 'direita' (acao principal por ultimo)."""
    linha = QHBoxLayout()
    linha.setSpacing(ESPACO)
    for b in list(esquerda) + list(direita):
        b.setMinimumHeight(ALTURA_RODAPE)
        b.setMinimumWidth(LARGURA_RODAPE)
    for b in esquerda:
        linha.addWidget(b)
    linha.addStretch()
    for b in direita:
        linha.addWidget(b)
    return linha


def montar_tela(widget, topo, corpo, base=None):
    """Esqueleto comum: topo (cabecalho), corpo (ocupa o resto) e base (rodape)."""
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(*MARGENS)
    layout.setSpacing(ESPACO)
    for parte, esticar in ((topo, 0), (corpo, 1), (base, 0)):
        if parte is None:
            continue
        if isinstance(parte, QWidget):
            layout.addWidget(parte, esticar)
        else:
            layout.addLayout(parte, esticar)
    return layout


def rolagem(conteudo):
    """Area com rolagem vertical (listas que podem crescer); nunca rola para o lado."""
    r = QScrollArea()
    r.setWidgetResizable(True)
    r.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    r.setWidget(conteudo)
    return r


def limpar_layout(layout):
    """Tira e apaga tudo de um layout (listas montadas de novo a cada abertura)."""
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().hide()          # some na hora; o deleteLater apaga depois
            item.widget().deleteLater()
