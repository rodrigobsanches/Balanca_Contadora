"""Pecas reaproveitadas pelas telas: botao grande, rotulo com papel, cartao."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton


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
    """Texto. papel: 'titulo', 'subtitulo', 'gigante', 'peso', 'aviso', 'erro', 'info'."""
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
