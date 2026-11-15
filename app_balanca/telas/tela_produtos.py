"""Tela 3a - Inventario: escolher o produto (botoes grandes, sem digitar)."""
from PySide6.QtWidgets import QGridLayout, QWidget

from telas.componentes import botao, cabecalho, limpar_layout, montar_tela, rodape, rolagem, rotulo
from telas.estilo import formatar_numero, formatar_peso

COLUNAS = 3


class TelaProdutos(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        topo, _, _ = cabecalho("Inventário", "Escolha o produto para contar")

        self.grade_widget = QWidget()
        self.grade = QGridLayout(self.grade_widget)
        self.grade.setContentsMargins(0, 0, 0, 0)
        self.grade.setSpacing(16)
        for coluna in range(COLUNAS):        # cartoes da mesma largura
            self.grade.setColumnStretch(coluna, 1)
        base = rodape([botao("Voltar", "secundario", janela.ir_menu)],
                      [botao("+ Novo produto", "sucesso", janela.abrir_novo_produto)])
        montar_tela(self, topo, rolagem(self.grade_widget), base)

    def recarregar(self):
        limpar_layout(self.grade)
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
        self.grade.setRowStretch((len(produtos) + COLUNAS - 1) // COLUNAS, 1)

    @staticmethod
    def _texto(codigo, p):
        unit = p.get("peso_unit_g")
        peso = ("%s por peça" % formatar_peso(unit)) if unit else "sem peso: usar amostra"
        estoque = formatar_numero(p.get("estoque_atual", 0))
        return "%s\n%s\n%s  ·  estoque %s" % (p.get("nome", codigo), codigo, peso, estoque)
