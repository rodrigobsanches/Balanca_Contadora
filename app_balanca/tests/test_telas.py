"""Teste das telas sem abrir janela (Qt 'offscreen'): o fluxo completo do inventario."""
import os
import sys
import time

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
                                     "P009": {"nome": "Sem peso", "estoque_atual": 0},
                                     "P002": {"nome": "Porca", "peso_unit_g": 2.6,
                                              "estoque_atual": 50}},
                        "pedidos": {"PED001": {"destino": "Correios - SEDEX", "status": "pendente",
                                               "itens": {"P001": {"qtd": 10}, "P002": {"qtd": 10}}}}})
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

    balanca.tarar()                                   # operador deixou uma tara
    janela.contagem.confirmar()
    app.processEvents()
    # depois de confirmar: tara tirada sozinha e pede para esvaziar o prato
    assert janela.pilha.currentWidget() is janela.retirar
    assert balanca.tara_g() == 0
    colocar_peso(app, balanca, janela, 500)           # ainda tem peca no prato: nao sai
    assert janela.pilha.currentWidget() is janela.retirar
    colocar_peso(app, balanca, janela, 0)             # prato vazio: volta aos produtos
    assert janela.pilha.currentWidget() is janela.produtos
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


def conferir_item(app, balanca, janela, codigo, esperada, gramas):
    janela.pesar_item(codigo, esperada)
    colocar_peso(app, balanca, janela, gramas)
    janela.contagem.confirmar()
    app.processEvents()
    assert janela.pilha.currentWidget() is janela.retirar
    colocar_peso(app, balanca, janela, 0)             # retira as pecas


def test_conferencia_ok_gera_etiqueta(app, sistema):
    ctrl, balanca, janela, sim, enviados = sistema
    ctrl.identificar(UID)
    janela.abrir_conferencia()
    janela.abrir_pedido("PED001")
    assert not janela.pedido.finalizar_botao.isEnabled()
    conferir_item(app, balanca, janela, "P001", 10, 104)
    assert janela.pilha.currentWidget() is janela.pedido
    conferir_item(app, balanca, janela, "P002", 10, 26)
    assert janela.pedido.finalizar_botao.isEnabled()

    janela.pedido.finalizar()
    app.processEvents()
    assert janela.pilha.currentWidget() is janela.etiqueta
    et = janela.etiqueta.etiqueta
    assert et["qr"] == "PED001" and len(et["itens"]) == 2
    assert not janela.etiqueta.imprimir_botao.isEnabled()          # sem impressora: so previa
    assert ctrl.dados.cadastro("pedidos", "PED001")["status"] == "conferido"
    assert ctrl.dados.cadastro("produtos", "P002")["estoque_atual"] == 40
    janela.etiqueta.previa.grab()                                    # desenha sem erro (QR)


def test_conferencia_com_falta_nao_libera(app, sistema):
    ctrl, balanca, janela, sim, enviados = sistema
    ctrl.identificar(UID)
    janela.abrir_pedido("PED001")
    conferir_item(app, balanca, janela, "P001", 10, 83.2)    # 8 pecas
    conferir_item(app, balanca, janela, "P002", 10, 26)
    janela.pedido.finalizar()
    app.processEvents()
    assert janela.pilha.currentWidget() is janela.mensagem
    assert "Faltam 2" in janela.mensagem.texto.text()
    assert ctrl.dados.cadastro("pedidos", "PED001")["status"] == "pendente"


class ImpressoraFalsa:
    def __init__(self):
        self.vezes = 0

    def imprimir_etiqueta(self, etiqueta):
        self.vezes += 1
        return True


def test_varios_toques_em_imprimir_saem_uma_etiqueta(app, sistema):
    ctrl, balanca, janela, sim, enviados = sistema
    janela.impressora = ImpressoraFalsa()
    janela.abrir_etiqueta({"titulo": "PEDIDO PED001", "itens": [], "qr": "PED001",
                           "peso_bruto_g": 0, "peso_liquido_g": 0})
    for _ in range(5):                      # toques repetidos enquanto imprime
        janela.etiqueta.imprimir_botao.click()
        app.processEvents()
    assert janela.impressora.vezes == 1
    assert janela.etiqueta.imprimir_botao.text() == "Imprimir de novo"


def test_mexer_no_prato_conta_como_uso_e_presenca_nao(app, sistema):
    ctrl, balanca, janela, sim, enviados = sistema
    ctrl.identificar(UID)
    janela.abrir_conferencia()
    janela.abrir_pedido("PED001")
    janela.pesar_item("P001", 10)
    colocar_peso(app, balanca, janela, 0)
    janela._ultima_atividade -= 100         # parado ha muito tempo
    colocar_peso(app, balanca, janela, 52)  # coloca pecas: conta como uso
    assert time.monotonic() - janela._ultima_atividade < 5

    janela._ultima_atividade -= 100
    ctrl.tratar_evento({"t": "presenca", "perto": True})   # so estar perto nao conta
    app.processEvents()
    janela._a_cada_segundo()
    assert janela.pilha.currentWidget() is janela.descanso


def test_tara_pre_programada(app, sistema):
    ctrl, balanca, janela, sim, enviados = sistema
    ctrl.tratar_evento({"t": "sync", "ok": True, "operadores": {UID: {"nome": "R", "ativo": True}},
                        "produtos": {"P001": {"nome": "Parafuso", "peso_unit_g": 3}}, "pedidos": {},
                        "taras": {"T2": {"nome": "Caixa", "g": 80, "ordem": 2},
                                  "T1": {"nome": "Pote", "g": 26, "ordem": 1},
                                  "T3": {"nome": "Vazia", "g": 0, "ordem": 3}}})
    assert [t["nome"] for t in ctrl.taras()] == ["Pote", "Caixa"]   # ordem; peso 0 fica de fora
    ctrl.identificar(UID)
    janela.abrir_inventario()
    janela.abrir_contagem("P001")
    assert [b.text() for b in janela.contagem.taras.botoes] == ["Pote\n26 g", "Caixa\n80 g"]
    janela.contagem.taras.botoes[0].click()
    assert balanca.tara_g() == 26
    colocar_peso(app, balanca, janela, 26 + 30)                  # pote + 10 parafusos de 3 g
    assert janela.contagem.quantidade.text() == "10"

    # firmware antigo (sem "taras" no sync) nao apaga as taras guardadas
    ctrl.tratar_evento({"t": "sync", "ok": True, "operadores": {}, "produtos": {}, "pedidos": {}})
    assert len(ctrl.taras()) == 2


def test_zerar_libera_o_retire_tudo_com_prato_marcando_peso(app, sistema):
    ctrl, balanca, janela, sim, enviados = sistema
    ctrl.identificar(UID)
    janela.abrir_inventario()
    janela.abrir_contagem("P001")
    colocar_peso(app, balanca, janela, 104)
    janela.contagem.confirmar()
    app.processEvents()
    colocar_peso(app, balanca, janela, 11)             # prato vazio, mas a celula marca 11 g
    assert janela.pilha.currentWidget() is janela.retirar
    assert janela.zerar_balanca()
    balanca._mudou_em -= 5
    janela.ler_balanca()
    app.processEvents()
    assert janela.pilha.currentWidget() is janela.produtos
    assert janela.barra.aviso.text() == "Balança zerada"


def test_sair_da_pesagem_tira_a_tara(app, sistema):
    ctrl, balanca, janela, sim, enviados = sistema
    ctrl.identificar(UID)
    janela.abrir_inventario()
    janela.abrir_contagem("P001")
    balanca.tara_predefinida(26)
    janela.abrir_amostra()                       # amostra continua com a tara do pote
    assert balanca.tara_g() == 26
    janela.voltar_contagem()
    janela.voltar_da_contagem()                  # saiu da pesagem: sem tara
    assert balanca.tara_g() == 0
