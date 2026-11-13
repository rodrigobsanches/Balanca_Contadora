"""Tela depois de toda pesagem confirmada: 'Registrado!' + 'Retire tudo da balança'.

Regras (definidas pelo autor em 13/11):
- ao confirmar, o app TIRA A TARA automaticamente (evita tara esquecida na proxima pesagem);
- a tela so libera outras atividades quando o prato esta VAZIO: peso estavel perto de zero
  e sem tara.
"""
from PySide6.QtWidgets import QVBoxLayout, QWidget

from telas.componentes import mudar_papel, rotulo
from telas.estilo import formatar_peso


class TelaRetirar(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self._depois = None
        self.titulo = rotulo("Registrado!", "titulo")
        self.texto = rotulo("", "ok")
        self.pedido = rotulo("Retire tudo da balança", "titulo")
        self.peso = rotulo("", "subtitulo")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(120, 30, 120, 30)
        layout.addStretch()
        layout.addWidget(self.titulo)
        layout.addWidget(self.texto)
        layout.addSpacing(30)
        layout.addWidget(self.pedido)
        layout.addWidget(self.peso)
        layout.addStretch()

    def abrir(self, titulo, texto, tipo="sucesso", depois=None):
        self._depois = depois
        self.titulo.setText(titulo)
        self.texto.setText(texto)
        mudar_papel(self.texto, "ok" if tipo == "sucesso" else "erro")
        self.atualizar_peso(None, None)

    def prato_vazio(self, estavel):
        """Vazio = peso estavel perto de zero E a balanca sem tara."""
        limite = max(float(self.janela.config.get("prato_vazio_g", 2)), self.janela.balanca.divisao_g())
        return (estavel is not None and abs(estavel) <= limite
                and abs(self.janela.balanca.tara_g()) <= limite)

    def atualizar_peso(self, estavel, atual):
        """Chamado pela janela a cada leitura da balanca."""
        self.peso.setText("No prato: %s" % formatar_peso(estavel if estavel is not None else atual))
        if self._depois and self.prato_vazio(estavel):
            depois, self._depois = self._depois, None
            depois()
