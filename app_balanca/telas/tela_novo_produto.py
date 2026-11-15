"""Novo produto pela balanca (sem teclado): pesar 1, 5 e 10 pecas -> peso de 1 peca -> Salvar.

O produto vai para o proximo codigo livre (P004, P005...) com nome provisorio; o nome de
verdade e colocado no dashboard (Cadastros -> Produtos). Cada etapa pede o total de pecas
no prato: da para ir acrescentando (1 -> mais 4 -> mais 5).
"""
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from contagem import avisos_de_precisao, peso_unitario_por_etapas
from telas.componentes import BarraTaras, botao, cabecalho, cartao, montar_tela, rodape, rotulo
from telas.estilo import formatar_peso

ETAPAS = (1, 5, 10)              # pecas no prato em cada etapa
DIFERENCA_MAXIMA = 0.10          # medidas que discordam mais que 10%: avisa para conferir


def peso_de_uma_peca(gramas):
    """Peso de 1 peca com 2 casas (ex.: 3,06 g): mais preciso que o visor, por ser uma media."""
    return ("%.2f g" % gramas).replace(".", ",")


class TelaNovoProduto(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.medidas = []            # [(pecas, peso_g), ...]
        self._peso = None
        self._peso_unit = None

        topo, self.titulo, _ = cabecalho("Novo produto",
                                         "Pese 1, 5 e 10 peças: a balança calcula o peso de 1 peça")
        self.instrucao = rotulo("", "subtitulo")
        self.numero = rotulo("", "gigante")
        self.numero.setStyleSheet("font-size: 90px;")    # "10 peças" nao cabe no tamanho gigante
        self.peso = rotulo("", "peso")
        self.etapas = rotulo("", "subtitulo")
        self.avisos = rotulo("", "aviso")
        self.avisos.hide()
        quadro = cartao()
        q = QVBoxLayout(quadro)
        q.addWidget(self.instrucao)
        q.addWidget(self.numero)
        q.addWidget(self.peso)
        q.addWidget(self.etapas)
        q.addWidget(self.avisos)

        ajustes = QHBoxLayout()
        ajustes.addWidget(botao("Tara", "secundario", janela.balanca.tarar, altura=70))
        ajustes.addWidget(botao("Zerar", "secundario", janela.zerar_balanca, altura=70))
        self.taras = BarraTaras(janela.balanca)
        lateral = QVBoxLayout()
        lateral.setSpacing(16)
        lateral.addLayout(ajustes)
        lateral.addWidget(self.taras)
        lateral.addStretch()

        corpo = QHBoxLayout()
        corpo.setSpacing(24)
        corpo.addWidget(quadro, 3)
        corpo.addLayout(lateral, 2)

        self.registrar = botao("", "sucesso", self.registrar_etapa)
        self.salvar = botao("Salvar produto", "sucesso", self.salvar_produto)
        base = rodape([botao("Cancelar", "secundario", janela.abrir_inventario),
                       botao("Refazer", "secundario", self.abrir)],
                      [self.registrar, self.salvar])
        montar_tela(self, topo, corpo, base)

    # ---------- etapas ----------
    def abrir(self):
        self.medidas = []
        self._peso_unit = None
        self.titulo.setText("Novo produto: %s" % self.janela.ctrl.proximo_codigo_produto())
        self.taras.recarregar(self.janela.ctrl.taras())
        self._mostrar_etapa()

    def pecas_da_etapa(self):
        return ETAPAS[len(self.medidas)] if len(self.medidas) < len(ETAPAS) else None

    def _mostrar_etapa(self):
        n = self.pecas_da_etapa()
        feitas = "   ".join("%d peça%s: %s" % (p, "" if p == 1 else "s", formatar_peso(g))
                           for p, g in self.medidas)
        self.etapas.setText(feitas)
        self.registrar.setVisible(n is not None)
        self.salvar.setVisible(n is None)
        if n is not None:
            self.instrucao.setText("Etapa %d de %d: deixe no prato" % (len(self.medidas) + 1, len(ETAPAS)))
            self.numero.setText("%d peça%s" % (n, "" if n == 1 else "s"))
            self.registrar.setText("Registrar %d peça%s" % (n, "" if n == 1 else "s"))
            self.avisos.hide()
        else:
            self._calcular()
        self.atualizar_peso(self._peso, self._peso)

    def _calcular(self):
        peso_unit, diferenca = peso_unitario_por_etapas(self.medidas)
        self._peso_unit = peso_unit
        self.instrucao.setText("Peso de 1 peça")
        self.numero.setText(peso_de_uma_peca(peso_unit))
        avisos = avisos_de_precisao(peso_unit, self.janela.balanca.divisao_g())
        if diferenca > DIFERENCA_MAXIMA:
            avisos.insert(0, "As medidas não batem (%.0f%% de diferença). Confira a quantidade "
                             "de peças e toque em Refazer." % (diferenca * 100))
        self.avisos.setText("\n".join(avisos))
        self.avisos.setVisible(bool(avisos))

    def registrar_etapa(self):
        n = self.pecas_da_etapa()
        if n is None or not self._peso or self._peso <= 0:
            return
        self.medidas.append((n, self._peso))
        self._mostrar_etapa()

    def salvar_produto(self):
        if not self._peso_unit:
            return
        codigo = self.janela.ctrl.criar_produto(self._peso_unit)
        self.janela.finalizar_pesagem(
            "Produto %s cadastrado!" % codigo,
            "1 peça = %s. Coloque o nome no dashboard (Cadastros → Produtos)."
            % peso_de_uma_peca(self._peso_unit),
            depois=self.janela.abrir_inventario)

    # ---------- chamado pela janela a cada leitura da balanca ----------
    def atualizar_peso(self, estavel, atual):
        self._peso = estavel
        self.peso.setText("No prato: %s" % formatar_peso(estavel if estavel is not None else atual))
        if self.pecas_da_etapa() is not None:
            self.registrar.setEnabled(bool(estavel and estavel > 0))
