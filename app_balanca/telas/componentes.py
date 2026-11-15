"""Pecas reaproveitadas pelas telas: botao grande, rotulo com papel, cartao, barra de taras."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


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
