"""Tela 4a - Conferencia: escolher o pedido pendente."""
from PySide6.QtWidgets import QGridLayout, QWidget

from telas.componentes import botao, cabecalho, limpar_layout, montar_tela, rodape, rolagem, rotulo

COLUNAS = 2


class TelaPedidos(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        topo, _, self.subtitulo = cabecalho("Conferência de despacho", "Escolha o pedido")

        self.grade_widget = QWidget()
        self.grade = QGridLayout(self.grade_widget)
        self.grade.setContentsMargins(0, 0, 0, 0)
        self.grade.setSpacing(16)
        for coluna in range(COLUNAS):        # cartoes da mesma largura
            self.grade.setColumnStretch(coluna, 1)
        base = rodape([botao("Voltar", "secundario", janela.ir_menu)])
        montar_tela(self, topo, rolagem(self.grade_widget), base)

    def recarregar(self):
        limpar_layout(self.grade)
        pedidos = self.janela.ctrl.pedidos_pendentes()
        n = len(pedidos)
        self.subtitulo.setText("Escolha o pedido   ·   %d pendente%s" % (n, "" if n == 1 else "s"))
        if not pedidos:
            self.grade.addWidget(rotulo("Nenhum pedido pendente.", "subtitulo"), 0, 0)
            return
        for i, (pid, p) in enumerate(sorted(pedidos.items())):
            n = len(p.get("itens") or {})
            texto = "%s\n%s\n%d ite%s" % (pid, p.get("destino", ""), n, "m" if n == 1 else "ns")
            b = botao(texto, "produto", altura=130)
            b.clicked.connect(lambda _=False, pid=pid: self.janela.abrir_pedido(pid))
            self.grade.addWidget(b, i // COLUNAS, i % COLUNAS)
        self.grade.setRowStretch((len(pedidos) + COLUNAS - 1) // COLUNAS, 1)
