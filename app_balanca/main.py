"""App da balanca contadora de pecas.

Rodar na pasta do projeto (feche o Thonny antes: ele ocupa a porta da ESP32):

    .venv\\Scripts\\python app_balanca\\main.py

Configuracao: app_balanca/config.json (copie do config_exemplo.json).
Com "balanca": "simulada", abre tambem a janela de Simulacao (peso, chaveiro, presenca).
"""
import os
import sys

PASTA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PASTA)

from PySide6.QtCore import QObject, Signal  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from balanca_base import criar_balanca  # noqa: E402
from config_app import caminho_dados, carregar_config  # noqa: E402
from controlador import Controlador  # noqa: E402
from dados_locais import DadosLocais  # noqa: E402
from esp32_serial import LigacaoESP32  # noqa: E402
from telas.janela import JanelaPrincipal  # noqa: E402
from telas.simulacao import JanelaSimulacao  # noqa: E402


class Ponte(QObject):
    """Leva o que chega da serial (outra thread) para a thread da tela, com seguranca.
    Assim o controlador e as telas sempre rodam na mesma thread."""
    evento = Signal(dict)
    conexao = Signal(bool, object)
    aviso = Signal(str, object)


def montar(config, enviar_esp32=None):
    """Cria controlador, balanca e janelas. Separado do main() para os testes usarem."""
    dados = DadosLocais(caminho_dados(config))
    balanca = criar_balanca(config)
    balanca.conectar()
    ponte = Ponte()
    ctrl = Controlador(config, dados, enviar_esp32 or (lambda cmd: False), avisar=ponte.aviso.emit)
    ponte.evento.connect(ctrl.tratar_evento)
    ponte.conexao.connect(ctrl.ao_conexao)
    janela = JanelaPrincipal(config, ctrl, balanca)
    ponte.aviso.connect(janela.ao_aviso)
    simulacao = None
    if balanca.nome == "simulada":
        simulacao = JanelaSimulacao(balanca, ctrl, janela)
        ponte.aviso.connect(simulacao.ao_aviso)
    return ponte, ctrl, balanca, janela, simulacao


def main():
    config = carregar_config()
    app = QApplication(sys.argv)
    ligacao = None

    def enviar(cmd):
        return ligacao.enviar(cmd) if ligacao else False

    ponte, ctrl, balanca, janela, simulacao = montar(config, enviar)
    ligacao = LigacaoESP32(ponte.evento.emit,
                           lambda conectado, porta: ponte.conexao.emit(conectado, porta),
                           config.get("porta_esp32", "auto"))
    janela.mostrar()
    if simulacao:
        simulacao.move(janela.x() + janela.width() + 10, janela.y())
        simulacao.show()
    ligacao.iniciar()
    codigo = app.exec()
    ligacao.parar()
    balanca.desconectar()
    ctrl.dados.fechar()
    return codigo


if __name__ == "__main__":
    sys.exit(main())
