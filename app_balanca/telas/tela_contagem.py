"""Tela 3b - Contagem: pecas no prato -> quantidade BEM grande -> Confirmar.

Serve para o inventario. A conferencia (Fase 3c) reaproveita esta tela.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from contagem import avisos_de_precisao, contar_pecas
from telas.componentes import botao, cartao, rotulo
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
        self._contagem = None      # ultima contagem com peso estavel
        self._peso_liquido = None

        # --- esquerda: o numero grande ---
        self.nome = rotulo("", "subtitulo")
        self.quantidade = rotulo("0", "gigante")
        self.unidade = rotulo("peças", "subtitulo")
        self.estado = rotulo("", "subtitulo")
        self.avisos = rotulo("", "aviso")
        self.avisos.hide()
        esquerda = cartao()
        e = QVBoxLayout(esquerda)
        e.setContentsMargins(30, 20, 30, 20)
        e.addWidget(self.nome)
        e.addStretch()
        e.addWidget(self.quantidade)
        e.addWidget(self.unidade)
        e.addWidget(self.estado)
        e.addStretch()
        e.addWidget(self.avisos)

        # --- direita: detalhes e botoes ---
        self.peso_liquido = rotulo("", "peso", Qt.AlignLeft)
        self.peso_unitario = rotulo("", "peso", Qt.AlignLeft)
        self.tara = rotulo("", "subtitulo", Qt.AlignLeft)
        detalhes = QGridLayout()
        detalhes.setHorizontalSpacing(16)
        detalhes.addWidget(rotulo("No prato", "subtitulo", Qt.AlignLeft | Qt.AlignVCenter), 0, 0)
        detalhes.addWidget(self.peso_liquido, 0, 1)
        detalhes.addWidget(rotulo("1 peça", "subtitulo", Qt.AlignLeft | Qt.AlignVCenter), 1, 0)
        detalhes.addWidget(self.peso_unitario, 1, 1)
        detalhes.addWidget(self.tara, 2, 0, 1, 2)
        detalhes.setColumnStretch(1, 1)

        self.botao_confirmar = botao("Confirmar", "sucesso", self.confirmar, altura=90)
        acoes = QHBoxLayout()
        acoes.addWidget(botao("Amostra", "secundario", janela.abrir_amostra, altura=70))
        acoes.addWidget(botao("Tara", "secundario", self.tarar, altura=70))
        direita = QVBoxLayout()
        direita.addLayout(detalhes)
        direita.addStretch()
        direita.addLayout(acoes)
        direita.addWidget(self.botao_confirmar)
        direita.addWidget(botao("Voltar", "secundario", janela.abrir_inventario, altura=60))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 12, 30, 12)
        layout.setSpacing(30)
        layout.addWidget(esquerda, 3)
        layout.addLayout(direita, 2)

    # ---------- abrir e configurar ----------
    def abrir(self, codigo):
        self.codigo = codigo
        self.produto = self.janela.ctrl.dados.cadastro("produtos", codigo) or {}
        self.nome.setText("%s  (%s)" % (self.produto.get("nome", codigo), codigo))
        unit = self.produto.get("peso_unit_g")
        self.usar_peso_unitario(float(unit) if unit else None, "cadastro")

    def usar_peso_unitario(self, peso_unit, metodo):
        self.peso_unit = peso_unit
        self.metodo = metodo
        if peso_unit:
            self.peso_unitario.setText("%s  (%s)" % (formatar_peso(round(peso_unit, 2)),
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
        self.tara.setText("Tara: %s" % formatar_peso(tara) if tara else "")
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
        self.botao_confirmar.setEnabled(bool(quantidade))

    # ---------- confirmar ----------
    def confirmar(self):
        c = self._contagem
        if not c or not c.quantidade:
            return
        tara = self.janela.balanca.tara_g()
        self.janela.ctrl.confirmar_inventario(
            self.codigo, c, peso_total_g=self._peso_liquido + tara, tara_g=tara,
            peso_unit_g=self.peso_unit, metodo=self.metodo)
        self.janela.mostrar_mensagem(
            "Registrado!", "%s peças de %s" % (formatar_numero(c.quantidade),
                                               self.produto.get("nome", self.codigo)),
            "sucesso", depois=self.janela.abrir_inventario)
