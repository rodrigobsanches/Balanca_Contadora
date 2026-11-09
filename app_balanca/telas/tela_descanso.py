"""Tela 1 - Descanso: 'Aproxime seu chaveiro'."""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget

from telas.componentes import mudar_papel, rotulo


class TelaDescanso(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.titulo = rotulo("Balança contadora de peças", "subtitulo")
        self.chamada = rotulo("Aproxime seu chaveiro", "titulo")
        self.instrucao = rotulo("Encoste o chaveiro no leitor para começar", "subtitulo")
        self.mensagem = rotulo("", "info")
        self.mensagem.hide()
        self._esconder = QTimer(self, singleShot=True, timeout=self.mensagem.hide)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.addStretch(2)
        layout.addWidget(self.titulo)
        layout.addSpacing(20)
        layout.addWidget(self.chamada)
        layout.addWidget(self.instrucao)
        layout.addSpacing(30)
        layout.addWidget(self.mensagem)
        layout.addStretch(3)

    def definir_presenca(self, perto):
        if perto:
            self.chamada.setText("Olá! Encoste seu chaveiro")
            self.instrucao.setText("O leitor fica ao lado da balança")
        else:
            self.chamada.setText("Aproxime seu chaveiro")
            self.instrucao.setText("Encoste o chaveiro no leitor para começar")

    def mostrar_mensagem(self, texto, papel="info", segundos=4):
        self.mensagem.setText(texto)
        mudar_papel(self.mensagem, papel)
        self.mensagem.show()
        self._esconder.start(int(segundos * 1000))
