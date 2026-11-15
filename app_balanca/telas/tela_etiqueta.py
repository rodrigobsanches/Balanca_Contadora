"""Tela 4c - Previa da etiqueta de conferido (com QR code) e botao Imprimir.

A impressao de verdade e feita pelo adaptador da balanca comercial. Sem ele, so a previa.
"""
from datetime import datetime

import qrcode
from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QWidget

from telas.componentes import botao, cabecalho, montar_tela, rodape
from telas.estilo import formatar_numero, formatar_peso

PAUSA_APOS_IMPRIMIR_MS = 3000   # botao desligado depois de imprimir (descarta toques repetidos)


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
        if e.get("endereco"):
            linhas.append(e["endereco"])
        for item in e["itens"]:
            linhas.append("%s  %s  x %s" % (item["produto"], item["nome"],
                                           formatar_numero(item["quantidade"])))
        linhas += ["Peso bruto: %s   Líquido: %s" % (formatar_peso(e["peso_bruto_g"]),
                                                    formatar_peso(e["peso_liquido_g"])),
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
        topo, self.titulo, self.situacao = cabecalho("Pedido conferido!")
        self.previa = PreviaEtiqueta()
        self.imprimir_botao = botao("Imprimir etiqueta", ao_clicar=self.imprimir)
        base = rodape([botao("Concluir", "secundario", janela.abrir_conferencia)], [self.imprimir_botao])
        montar_tela(self, topo, self.previa, base)

    def abrir(self, etiqueta):
        self.etiqueta = etiqueta
        self.previa.mostrar(etiqueta)
        tem_impressora = self.janela.impressora is not None
        self.imprimir_botao.setText("Imprimir etiqueta")
        self.imprimir_botao.setEnabled(tem_impressora)
        self.situacao.setText("Confira a etiqueta e toque em Imprimir" if tem_impressora
                              else "Prévia da etiqueta (impressora não configurada)")

    def imprimir(self):
        """Imprime UMA etiqueta. A impressao trava a tela por ~2 s; os toques dados nesse
        tempo ficam na fila e chegariam depois. Por isso o botao fica desligado durante
        a impressao e so volta um pouco depois, quando esses toques ja foram descartados."""
        if not (self.janela.impressora and self.etiqueta) or not self.imprimir_botao.isEnabled():
            return
        self.imprimir_botao.setEnabled(False)
        self.situacao.setText("Imprimindo...")
        self.situacao.repaint()
        ok = self.janela.impressora.imprimir_etiqueta(self.etiqueta)
        self.situacao.setText("Etiqueta impressa" if ok else "Falha ao imprimir")
        self.imprimir_botao.setText("Imprimir de novo")
        QTimer.singleShot(PAUSA_APOS_IMPRIMIR_MS, lambda: self.imprimir_botao.setEnabled(True))
