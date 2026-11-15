"""Tela 5 - Amostra: coloque N pecas -> peso de 1 peca -> Usar / Usar e salvar no cadastro."""
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from contagem import avisos_de_precisao, peso_unitario_por_amostra
from telas.componentes import BarraTaras, botao, cabecalho, cartao, montar_tela, rodape, rotulo
from telas.estilo import formatar_peso

MINIMO, MAXIMO = 1, 100


class TelaAmostra(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.n = int(janela.config.get("amostra_padrao", 10))
        self._peso = None

        topo, self.titulo, self.produto = cabecalho("Amostra", "")
        self.instrucao = rotulo("", "subtitulo")
        self.numero = rotulo("", "gigante")
        menos = botao("−", "secundario", lambda: self.mudar_n(-1), altura=110)
        mais = botao("+", "secundario", lambda: self.mudar_n(+1), altura=110)
        for b in (menos, mais):
            b.setFixedWidth(130)
            b.setStyleSheet("font-size: 56px; font-weight: 700; padding: 0;")
        seletor = QHBoxLayout()
        seletor.addStretch()
        seletor.addWidget(menos)
        seletor.addWidget(self.numero)
        seletor.addWidget(mais)
        seletor.addStretch()

        self.peso = rotulo("", "peso")
        self.resultado = rotulo("", "titulo")
        self.avisos = rotulo("", "aviso")
        self.avisos.hide()
        quadro = cartao()
        q = QVBoxLayout(quadro)
        q.addWidget(self.instrucao)
        q.addLayout(seletor)
        q.addWidget(self.peso)
        q.addWidget(self.resultado)
        q.addWidget(self.avisos)

        lateral = QVBoxLayout()
        lateral.setSpacing(16)
        topo_lateral = QHBoxLayout()
        topo_lateral.addWidget(botao("Tara", "secundario", janela.balanca.tarar, altura=70))
        topo_lateral.addWidget(botao("Zerar", "secundario", janela.zerar_balanca, altura=70))
        lateral.addLayout(topo_lateral)
        self.taras = BarraTaras(janela.balanca)
        lateral.addWidget(self.taras)
        lateral.addStretch()

        corpo = QHBoxLayout()
        corpo.setSpacing(24)
        corpo.addWidget(quadro, 3)
        corpo.addLayout(lateral, 2)

        self.usar = botao("Usar", ao_clicar=lambda: self.confirmar(False))
        self.usar_salvar = botao("Usar e salvar", "sucesso", lambda: self.confirmar(True))
        self.usar_salvar.setToolTip("Usa agora e grava o peso de 1 peça no cadastro do produto")
        base = rodape([botao("Cancelar", "secundario", janela.voltar_contagem)],
                      [self.usar, self.usar_salvar])
        montar_tela(self, topo, corpo, base)

    def abrir(self, nome_produto):
        self.produto.setText(nome_produto)
        self.taras.recarregar(self.janela.ctrl.taras())
        self.mudar_n(0)

    def mudar_n(self, delta):
        self.n = max(MINIMO, min(MAXIMO, self.n + delta))
        self.numero.setText(str(self.n))
        self.instrucao.setText("Coloque %d peça%s no prato" % (self.n, "" if self.n == 1 else "s"))
        self.atualizar_peso(self._peso, self._peso)

    def atualizar_peso(self, estavel, atual):
        self._peso = estavel
        self.peso.setText("No prato: %s" % formatar_peso(estavel if estavel is not None else atual))
        pronto = bool(estavel and estavel > 0)
        self.usar.setEnabled(pronto)
        self.usar_salvar.setEnabled(pronto)
        if not pronto:
            self.resultado.setText("Aguarde o peso estabilizar..." if estavel is None else "")
            self.avisos.hide()
            return
        unit = peso_unitario_por_amostra(estavel, self.n)
        self.resultado.setText("1 peça = %s" % formatar_peso(round(unit, 2)))
        avisos = avisos_de_precisao(unit, self.janela.balanca.divisao_g(), estavel)
        self.avisos.setText("\n".join(avisos))
        self.avisos.setVisible(bool(avisos))

    def confirmar(self, salvar):
        if not self._peso:
            return
        unit = peso_unitario_por_amostra(self._peso, self.n)
        contagem = self.janela.contagem
        if salvar:
            self.janela.ctrl.salvar_peso_unitario(contagem.codigo, unit)
        contagem.usar_peso_unitario(unit, "amostra")
        self.janela.voltar_contagem()
