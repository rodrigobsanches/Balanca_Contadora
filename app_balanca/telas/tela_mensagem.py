"""Tela de resultado: 'Registrado!' em verde (ou erro em vermelho) por alguns segundos."""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget

from telas.componentes import botao, mudar_papel, rotulo
from telas.estilo import COR

PAPEIS = {"sucesso": "info", "erro": "erro", "info": "info"}


class TelaMensagem(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self._depois = None
        self.titulo = rotulo("", "titulo")
        self.texto = rotulo("", "info")
        self._timer = QTimer(self, singleShot=True, timeout=self.continuar)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(120, 40, 120, 40)
        layout.addStretch()
        layout.addWidget(self.titulo)
        layout.addSpacing(20)
        layout.addWidget(self.texto)
        layout.addSpacing(40)
        layout.addWidget(botao("Continuar", ao_clicar=self.continuar, altura=90))
        layout.addStretch()

    def mostrar(self, titulo, texto, tipo="sucesso", depois=None, segundos=3):
        self._depois = depois
        self.titulo.setText(titulo)
        self.texto.setText(texto)
        mudar_papel(self.texto, PAPEIS.get(tipo, "info"))
        cor = COR.get(tipo, COR["primaria"])
        self.texto.setStyleSheet("background: %s;" % cor)
        self._timer.start(int(segundos * 1000))

    def continuar(self):
        self._timer.stop()
        depois, self._depois = self._depois, None
        if depois:
            depois()
