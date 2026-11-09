"""Tela 4c - Previa da etiqueta de conferido (com QR code) e botao Imprimir.

A impressao de verdade e feita pelo adaptador privado (Fase 5). Sem ele, so a previa.
"""
from datetime import datetime

import qrcode
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from telas.componentes import botao, rotulo
from telas.estilo import formatar_numero, formatar_peso


def matriz_qr(texto):
    """Quadradinhos do QR code (True = preto). Nao precisa de biblioteca de imagem."""
    qr = qrcode.QRCode(border=0, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(texto)
    qr.make(fit=True)
    return qr.get_matrix()


def data_legivel(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return iso or ""


class PreviaEtiqueta(QWidget):
    """Desenha a etiqueta como ela sai da impressora (papel branco, texto preto)."""
    def __init__(self):
        super().__init__()
        self.etiqueta = None
        self.setMinimumSize(560, 380)

    def mostrar(self, etiqueta):
        self.etiqueta = etiqueta
        self.update()

    def paintEvent(self, _evento):
        if not self.etiqueta:
            return
        e = self.etiqueta
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        papel = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        p.setPen(QColor("#9AA5B1"))
        p.setBrush(QColor("white"))
        p.drawRoundedRect(papel, 8, 8)

        m = 22
        x, y = papel.left() + m, papel.top() + m
        p.setPen(QColor("black"))
        p.setFont(QFont("Arial", 18, QFont.Bold))
        p.drawText(QRectF(x, y, papel.width() - 2 * m, 30), Qt.AlignLeft, e["titulo"])
        y += 40
        p.setFont(QFont("Arial", 12))
        linhas = ["Destino: %s" % e.get("destino", "")]
        for item in e["itens"]:
            linhas.append("%s  %s  x %s" % (item["produto"], item["nome"],
                                           formatar_numero(item["quantidade"])))
        linhas += ["Peso: %s" % formatar_peso(e["peso_total_g"]),
                   "Conferido por: %s" % e.get("operador", ""),
                   "%s   %s" % (data_legivel(e.get("data_hora")), e.get("balanca", ""))]
        for linha in linhas:
            p.drawText(QRectF(x, y, papel.width() * 0.62, 24), Qt.AlignLeft, linha)
            y += 26

        # QR code no canto direito
        matriz = matriz_qr(e["qr"])
        lado = min(papel.width() * 0.32, papel.height() - 2 * m - 40)
        celula = lado / len(matriz)
        qx = papel.right() - m - lado
        qy = papel.top() + m + 40
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("black"))
        for i, fileira in enumerate(matriz):
            for j, preto in enumerate(fileira):
                if preto:
                    p.drawRect(QRectF(qx + j * celula, qy + i * celula, celula + 0.5, celula + 0.5))
        p.end()


class TelaEtiqueta(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.etiqueta = None
        self.titulo = rotulo("Pedido conferido!", "titulo")
        self.previa = PreviaEtiqueta()
        self.situacao = rotulo("", "subtitulo")

        self.imprimir_botao = botao("Imprimir etiqueta", ao_clicar=self.imprimir, altura=90)
        lateral = QVBoxLayout()
        lateral.addWidget(self.situacao)
        lateral.addStretch()
        lateral.addWidget(self.imprimir_botao)
        lateral.addWidget(botao("Concluir", "sucesso", janela.abrir_conferencia, altura=90))

        corpo = QHBoxLayout()
        corpo.setSpacing(30)
        corpo.addWidget(self.previa, 3)
        corpo.addLayout(lateral, 2)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 16, 40, 16)
        layout.addWidget(self.titulo)
        layout.addLayout(corpo, 1)

    def abrir(self, etiqueta):
        self.etiqueta = etiqueta
        self.previa.mostrar(etiqueta)
        tem_impressora = self.janela.impressora is not None
        self.imprimir_botao.setEnabled(tem_impressora)
        self.situacao.setText("Confira a etiqueta" if tem_impressora
                              else "Prévia da etiqueta\n(impressora não configurada)")

    def imprimir(self):
        if self.janela.impressora and self.etiqueta:
            ok = self.janela.impressora.imprimir_etiqueta(self.etiqueta)
            self.situacao.setText("Etiqueta impressa" if ok else "Falha ao imprimir")
