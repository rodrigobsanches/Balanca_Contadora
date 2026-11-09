"""Tela 2 - Menu: nome do operador + Inventario, Conferencia de despacho e Sair."""
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from telas.componentes import botao, rotulo


class TelaMenu(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.ola = rotulo("Olá!", "titulo")
        pergunta = rotulo("O que vamos fazer?", "subtitulo")

        inventario = botao("Inventário\ncontar o estoque", ao_clicar=janela.abrir_inventario, altura=230)
        conferencia = botao("Conferência\nde despacho", "secundario",
                            ao_clicar=janela.abrir_conferencia, altura=230)
        sair = botao("Sair", "perigo", ao_clicar=janela.ctrl.sair, altura=80)
        sair.setMaximumWidth(260)

        opcoes = QHBoxLayout()
        opcoes.setSpacing(40)
        opcoes.addWidget(inventario)
        opcoes.addWidget(conferencia)

        rodape = QHBoxLayout()
        rodape.addStretch()
        rodape.addWidget(sair)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 30, 80, 30)
        layout.addWidget(self.ola)
        layout.addWidget(pergunta)
        layout.addStretch(1)
        layout.addLayout(opcoes)
        layout.addStretch(1)
        layout.addLayout(rodape)

    def definir_operador(self, nome):
        primeiro = nome.split()[0] if nome else ""
        self.ola.setText("Olá, %s!" % primeiro)
