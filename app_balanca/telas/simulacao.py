"""Janela de simulacao (so no modo simulado): faz o papel da balanca e dos sensores.

- Peso no prato: digitar, ou somar/tirar pecas do produto aberto na contagem.
- Chaveiro: escolhe um operador (ou um desconhecido) e "encosta".
- Presenca: alguem perto / longe.
Com a ESP32 ligada, o chaveiro e o sensor de verdade tambem funcionam.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QGridLayout, QGroupBox, QHBoxLayout,
                               QPushButton, QVBoxLayout, QWidget)

UID_DESCONHECIDO = "99:99:99:99"


class JanelaSimulacao(QWidget):
    def __init__(self, balanca, ctrl, janela):
        super().__init__()
        self.balanca = balanca
        self.ctrl = ctrl
        self.janela = janela
        self.setWindowTitle("Simulação")
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("QWidget { font-size: 15px; } QPushButton { padding: 6px 10px; }")

        # --- peso ---
        self.peso = QDoubleSpinBox(decimals=1, maximum=30000, singleStep=1, suffix=" g")
        self.peso.valueChanged.connect(self.balanca.definir_peso)
        grade = QGridLayout()
        grade.addWidget(self.peso, 0, 0, 1, 4)
        botoes = [("+1 peça", 1), ("+10 peças", 10), ("−1 peça", -1), ("−10 peças", -10)]
        for i, (texto, n) in enumerate(botoes):
            b = QPushButton(texto)
            b.clicked.connect(lambda _=False, n=n: self.somar_pecas(n))
            grade.addWidget(b, 1, i)
        esvaziar = QPushButton("Esvaziar prato")
        esvaziar.clicked.connect(lambda: self.peso.setValue(0))
        grade.addWidget(esvaziar, 2, 0, 1, 4)
        caixa_peso = QGroupBox("Peso no prato (bruto)")
        caixa_peso.setLayout(grade)

        # --- chaveiro ---
        self.chaveiros = QComboBox()
        encostar = QPushButton("Encostar chaveiro")
        encostar.clicked.connect(self.encostar)
        linha = QHBoxLayout()
        linha.addWidget(self.chaveiros, 1)
        linha.addWidget(encostar)
        caixa_rfid = QGroupBox("Chaveiro (RFID)")
        caixa_rfid.setLayout(linha)

        # --- presenca ---
        self.perto = QPushButton("Pessoa perto")
        self.perto.setCheckable(True)
        self.perto.toggled.connect(self.mudar_presenca)
        caixa_presenca = QGroupBox("Sensor de presença")
        QVBoxLayout(caixa_presenca).addWidget(self.perto)

        layout = QVBoxLayout(self)
        layout.addWidget(caixa_peso)
        layout.addWidget(caixa_rfid)
        layout.addWidget(caixa_presenca)
        self.recarregar_chaveiros()

    def recarregar_chaveiros(self):
        atual = self.chaveiros.currentData()
        self.chaveiros.clear()
        for uid, op in sorted(self.ctrl.dados.cadastros("operadores").items()):
            self.chaveiros.addItem("%s  (%s)" % (op.get("nome", uid), uid), uid)
        self.chaveiros.addItem("Desconhecido (%s)" % UID_DESCONHECIDO, UID_DESCONHECIDO)
        # mantem a escolha anterior; se nao havia (ou era o desconhecido), fica o 1o operador
        i = self.chaveiros.findData(atual) if atual not in (None, UID_DESCONHECIDO) else -1
        self.chaveiros.setCurrentIndex(max(i, 0))

    def somar_pecas(self, n):
        """Soma n pecas do produto aberto (usa o peso unitario do cadastro ou da amostra)."""
        unit = self.janela.contagem.peso_unit or self.janela.contagem.produto.get("peso_unit_g")
        if not unit:
            return
        self.peso.setValue(max(0.0, self.peso.value() + n * float(unit)))

    def encostar(self):
        uid = self.chaveiros.currentData()
        if uid:
            self.ctrl.tratar_evento({"t": "rfid", "uid": uid})

    def mudar_presenca(self, perto):
        self.perto.setText("Pessoa perto" if not perto else "Pessoa perto (ativo)")
        self.ctrl.tratar_evento({"t": "presenca", "perto": perto, "cm": 40 if perto else 999})

    def ao_aviso(self, tipo, info):
        if tipo == "cadastros":
            self.recarregar_chaveiros()
