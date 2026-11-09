"""Teste das telas sem abrir janela (Qt 'offscreen'): o fluxo completo do inventario."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from main import montar  # noqa: E402

UID = "36:BD:9A:AC"


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def sistema(app, tmp_path):
    enviados = []

    def enviar(cmd):
        enviados.append(cmd)
        return True

    config = {"balanca": "simulada", "arquivo_dados": str(tmp_path / "t.db"),
              "segundos_para_sair": 60, "amostra_padrao": 10}
    ponte, ctrl, balanca, janela, sim = montar(config, enviar)
    ctrl.tratar_evento({"t": "sync", "ok": True,
                        "operadores": {UID: {"nome": "Rodrigo Sanches", "ativo": True}},
                        "produtos": {"P001": {"nome": "Parafuso", "peso_unit_g": 10.4,
                                              "estoque_atual": 0},
                                     "P009": {"nome": "Sem peso", "estoque_atual": 0}},
                        "pedidos": {}})
    app.processEvents()
    yield ctrl, balanca, janela, sim, enviados
    janela.close()
    sim.close()
    ctrl.dados.fechar()


def colocar_peso(app, balanca, janela, gramas):
    balanca.definir_peso(gramas)
    balanca._mudou_em -= 5          # "espera" o peso estabilizar
    janela.ler_balanca()
    app.processEvents()


def test_fluxo_inventario(app, sistema):
    ctrl, balanca, janela, sim, enviados = sistema
    assert janela.pilha.currentWidget() is janela.descanso

    sim.chaveiros.setCurrentIndex(sim.chaveiros.findData(UID))
    sim.encostar()
    app.processEvents()
    assert janela.pilha.currentWidget() is janela.menu
    assert "Rodrigo" in janela.menu.ola.text()

    janela.abrir_inventario()
    janela.abrir_contagem("P001")
    colocar_peso(app, balanca, janela, 1040)
    assert janela.contagem.quantidade.text() == "100"
    assert janela.contagem.botao_confirmar.isEnabled()

    janela.contagem.confirmar()
    app.processEvents()
    assert janela.pilha.currentWidget() is janela.mensagem
    assert ctrl.dados.cadastro("produtos", "P001")["estoque_atual"] == 100
    assert any(c.get("path", "").startswith("contagens/") for c in enviados)


def test_amostra_define_peso_unitario(app, sistema):
    ctrl, balanca, janela, sim, enviados = sistema
    ctrl.identificar(UID)
    janela.abrir_contagem("P009")
    colocar_peso(app, balanca, janela, 500)
    assert not janela.contagem.botao_confirmar.isEnabled()     # sem peso unitario ainda

    janela.abrir_amostra()
    colocar_peso(app, balanca, janela, 52)                    # 10 pecas de 5,2 g
    janela.amostra.confirmar(salvar=True)
    app.processEvents()
    assert janela.pilha.currentWidget() is janela.contagem
    assert janela.contagem.peso_unit == pytest.approx(5.2)
    assert ctrl.dados.cadastro("produtos", "P009")["peso_unit_g"] == pytest.approx(5.2)

    colocar_peso(app, balanca, janela, 520)
    assert janela.contagem.quantidade.text() == "100"


def test_chaveiro_desconhecido_fica_no_descanso(app, sistema):
    ctrl, balanca, janela, sim, enviados = sistema
    sim.chaveiros.setCurrentIndex(sim.chaveiros.count() - 1)  # "Desconhecido"
    sim.encostar()
    app.processEvents()
    assert janela.pilha.currentWidget() is janela.descanso
    assert not janela.descanso.mensagem.isHidden()


def test_sair_volta_ao_descanso(app, sistema):
    ctrl, balanca, janela, sim, enviados = sistema
    ctrl.identificar(UID)
    app.processEvents()
    ctrl.sair()
    app.processEvents()
    assert janela.pilha.currentWidget() is janela.descanso
