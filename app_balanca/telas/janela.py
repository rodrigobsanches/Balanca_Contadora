"""Janela principal: visor (simulado), barra de status e as telas empilhadas.

A janela so troca de tela e repassa avisos. As regras ficam no controlador.
Tamanho: feita para a tela da balanca (1366 x 768), deixando uma faixa livre no topo
(faixa_reservada_topo_px) para o visor de peso da propria balanca, que nao pode ser coberto.
"""
import time
from datetime import datetime

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from telas.componentes import rotulo
from telas.estilo import QSS, formatar_peso
from telas.tela_amostra import TelaAmostra
from telas.tela_contagem import TelaContagem
from telas.tela_descanso import TelaDescanso
from telas.tela_etiqueta import TelaEtiqueta
from telas.tela_menu import TelaMenu
from telas.tela_mensagem import TelaMensagem
from telas.tela_pedido import TelaPedido
from telas.tela_pedidos import TelaPedidos
from telas.tela_produtos import TelaProdutos
from telas.tela_retirar import TelaRetirar
from voz import Voz

LARGURA, ALTURA = 1366, 768
INTERVALO_BALANCA_MS = 200


class VisorSimulado(QFrame):
    """Imita, na faixa do topo, o visor de peso da balanca (so no modo simulado)."""
    def __init__(self, altura):
        super().__init__()
        self.setObjectName("visor")
        self.setFixedHeight(altura)
        self.peso = rotulo("", None, Qt.AlignRight | Qt.AlignVCenter)
        self.peso.setStyleSheet("font-size: 64px; font-weight: 700; font-family: Consolas;")
        self.info = rotulo("VISOR DA BALANÇA (simulado)", None, Qt.AlignLeft | Qt.AlignVCenter)
        self.info.setStyleSheet("font-size: 18px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 0, 40, 0)
        layout.addWidget(self.info, 1)
        layout.addWidget(self.peso)

    def mostrar(self, atual, estavel, tara):
        situacao = "estável" if estavel is not None else "instável"
        tara_txt = ("   ·   tara %s" % formatar_peso(tara)) if tara else ""
        self.info.setText("VISOR DA BALANÇA (simulado)\n%s%s" % (situacao, tara_txt))
        self.peso.setText(formatar_peso(atual))


class BarraStatus(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("barra_status")
        self.setFixedHeight(36)
        self.balanca = rotulo("", None, Qt.AlignLeft | Qt.AlignVCenter)
        self.esp32 = rotulo("ESP32: procurando...", None, Qt.AlignLeft | Qt.AlignVCenter)
        self.wifi = rotulo("", None, Qt.AlignLeft | Qt.AlignVCenter)
        self.envio = rotulo("", None, Qt.AlignLeft | Qt.AlignVCenter)
        self.operador = rotulo("", None, Qt.AlignRight | Qt.AlignVCenter)
        self.relogio = rotulo("", None, Qt.AlignRight | Qt.AlignVCenter)
        for r in (self.balanca, self.esp32, self.wifi, self.envio, self.operador, self.relogio):
            r.setWordWrap(False)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        for w in (self.balanca, self.esp32, self.wifi, self.envio):
            layout.addWidget(w)
        layout.addStretch()
        layout.addWidget(self.operador)
        layout.addWidget(self.relogio)


class JanelaPrincipal(QWidget):
    def __init__(self, config, ctrl, balanca, impressora=None):
        super().__init__()
        self.config = config
        self.ctrl = ctrl
        self.balanca = balanca
        self.impressora = impressora       # None = so previa da etiqueta
        self.voz = Voz(config)             # frases gravadas; "voz": false no config = silencio
        self.setWindowTitle("Balança contadora de peças")
        self.setStyleSheet(QSS)
        self.alguem_perto = False
        self._ultima_atividade = time.monotonic()
        self._uid_logado = None

        # --- topo: visor simulado ou faixa livre para o visor da balanca real ---
        faixa = self.faixa_topo()
        self.tela_cheia = bool(config.get("tela_cheia", False))
        self.visor = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if balanca.nome == "simulada":
            self.visor = VisorSimulado(faixa)
            layout.addWidget(self.visor)
        elif not self.tela_cheia:
            layout.addSpacing(faixa)   # no PC, so para manter as proporcoes da balanca

        self.barra = BarraStatus()
        layout.addWidget(self.barra)

        # --- telas ---
        self.pilha = QStackedWidget()
        self.descanso = TelaDescanso(self)
        self.menu = TelaMenu(self)
        self.produtos = TelaProdutos(self)
        self.contagem = TelaContagem(self)
        self.amostra = TelaAmostra(self)
        self.mensagem = TelaMensagem(self)
        self.pedidos = TelaPedidos(self)
        self.pedido = TelaPedido(self)
        self.etiqueta = TelaEtiqueta(self)
        self.retirar = TelaRetirar(self)
        for t in (self.descanso, self.menu, self.produtos, self.contagem, self.amostra,
                  self.mensagem, self.pedidos, self.pedido, self.etiqueta, self.retirar):
            self.pilha.addWidget(t)
        layout.addWidget(self.pilha, 1)

        # --- relogios ---
        self._timer_balanca = QTimer(self, interval=INTERVALO_BALANCA_MS, timeout=self.ler_balanca)
        self._timer_balanca.start()
        self._timer_segundo = QTimer(self, interval=1000, timeout=self._a_cada_segundo)
        self._timer_segundo.start()
        QApplication.instance().installEventFilter(self)   # toque em qualquer lugar = atividade
        self._atualizar_barra()
        self.produtos.recarregar()

    # ================= janela =================
    def faixa_topo(self):
        """Altura livre no topo para a janela de peso da balanca. A balanca real informa a
        altura exata da janela dela; senao, vale faixa_reservada_topo_px do config."""
        return int(self.balanca.altura_visor_px() or self.config.get("faixa_reservada_topo_px", 150))

    def mostrar(self):
        if self.tela_cheia:
            # na balanca: sem moldura, colado embaixo da janela de peso, ate o fim da tela
            tela = QGuiApplication.primaryScreen().geometry()
            faixa = self.faixa_topo()
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setGeometry(tela.x(), tela.y() + faixa, tela.width(), tela.height() - faixa)
        else:
            # no PC: o mesmo tamanho da tela da balanca, para ver exatamente o que cabe
            self.setFixedSize(LARGURA, ALTURA)
        self.show()

    def eventFilter(self, obj, evento):
        if evento.type() in (QEvent.MouseButtonPress, QEvent.TouchBegin):
            self._ultima_atividade = time.monotonic()
        return False

    # ================= navegacao =================
    def ir(self, tela):
        self.pilha.setCurrentWidget(tela)
        self.ler_balanca()

    def ir_menu(self):
        self.ir(self.menu if self.ctrl.operador else self.descanso)

    def abrir_inventario(self):
        self.produtos.recarregar()
        self.ir(self.produtos)

    def abrir_contagem(self, codigo):
        self.contagem.abrir(codigo)
        self.ir(self.contagem)

    def abrir_amostra(self):
        self.amostra.abrir(self.contagem.produto.get("nome", self.contagem.codigo))
        self.ir(self.amostra)

    def voltar_contagem(self):
        self.ir(self.contagem)

    def voltar_da_contagem(self):
        if self.contagem.modo == "conferencia":
            self.ir(self.pedido)
        else:
            self.abrir_inventario()

    # --- conferencia de despacho ---
    def abrir_conferencia(self):
        self.pedidos.recarregar()
        self.ir(self.pedidos)

    def abrir_pedido(self, pedido_id):
        self.pedido.abrir(pedido_id)
        self.ir(self.pedido)

    def pesar_item(self, codigo, esperada):
        self.contagem.abrir(codigo, "conferencia", esperada, self.pedido.pedido_id)
        self.ir(self.contagem)

    def item_conferido(self, codigo, registro, resultado):
        self.pedido.resultado_item(codigo, registro, resultado)
        if resultado.resultado == "OK":
            texto = "%s: confere" % registro.get("produto_nome", codigo)
        else:
            texto = "%s: %s" % (registro.get("produto_nome", codigo), resultado.mensagem)
        ok = resultado.resultado == "OK"
        self.finalizar_pesagem("Item registrado", texto, "sucesso" if ok else "erro",
                               depois=lambda: self.ir(self.pedido),
                               frase="item_conferido" if ok else "divergente")

    def finalizar_pesagem(self, titulo, texto, tipo="sucesso", depois=None, frase=None):
        """Depois de toda pesagem confirmada: tira a tara da balanca e pede para retirar
        tudo do prato. So segue (depois) quando o prato estiver vazio.
        frase: chave da voz (voz.FRASES) falada junto."""
        if frase:
            self.voz.falar(frase)
        if not self.balanca.limpar_tara():
            print("ATENCAO: nao consegui tirar a tara da balanca")
        self.retirar.abrir(titulo, texto, tipo, depois or self.ir_menu)
        self.ir(self.retirar)

    def abrir_etiqueta(self, etiqueta):
        self.etiqueta.abrir(etiqueta)
        self.ir(self.etiqueta)

    def mostrar_mensagem(self, titulo, texto, tipo="sucesso", depois=None, segundos=3):
        self.mensagem.mostrar(titulo, texto, tipo, depois or self.ir_menu, segundos)
        self.ir(self.mensagem)

    # ================= balanca =================
    def ler_balanca(self):
        estavel = self.balanca.peso_estavel_g()
        atual = self.balanca.peso_atual_g()
        if self.visor:
            self.visor.mostrar(atual, estavel, self.balanca.tara_g())
        tela = self.pilha.currentWidget()
        if tela in (self.contagem, self.amostra, self.retirar):
            tela.atualizar_peso(estavel, atual)

    # ================= avisos do controlador =================
    def ao_aviso(self, tipo, info):
        if tipo == "login":
            novo = info["uid"] != self._uid_logado
            self._uid_logado = info["uid"]
            self._ultima_atividade = time.monotonic()
            self.menu.definir_operador(info["nome"])
            # o mesmo chaveiro de novo no meio de uma contagem nao interrompe nada
            if novo or self.pilha.currentWidget() is self.descanso:
                self.voz.falar("bem_vindo")
                self.ir(self.menu)
        elif tipo == "logout":
            self._uid_logado = None
            self.voz.falar("ate_logo")
            self.ir(self.descanso)
        elif tipo == "verificando":
            self.descanso.mostrar_mensagem("Verificando chaveiro...", "info")
        elif tipo == "desconhecido":
            self.voz.falar("nao_cadastrado")
            self.descanso.mostrar_mensagem(
                "Chaveiro não cadastrado (%s).\nPeça o cadastro ao responsável." % info["uid"], "erro", 6)
        elif tipo == "presenca":
            self.alguem_perto = info["perto"]
            if self.alguem_perto:
                self._ultima_atividade = time.monotonic()
                if not self.ctrl.operador:
                    self.voz.falar("aproxime")
            self.descanso.definir_presenca(self.alguem_perto)
        elif tipo == "cadastros":
            if self.pilha.currentWidget() is self.produtos:
                self.produtos.recarregar()
            elif self.pilha.currentWidget() is self.pedidos:
                self.pedidos.recarregar()
        self._atualizar_barra()

    # ================= barra de status e saida automatica =================
    def _a_cada_segundo(self):
        self.barra.relogio.setText(datetime.now().strftime("%d/%m  %H:%M"))
        if self.alguem_perto:
            self._ultima_atividade = time.monotonic()
        limite = float(self.config.get("segundos_para_sair", 60))
        if self.ctrl.operador and time.monotonic() - self._ultima_atividade > limite:
            self.ctrl.sair()
        self.ctrl.sync_periodico()

    def _atualizar_barra(self):
        c = self.ctrl
        if self.balanca.nome == "simulada":
            self.barra.balanca.setText("Balança: simulada")
        elif getattr(self.balanca, "conectada", True):
            self.barra.balanca.setText("Balança: conectada")
        else:
            self.barra.balanca.setText("Balança: SEM CONEXÃO")
        if c.esp32_conectada:
            self.barra.esp32.setText("ESP32: conectada")
            st = c.status_esp32
            self.barra.wifi.setText("Wi-Fi: %s" % ("ok" if st.get("wifi") else "sem conexão"))
        else:
            self.barra.esp32.setText("ESP32: desconectada")
            self.barra.wifi.setText("")
        # "aguardando a nuvem" = ainda no PC (pendente) + guardado na fila da ESP32 (fila)
        n = c.dados.contar_por_status()
        self.barra.envio.setText("Aguardando nuvem: %d" % (n.get("pendente", 0) + n.get("fila", 0)))
        self.barra.operador.setText("Operador: %s" % c.operador["nome"] if c.operador else "")
