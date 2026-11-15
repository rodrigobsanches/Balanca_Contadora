"""Tela 1 - Descanso: 'Identifique-se para iniciar' + animacao do chaveiro encostando no leitor."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget

from telas.componentes import mudar_papel, rotulo
from telas.estilo import COR

CICLO_S = 3.0          # duracao de uma volta da animacao
QUADROS_MS = 33        # ~30 quadros por segundo (so enquanto a tela esta visivel)
# O leitor de chaveiro fica na LATERAL da balanca, a esquerda da tela (marcado por uma fita
# cinza). Por isso o desenho mostra a lateral saindo da borda esquerda da tela e o chaveiro
# vindo da direita ate a fita. Se o leitor mudar de lugar, mudar o desenho aqui.
LATERAL_LARGURA = 190  # parte da lateral da balanca que aparece na tela
FITA = (112, 60, 150)  # fita cinza na lateral (encostada na borda dela): x, largura, altura


def suave(t):
    """0..1 -> 0..1 com inicio e fim suaves (movimento mais natural)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class AnimacaoChaveiro(QWidget):
    """Desenho animado: o chaveiro vai ate a fita cinza na lateral da balanca, encosta, o
    leitor 'responde' (ondas verdes + OK) e o chaveiro volta. Desenhado com QPainter: nao
    precisa de arquivo de imagem."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(380)
        self.tempo = 0.0
        self._timer = QTimer(self, interval=QUADROS_MS, timeout=self._avancar)

    def showEvent(self, evento):
        self._timer.start()
        super().showEvent(evento)

    def hideEvent(self, evento):
        self._timer.stop()
        super().hideEvent(evento)

    def _avancar(self):
        self.tempo = (self.tempo + QUADROS_MS / 1000) % CICLO_S
        self.update()

    # ---------- fases da volta (em segundos) ----------
    # 0,0-0,4 parado | 0,4-1,3 vai ate o leitor | 1,3-2,3 encostado (ondas, OK) | 2,3-3,0 volta
    def _posicao(self):
        t = self.tempo
        if t < 0.4:
            return 0.0
        if t < 1.3:
            return suave((t - 0.4) / 0.9)
        if t < 2.3:
            return 1.0
        return 1.0 - suave((t - 2.3) / 0.7)

    def paintEvent(self, _evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cy = h / 2
        encostado = 1.3 <= self.tempo < 2.3

        # lateral da balanca saindo da borda esquerda da tela, com a fita cinza do leitor
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(COR["visor"]))
        p.drawRoundedRect(QRectF(-40, cy - 170, LATERAL_LARGURA + 40, 340), 28, 28)
        fx, fl, fa = FITA
        fita = QRectF(fx, cy - fa / 2, fl, fa)
        p.setBrush(QColor("#A7B1BC"))
        p.drawRoundedRect(fita, 6, 6)
        self._ondas(p, QPointF(LATERAL_LARGURA, cy), encostado)
        if encostado:
            self._ok(p, QPointF(fita.center().x(), fita.top() - 45))
        else:
            self._setas(p, QPointF(LATERAL_LARGURA + 60, cy - 130))

        # chaveiro: vem da direita e encosta na fita
        inicio_x = w * 0.72
        fim_x = LATERAL_LARGURA + 34   # a ponta do chaveiro encosta na lateral, na altura da fita
        x = inicio_x + (fim_x - inicio_x) * self._posicao()
        balanco = 6 * math.sin(self.tempo * 6) if not encostado else 0   # leve balanco no ar
        self._chaveiro(p, QPointF(x, cy + balanco))
        p.end()

    def _ondas(self, p, origem, encostado):
        """Arcos saindo da fita para a direita: fracos o tempo todo, verdes quando encosta."""
        cor = QColor(COR["sucesso"] if encostado else COR["primaria"])
        fase = (self.tempo * (1.6 if encostado else 0.8)) % 1.0
        p.setBrush(Qt.NoBrush)
        for i in range(3):
            k = (fase + i / 3) % 1.0
            c = QColor(cor)
            c.setAlphaF((1 - k) * (0.7 if encostado else 0.35))
            p.setPen(QPen(c, 6, Qt.SolidLine, Qt.RoundCap))
            raio = 30 + k * 140
            p.drawArc(QRectF(origem.x() - raio, origem.y() - raio, 2 * raio, 2 * raio),
                      -45 * 16, 90 * 16)

    def _setas(self, p, inicio):
        """Tres setas '<' piscando em sequencia, apontando para a lateral (onde encostar)."""
        for i in range(3):
            brilho = (math.sin(self.tempo * 5 + i * 1.2) + 1) / 2
            c = QColor(COR["primaria"])
            c.setAlphaF(0.25 + 0.75 * brilho)
            p.setPen(QPen(c, 8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            x = inicio.x() + i * 45
            seta = QPainterPath(QPointF(x + 18, inicio.y() - 22))
            seta.lineTo(x, inicio.y())
            seta.lineTo(x + 18, inicio.y() + 22)
            p.drawPath(seta)

    @staticmethod
    def _chaveiro(p, centro):
        """Chaveiro em gota (como os do kit), com a argola a direita: a ponta redonda encosta."""
        x, y = centro.x(), centro.y()
        p.setPen(QPen(QColor(COR["texto_suave"]), 6))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(x + 92, y), 22, 22)                   # argola
        corpo = QPainterPath()
        corpo.moveTo(x + 70, y)
        corpo.cubicTo(x + 50, y - 70, x - 30, y - 60, x - 30, y)
        corpo.cubicTo(x - 30, y + 60, x + 50, y + 70, x + 70, y)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(COR["primaria"]))
        p.drawPath(corpo)
        p.setBrush(QColor(COR["fundo"]))
        p.drawEllipse(QPointF(x + 52, y), 9, 9)                     # furo da argola

    @staticmethod
    def _ok(p, centro):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(COR["sucesso"]))
        p.drawEllipse(centro, 30, 30)
        p.setPen(QPen(QColor("white"), 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        caminho = QPainterPath(QPointF(centro.x() - 13, centro.y()))
        caminho.lineTo(centro.x() - 3, centro.y() + 10)
        caminho.lineTo(centro.x() + 14, centro.y() - 10)
        p.setBrush(Qt.NoBrush)
        p.drawPath(caminho)


class TelaDescanso(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.chamada = rotulo("Identifique-se para iniciar", "titulo")
        self.animacao = AnimacaoChaveiro()
        self.mensagem = rotulo("", "info")
        self.mensagem.hide()
        self._esconder = QTimer(self, singleShot=True, timeout=self.mensagem.hide)

        # a animacao vai de borda a borda: a lateral da balanca "sai" da borda esquerda da tela
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 30, 0, 30)
        layout.addStretch(1)
        layout.addWidget(self.chamada)
        layout.addSpacing(10)
        layout.addWidget(self.animacao)
        layout.addWidget(self.mensagem, 0, Qt.AlignHCenter)
        layout.addStretch(1)

    def definir_presenca(self, perto):
        """Alguem chegou perto (sensor de presenca): o texto e o mesmo; a animacao ja chama."""

    def mostrar_mensagem(self, texto, papel="info", segundos=4):
        self.mensagem.setText(texto)
        mudar_papel(self.mensagem, papel)
        self.mensagem.show()
        self._esconder.start(int(segundos * 1000))
