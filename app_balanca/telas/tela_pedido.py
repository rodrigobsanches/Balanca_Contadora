"""Tela 4b - Conferencia de UM pedido: pesar cada item -> Finalizar.

Cada item mostra o resultado (OK / FALTA / SOBRA). Finalizar so libera quando todos
foram pesados. Tudo OK: etiqueta de conferido. Divergencia: aviso em vermelho e o
pedido continua pendente (da para recontar o item).
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from telas.componentes import botao, mudar_papel, rotulo
from telas.estilo import formatar_numero


class TelaPedido(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.pedido_id = None
        self.pedido = {}
        self.registros = {}      # codigo -> ultimo registro de contagem do item
        self.resultados = {}     # codigo -> ResultadoConferencia

        self.titulo = rotulo("", "titulo", Qt.AlignLeft | Qt.AlignVCenter)
        self.destino = rotulo("", "subtitulo", Qt.AlignLeft | Qt.AlignVCenter)
        cabecalho = QVBoxLayout()
        cabecalho.addWidget(self.titulo)
        cabecalho.addWidget(self.destino)

        self.lista_widget = QWidget()
        self.lista = QGridLayout(self.lista_widget)
        self.lista.setHorizontalSpacing(20)
        self.lista.setVerticalSpacing(12)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setWidget(self.lista_widget)

        self.finalizar_botao = botao("Finalizar", "sucesso", self.finalizar, altura=90)
        lateral = QVBoxLayout()
        lateral.addStretch()
        lateral.addWidget(self.finalizar_botao)
        lateral.addWidget(botao("Voltar", "secundario", janela.abrir_conferencia, altura=70))

        corpo = QHBoxLayout()
        corpo.setSpacing(30)
        corpo.addWidget(rolagem, 3)
        corpo.addLayout(lateral, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 16, 40, 16)
        layout.addLayout(cabecalho)
        layout.addLayout(corpo, 1)

    def abrir(self, pedido_id):
        self.pedido_id = pedido_id
        self.pedido = self.janela.ctrl.dados.cadastro("pedidos", pedido_id) or {}
        self.registros = {}
        self.resultados = {}
        self.titulo.setText("Pedido %s" % pedido_id)
        self.destino.setText(self.pedido.get("destino", ""))
        self._montar_lista()

    def itens(self):
        """{codigo: quantidade esperada}"""
        return {c: int(v.get("qtd", 0)) for c, v in (self.pedido.get("itens") or {}).items()}

    def resultado_item(self, codigo, registro, resultado):
        self.registros[codigo] = registro
        self.resultados[codigo] = resultado
        self._montar_lista()

    def _montar_lista(self):
        while self.lista.count():
            item = self.lista.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        produtos = self.janela.ctrl.produtos()
        for linha, (codigo, esperada) in enumerate(sorted(self.itens().items())):
            nome = produtos.get(codigo, {}).get("nome", codigo)
            self.lista.addWidget(rotulo("%s\n%s" % (nome, codigo), "peso",
                                        Qt.AlignLeft | Qt.AlignVCenter), linha, 0)
            self.lista.addWidget(rotulo("%s peças" % formatar_numero(esperada), "subtitulo"), linha, 1)
            situacao = rotulo("", "subtitulo")
            r = self.resultados.get(codigo)
            if r:
                situacao.setText("Confere" if r.resultado == "OK" else r.mensagem)
                mudar_papel(situacao, "ok" if r.resultado == "OK" else "erro")
            else:
                situacao.setText("a pesar")
            self.lista.addWidget(situacao, linha, 2)
            pesar = botao("Recontar" if r else "Pesar", "secundario" if r else None, altura=70)
            pesar.setMinimumWidth(170)
            pesar.clicked.connect(lambda _=False, c=codigo, e=esperada: self.janela.pesar_item(c, e))
            self.lista.addWidget(pesar, linha, 3)
        self.lista.setColumnStretch(0, 1)
        self.lista.setRowStretch(len(self.itens()), 1)
        self.finalizar_botao.setEnabled(bool(self.itens()) and
                                        set(self.resultados) >= set(self.itens()))

    def finalizar(self):
        registros = [self.registros[c] for c in sorted(self.itens())]
        ctrl = self.janela.ctrl
        if ctrl.finalizar_conferencia(self.pedido_id, registros):
            self.janela.abrir_etiqueta(ctrl.dados_etiqueta(self.pedido_id, registros))
            return
        problemas = ["%s: %s" % (c, r.mensagem) for c, r in sorted(self.resultados.items())
                     if r.resultado != "OK"]
        self.janela.mostrar_mensagem(
            "Divergência no pedido %s" % self.pedido_id,
            "\n".join(problemas) + "\nO pedido continua pendente. Reconte ou separe as peças.",
            "erro", depois=lambda: self.janela.ir(self), segundos=8)
