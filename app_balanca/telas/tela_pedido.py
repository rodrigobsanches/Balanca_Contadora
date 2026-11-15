"""Tela 4b - Conferencia de UM pedido: pesar cada item -> Finalizar.

Cada item mostra o resultado (OK / FALTA / SOBRA). Finalizar so libera quando todos
foram pesados. Tudo OK: etiqueta de conferido. Divergencia: aviso em vermelho e o
pedido continua pendente (da para recontar o item).
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from telas.componentes import (botao, cabecalho, cartao, limpar_layout, montar_tela, mudar_papel,
                               rodape, rolagem, rotulo)
from telas.estilo import formatar_numero

# larguras fixas: as colunas ficam alinhadas de uma linha para a outra
LARGURA_QTD, LARGURA_SELO, LARGURA_BOTAO = 150, 250, 190


class TelaPedido(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.pedido_id = None
        self.pedido = {}
        self.registros = {}      # codigo -> ultimo registro de contagem do item
        self.resultados = {}     # codigo -> ResultadoConferencia

        topo, self.titulo, self.destino = cabecalho()

        self.lista_widget = QWidget()
        self.lista = QVBoxLayout(self.lista_widget)
        self.lista.setContentsMargins(0, 0, 0, 0)
        self.lista.setSpacing(12)

        self.finalizar_botao = botao("Finalizar", "sucesso", self.finalizar)
        base = rodape([botao("Voltar", "secundario", janela.abrir_conferencia)], [self.finalizar_botao])
        montar_tela(self, topo, rolagem(self.lista_widget), base)

    def abrir(self, pedido_id):
        self.pedido_id = pedido_id
        self.pedido = self.janela.ctrl.dados.cadastro("pedidos", pedido_id) or {}
        self.registros = {}
        self.resultados = {}
        self.titulo.setText("Pedido %s" % pedido_id)
        self._montar_lista()

    def itens(self):
        """{codigo: quantidade esperada}"""
        return {c: int(v.get("qtd", 0)) for c, v in (self.pedido.get("itens") or {}).items()}

    def resultado_item(self, codigo, registro, resultado):
        self.registros[codigo] = registro
        self.resultados[codigo] = resultado
        self._montar_lista()

    def _montar_lista(self):
        limpar_layout(self.lista)
        produtos = self.janela.ctrl.produtos()
        for codigo, esperada in sorted(self.itens().items()):
            nome = produtos.get(codigo, {}).get("nome", codigo)
            self.lista.addWidget(self._linha(codigo, nome, esperada, self.resultados.get(codigo)))
        self.lista.addStretch()
        pesados = len(set(self.resultados) & set(self.itens()))
        self.destino.setText("Destino: %s   ·   %d de %d ite%s pesado%s" % (
            self.pedido.get("destino", ""), pesados, len(self.itens()),
            "m" if len(self.itens()) == 1 else "ns", "" if pesados == 1 else "s"))
        self.finalizar_botao.setEnabled(bool(self.itens()) and
                                        set(self.resultados) >= set(self.itens()))

    def _linha(self, codigo, nome, esperada, r):
        """Um item do pedido: nome e codigo | quantidade | situacao | Pesar (no fim da linha)."""
        linha = cartao()
        h = QHBoxLayout(linha)
        h.setContentsMargins(24, 12, 16, 12)
        h.setSpacing(16)
        textos = QVBoxLayout()
        textos.setSpacing(0)
        textos.addWidget(rotulo(nome, "nome", Qt.AlignLeft | Qt.AlignVCenter))
        textos.addWidget(rotulo(codigo, "detalhe", Qt.AlignLeft | Qt.AlignVCenter))
        h.addLayout(textos, 1)

        qtd = rotulo("%s peças" % formatar_numero(esperada), "peso", Qt.AlignRight | Qt.AlignVCenter)
        qtd.setFixedWidth(LARGURA_QTD)
        h.addWidget(qtd)

        # selo de situacao so aparece depois de pesar; antes fica oculto, mas guardando o
        # lugar (as colunas continuam alinhadas entre itens pesados e nao pesados)
        selo = rotulo()
        selo.setFixedWidth(LARGURA_SELO)
        politica = selo.sizePolicy()
        politica.setRetainSizeWhenHidden(True)
        selo.setSizePolicy(politica)
        if r:
            selo.setText("Confere" if r.resultado == "OK" else r.mensagem.rstrip("."))
            mudar_papel(selo, "selo_ok" if r.resultado == "OK" else "selo_erro")
        else:
            selo.hide()
        h.addWidget(selo)

        pesar = botao("Recontar" if r else "Pesar", "secundario" if r else None, altura=70)
        pesar.setFixedWidth(LARGURA_BOTAO)
        pesar.clicked.connect(lambda _=False, c=codigo, e=esperada: self.janela.pesar_item(c, e))
        h.addWidget(pesar)
        return linha

    def finalizar(self):
        registros = [self.registros[c] for c in sorted(self.itens())]
        ctrl = self.janela.ctrl
        if ctrl.finalizar_conferencia(self.pedido_id, registros):
            self.janela.voz.falar("pedido_conferido")
            self.janela.abrir_etiqueta(ctrl.dados_etiqueta(self.pedido_id, registros))
            return
        problemas = ["%s: %s" % (c, r.mensagem) for c, r in sorted(self.resultados.items())
                     if r.resultado != "OK"]
        self.janela.voz.falar("pedido_divergente")
        self.janela.mostrar_mensagem(
            "Divergência no pedido %s" % self.pedido_id,
            "\n".join(problemas) + "\nO pedido continua pendente. Reconte ou separe as peças.",
            "erro", depois=lambda: self.janela.ir(self), segundos=8)
