"""Tela de contagem: pecas no prato -> quantidade BEM grande -> Confirmar.

Dois modos:
  inventario  -> Confirmar registra a contagem e substitui o estoque
  conferencia -> mostra a quantidade esperada do pedido; Confirmar registra o item
                 (OK / FALTA / SOBRA) e volta para a tela do pedido
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from contagem import avisos_de_precisao, conferir, contar_pecas
from telas.componentes import (BarraTaras, botao, cabecalho, cartao, montar_tela, mudar_papel,
                               rodape, rotulo)
from telas.estilo import formatar_numero, formatar_peso

NOMES_METODO = {"cadastro": "do cadastro", "amostra": "pela amostra"}


class TelaContagem(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.codigo = None
        self.produto = {}
        self.peso_unit = None
        self.metodo = "cadastro"
        self.modo = "inventario"
        self.esperada = None       # so na conferencia
        self.pedido_id = None
        self._contagem = None      # ultima contagem com peso estavel
        self._peso_liquido = None

        topo, self.nome, self.subtitulo = cabecalho()

        # --- esquerda: o numero grande ---
        self.esperado = rotulo("", "info")
        self.esperado.hide()
        self.quantidade = rotulo("0", "gigante")
        self.unidade = rotulo("peças", "subtitulo")
        self.estado = rotulo("", "subtitulo")
        self.avisos = rotulo("", "aviso")
        self.avisos.hide()
        esquerda = cartao()
        e = QVBoxLayout(esquerda)
        e.setContentsMargins(24, 16, 24, 16)
        e.addWidget(self.esperado)
        e.addStretch()
        e.addWidget(self.quantidade)
        e.addWidget(self.unidade)
        e.addWidget(self.estado)
        e.addStretch()
        e.addWidget(self.avisos)

        # --- direita: pesos e ajustes da balanca ---
        self.peso_liquido = rotulo("", "peso", Qt.AlignLeft | Qt.AlignVCenter)
        self.peso_unitario = rotulo("", "peso", Qt.AlignLeft | Qt.AlignVCenter)
        self.tara = rotulo("", "peso", Qt.AlignLeft | Qt.AlignVCenter)
        quadro = cartao()
        detalhes = QGridLayout(quadro)
        detalhes.setContentsMargins(24, 16, 24, 16)
        detalhes.setHorizontalSpacing(16)
        detalhes.setVerticalSpacing(10)
        for linha, (texto, valor) in enumerate((("No prato", self.peso_liquido),
                                                ("1 peça", self.peso_unitario),
                                                ("Tara", self.tara))):
            detalhes.addWidget(rotulo(texto, "subtitulo", Qt.AlignLeft | Qt.AlignVCenter), linha, 0)
            detalhes.addWidget(valor, linha, 1)
        detalhes.setColumnStretch(1, 1)

        acoes = QHBoxLayout()
        acoes.addWidget(botao("Amostra", "secundario", janela.abrir_amostra, altura=70))
        acoes.addWidget(botao("Tara", "secundario", self.tarar, altura=70))
        acoes.addWidget(botao("Zerar", "secundario", janela.zerar_balanca, altura=70))
        self.taras = BarraTaras(janela.balanca)
        direita = QVBoxLayout()
        direita.setSpacing(16)
        direita.addWidget(quadro)
        direita.addStretch()
        direita.addLayout(acoes)
        direita.addWidget(self.taras)

        corpo = QHBoxLayout()
        corpo.setSpacing(24)
        corpo.addWidget(esquerda, 3)
        corpo.addLayout(direita, 2)

        self.botao_confirmar = botao("Confirmar", "sucesso", self.confirmar)
        base = rodape([botao("Voltar", "secundario", janela.voltar_da_contagem)], [self.botao_confirmar])
        montar_tela(self, topo, corpo, base)

    # ---------- abrir e configurar ----------
    def abrir(self, codigo, modo="inventario", esperada=None, pedido_id=None):
        self.codigo = codigo
        self.modo = modo
        self.esperada = esperada
        self.pedido_id = pedido_id
        self.esperado.setVisible(modo == "conferencia")
        self.taras.recarregar(self.janela.ctrl.taras())
        self.produto = self.janela.ctrl.dados.cadastro("produtos", codigo) or {}
        self.nome.setText(self.produto.get("nome", codigo))
        self.subtitulo.setText("%s   ·   %s" % (codigo, "Pedido %s" % pedido_id if modo == "conferencia"
                                                  else "Inventário"))
        unit = self.produto.get("peso_unit_g")
        self.usar_peso_unitario(float(unit) if unit else None, "cadastro")

    def usar_peso_unitario(self, peso_unit, metodo):
        self.peso_unit = peso_unit
        self.metodo = metodo
        if peso_unit:
            self.peso_unitario.setText("%s  %s" % (formatar_peso(round(peso_unit, 2)),
                                                  NOMES_METODO.get(metodo, metodo)))
        else:
            self.peso_unitario.setText("sem peso: use a Amostra")
        self._contagem = None

    def tarar(self):
        self.janela.balanca.tarar()

    # ---------- chamado pela janela a cada leitura da balanca ----------
    def atualizar_peso(self, estavel, atual):
        b = self.janela.balanca
        tara = b.tara_g()
        self.tara.setText(formatar_peso(tara) if tara else "sem tara")
        self.peso_liquido.setText(formatar_peso(estavel if estavel is not None else atual))
        if not self.peso_unit:
            self._mostrar(None, "Faça a amostra para saber o peso de 1 peça")
            return
        if estavel is None:
            self.estado.setText("Aguarde o peso estabilizar...")
            self.botao_confirmar.setEnabled(False)
            return
        c = contar_pecas(estavel, self.peso_unit)
        self._contagem, self._peso_liquido = c, estavel
        avisos = avisos_de_precisao(self.peso_unit, b.divisao_g())
        if c.incerta and c.quantidade > 0:
            avisos.append("Contagem incerta: confira as peças ou refaça a amostra.")
        self._mostrar(c.quantidade, "Peso estável" if c.quantidade else "Coloque as peças no prato",
                      avisos)

    def _mostrar(self, quantidade, estado, avisos=()):
        self.quantidade.setText(formatar_numero(quantidade) if quantidade is not None else "--")
        self.unidade.setText("peça" if quantidade == 1 else "peças")
        self.estado.setText(estado)
        self.avisos.setText("\n".join(avisos))
        self.avisos.setVisible(bool(avisos))
        if self.modo == "conferencia":
            self._mostrar_comparacao(quantidade)
            # na conferencia, zero pecas tambem vale (o item pode estar faltando inteiro)
            self.botao_confirmar.setEnabled(quantidade is not None and self._contagem is not None)
        else:
            self.botao_confirmar.setEnabled(bool(quantidade))

    def _mostrar_comparacao(self, quantidade):
        texto = "Esperado: %s peças" % formatar_numero(self.esperada)
        papel = "info"
        if quantidade is not None and self._contagem is not None:
            r = conferir(quantidade, self.esperada)
            texto += "   ·   " + ("Confere" if r.resultado == "OK" else r.mensagem)
            papel = "ok" if r.resultado == "OK" else "erro"
        self.esperado.setText(texto)
        mudar_papel(self.esperado, papel)

    # ---------- confirmar ----------
    def confirmar(self):
        c = self._contagem
        if not c or (not c.quantidade and self.modo != "conferencia"):
            return
        tara = self.janela.balanca.tara_g()
        if self.modo == "conferencia":
            registro, resultado = self.janela.ctrl.conferir_item(
                self.pedido_id, self.codigo, c, self.esperada,
                peso_total_g=self._peso_liquido + tara, tara_g=tara,
                peso_unit_g=self.peso_unit, metodo=self.metodo)
            self.janela.item_conferido(self.codigo, registro, resultado)
            return
        self.janela.ctrl.confirmar_inventario(
            self.codigo, c, peso_total_g=self._peso_liquido + tara, tara_g=tara,
            peso_unit_g=self.peso_unit, metodo=self.metodo)
        self.janela.finalizar_pesagem(
            "Registrado!", "%s peças de %s" % (formatar_numero(c.quantidade),
                                               self.produto.get("nome", self.codigo)),
            "sucesso", depois=self.janela.abrir_inventario, frase="contagem_registrada")
