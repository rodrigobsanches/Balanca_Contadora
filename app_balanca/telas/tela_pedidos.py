"""Tela 4a - Conferencia: escolher o pedido pendente."""
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from telas.componentes import botao, rotulo

COLUNAS = 2


class TelaPedidos(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        titulo = rotulo("Conferência: escolha o pedido", "titulo")
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
                item.widget().hide()
                item.widget().deleteLater()
        pedidos = self.janela.ctrl.pedidos_pendentes()
        if not pedidos:
            self.grade.addWidget(rotulo("Nenhum pedido pendente.", "subtitulo"), 0, 0)
            return
        for i, (pid, p) in enumerate(sorted(pedidos.items())):
            n = len(p.get("itens") or {})
            texto = "%s\n%s\n%d ite%s" % (pid, p.get("destino", ""), n, "m" if n == 1 else "ns")
            b = botao(texto, "produto", altura=130)
            b.clicked.connect(lambda _=False, pid=pid: self.janela.abrir_pedido(pid))
            self.grade.addWidget(b, i // COLUNAS, i % COLUNAS)
        self.grade.setRowStretch(len(pedidos) // COLUNAS + 1, 1)
