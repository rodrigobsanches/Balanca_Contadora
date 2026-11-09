"""Tela 3a - Inventario: escolher o produto (botoes grandes, sem digitar)."""
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from telas.componentes import botao, rotulo
from telas.estilo import formatar_numero, formatar_peso

COLUNAS = 3


class TelaProdutos(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        titulo = rotulo("Inventário: escolha o produto", "titulo")
        voltar = botao("Voltar", "secundario", janela.ir_menu, altura=70)
        voltar.setMaximumWidth(220)

        topo = QHBoxLayout()
        topo.addWidget(titulo, 1)
        topo.addWidget(voltar)

        self.grade_widget = QWidget()
        self.grade = QGridLayout(self.grade_widget)
        self.grade.setSpacing(18)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setWidget(self.grade_widget)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.addLayout(topo)
        layout.addWidget(rolagem, 1)

    def recarregar(self):
        while self.grade.count():
            item = self.grade.takeAt(0)
            if item.widget():
                item.widget().hide()          # some na hora; o deleteLater apaga depois
                item.widget().deleteLater()
        produtos = self.janela.ctrl.produtos()
        if not produtos:
            self.grade.addWidget(rotulo(
                "Nenhum produto ainda.\nLigue a ESP32 com internet para baixar os cadastros.",
                "subtitulo"), 0, 0)
            return
        for i, (codigo, p) in enumerate(sorted(produtos.items())):
            b = botao(self._texto(codigo, p), "produto", altura=130)
            b.clicked.connect(lambda _=False, c=codigo: self.janela.abrir_contagem(c))
            self.grade.addWidget(b, i // COLUNAS, i % COLUNAS)
        self.grade.setRowStretch(len(produtos) // COLUNAS + 1, 1)

    @staticmethod
    def _texto(codigo, p):
        unit = p.get("peso_unit_g")
        peso = ("%s por peça" % formatar_peso(unit)) if unit else "sem peso: usar amostra"
        estoque = formatar_numero(p.get("estoque_atual", 0))
        return "%s\n%s\n%s  ·  estoque %s" % (p.get("nome", codigo), codigo, peso, estoque)
