"""Testes da Fase 3a: dados locais, ligacao serial (partes sem hardware) e controlador."""
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contagem import contar_pecas  # noqa: E402
from controlador import Controlador  # noqa: E402
from dados_locais import DadosLocais  # noqa: E402
from esp32_serial import ControleEnvio, escolher_porta, interpretar_linha  # noqa: E402

UID_RODRIGO = "36:BD:9A:AC"


# ---------------- apoio ----------------
@pytest.fixture
def dados(tmp_path):
    d = DadosLocais(str(tmp_path / "teste.db"))
    d.salvar_cadastros("operadores", {UID_RODRIGO: {"nome": "Rodrigo", "ativo": True},
                                      "AA:BB": {"nome": "Inativo", "ativo": False}})
    d.salvar_cadastros("produtos", {"P001": {"nome": "Parafuso", "peso_unit_g": 10.4,
                                             "estoque_atual": 50, "estoque_minimo": 10}})
    d.salvar_cadastros("pedidos", {"PED001": {"status": "pendente", "itens": {"P001": {"qtd": 10}}},
                                   "PED002": {"status": "conferido", "itens": {}}})
    yield d
    d.fechar()


class EspFalsa:
    """Faz o papel da ESP32: guarda os comandos recebidos."""
    def __init__(self, conectada=True):
        self.conectada = conectada
        self.comandos = []

    def __call__(self, comando):
        if not self.conectada:
            return False
        self.comandos.append(comando)
        return True

    def de_tipo(self, c):
        return [x for x in self.comandos if x["c"] == c]


@pytest.fixture
def esp():
    return EspFalsa()


@pytest.fixture
def ctrl(dados, esp):
    avisos = []
    contador = iter(range(1, 1000))
    c = Controlador({"id_balanca": "BAL-01"}, dados, esp,
                    avisar=lambda tipo, info: avisos.append((tipo, info)),
                    gerar_id=lambda: "id-%d" % next(contador),
                    relogio=lambda: "2026-11-15T14:32:05")
    c.avisos = avisos
    return c


# ---------------- serial ----------------
def test_escolher_porta_prefere_usb_nativa():
    portas = [SimpleNamespace(device="COM3", vid=0x8086),
              SimpleNamespace(device="COM7", vid=0x1A86),
              SimpleNamespace(device="COM5", vid=0x303A)]
    assert escolher_porta(portas) == "COM5"
    assert escolher_porta(portas[:2]) == "COM7"
    assert escolher_porta(portas[:1]) is None
    assert escolher_porta(portas, "COM9") == "COM9"


def test_interpretar_linha():
    assert interpretar_linha('{"t":"rfid","uid":"X"}\r\n') == {"t": "rfid", "uid": "X"}
    assert interpretar_linha("MPY: soft reboot") is None
    assert interpretar_linha('{"c":"ping"}') is None   # eco de comando, nao e evento
    assert interpretar_linha("{quebrado") is None


def test_controle_envio_um_comando_longo_por_vez():
    c = ControleEnvio(tempo_limite_s=15)
    c.adicionar({"c": "enviar", "id": "a"})
    c.adicionar({"c": "atualizar", "id": "b"})
    c.adicionar({"c": "sinal", "estado": "ok"})
    assert c.proximo(0)["id"] == "a"
    assert c.proximo(1) == {"c": "sinal", "estado": "ok"}   # curto passa na frente
    assert c.proximo(2) is None                              # "b" espera o ack de "a"
    c.resposta({"t": "ack", "id": "outro", "ok": True})
    assert c.proximo(3) is None
    c.resposta({"t": "ack", "id": "a", "ok": False, "fila": True})
    assert c.proximo(4)["id"] == "b"


def test_controle_envio_sync_e_tempo_limite():
    c = ControleEnvio(tempo_limite_s=15)
    c.adicionar({"c": "sync"})
    c.adicionar({"c": "enviar", "id": "a"})
    assert c.proximo(0)["c"] == "sync"
    assert c.proximo(5) is None
    assert c.proximo(16)["id"] == "a"          # a resposta do sync nao veio: segue
    c.resposta({"t": "hello"})                 # placa reiniciou: libera
    c.adicionar({"c": "enviar", "id": "b"})
    assert c.proximo(17)["id"] == "b"
    c.limpar()
    assert c.proximo(18) is None


# ---------------- dados locais ----------------
def test_registro_muda_de_estado(dados):
    dados.novo_registro("r1", "put", "contagens/r1", {"a": 1})
    assert [r["id"] for r in dados.pendentes()] == ["r1"]
    dados.marcar("r1", "enviado")
    assert dados.pendentes() == []
    assert dados.contar_por_status() == {"enviado": 1}


def test_atualizar_cadastro_local(dados):
    dados.atualizar_cadastro("produtos", "P001", {"estoque_atual": 7})
    assert dados.cadastro("produtos", "P001")["estoque_atual"] == 7
    assert dados.cadastro("produtos", "P001")["nome"] == "Parafuso"


# ---------------- controlador ----------------
def test_conectar_pede_sync_e_reenvia_pendentes(ctrl, esp, dados):
    dados.novo_registro("velho", "put", "contagens/velho", {"id": "velho"})
    ctrl.ao_conexao(True, "COM5")
    assert esp.comandos[0] == {"c": "sync"}
    assert esp.de_tipo("enviar")[0]["id"] == "velho"


def test_sync_guarda_cadastros(ctrl, dados):
    ctrl.tratar_evento({"t": "sync", "ok": True, "operadores": {"X": {"nome": "Ana"}},
                        "produtos": {}, "pedidos": {}})
    assert dados.cadastros("operadores") == {"X": {"nome": "Ana"}}
    assert ("cadastros", None) in ctrl.avisos


def test_sync_falho_mantem_cadastros(ctrl, dados):
    ctrl.tratar_evento({"t": "sync", "ok": False, "erro": "sem wifi"})
    assert UID_RODRIGO in dados.cadastros("operadores")


def test_chaveiro_cadastrado_faz_login(ctrl, esp):
    ctrl.tratar_evento({"t": "rfid", "uid": UID_RODRIGO})
    assert (ctrl.operador["uid"], ctrl.operador["nome"]) == (UID_RODRIGO, "Rodrigo")
    assert {"c": "sinal", "estado": "ok"} in esp.comandos


def test_chaveiro_desconhecido_e_bloqueado_e_registrado(ctrl, esp):
    assert not ctrl.identificar("99:99")
    assert not ctrl.identificar("AA:BB")       # cadastrado mas inativo
    assert ctrl.operador is None
    enviados = esp.de_tipo("enviar")
    assert enviados[0]["path"] == "rfid_desconhecidos/99:99"
    assert {"c": "sinal", "estado": "erro"} in esp.comandos


def test_wifi_voltando_pede_sync(ctrl, esp):
    ctrl.tratar_evento({"t": "status", "wifi": False, "fila": 0})
    assert esp.de_tipo("sync") == []
    ctrl.tratar_evento({"t": "status", "wifi": True, "fila": 0})
    ctrl.tratar_evento({"t": "status", "wifi": True, "fila": 0})   # continua ligado: nao repete
    assert len(esp.de_tipo("sync")) == 1


def test_sync_periodico_so_em_descanso(dados, esp):
    agora = [1000.0]
    c = Controlador({"segundos_sync_descanso": 120}, dados, esp, segundos=lambda: agora[0])
    c.ao_conexao(True)                       # conectou: 1o sync
    assert len(esp.de_tipo("sync")) == 1
    agora[0] += 60
    c.sync_periodico()                       # ainda nao deu o intervalo
    assert len(esp.de_tipo("sync")) == 1
    agora[0] += 60
    c.sync_periodico()                       # 120 s em descanso: pede de novo
    assert len(esp.de_tipo("sync")) == 2
    c.operador = {"uid": "X", "nome": "Ana"}
    agora[0] += 500
    c.sync_periodico()                       # alguem logado: nao atrapalha a operacao
    assert len(esp.de_tipo("sync")) == 2
    c.operador = None
    c.config["segundos_sync_descanso"] = 0   # 0 desliga
    c.sync_periodico()
    assert len(esp.de_tipo("sync")) == 2


def test_chaveiro_novo_confere_na_nuvem_antes_de_recusar(ctrl, esp, dados):
    ctrl.tratar_evento({"t": "status", "wifi": True})
    assert ctrl.identificar("NOVO:01") is None              # ainda nao sabe: pede sync
    assert ("verificando", {"uid": "NOVO:01"}) in ctrl.avisos
    assert esp.de_tipo("enviar") == []                      # nao registrou como desconhecido
    ctrl.tratar_evento({"t": "sync", "ok": True, "produtos": {}, "pedidos": {},
                        "operadores": {"NOVO:01": {"nome": "Ana", "ativo": True}}})
    assert (ctrl.operador["uid"], ctrl.operador["nome"]) == ("NOVO:01", "Ana")


def test_chaveiro_novo_que_continua_desconhecido(ctrl, esp):
    ctrl.tratar_evento({"t": "status", "wifi": True})
    ctrl.identificar("NOVO:02")
    ctrl.tratar_evento({"t": "sync", "ok": True, "operadores": {}, "produtos": {}, "pedidos": {}})
    assert ctrl.operador is None
    assert esp.de_tipo("enviar")[0]["path"] == "rfid_desconhecidos/NOVO:02"


def test_inventario_registra_e_substitui_estoque(ctrl, esp, dados):
    ctrl.identificar(UID_RODRIGO)
    c = contar_pecas(1040, 10.4)
    reg = ctrl.confirmar_inventario("P001", c, 1040, 0, 10.4, "amostra")
    assert reg["quantidade"] == 100 and reg["modo"] == "inventario"
    assert reg["operador_nome"] == "Rodrigo" and reg["produto_nome"] == "Parafuso"
    put = esp.de_tipo("enviar")[-1]
    assert put["path"] == "contagens/" + reg["id"] and put["dados"]["id"] == reg["id"]
    patch = esp.de_tipo("atualizar")[-1]
    assert patch["path"] == "produtos/P001" and patch["dados"] == {"estoque_atual": 100}
    assert dados.cadastro("produtos", "P001")["estoque_atual"] == 100


def test_ack_atualiza_registro(ctrl, dados):
    ctrl.identificar(UID_RODRIGO)
    reg = ctrl.confirmar_inventario("P001", contar_pecas(104, 10.4), 104, 0, 10.4)
    ctrl.tratar_evento({"t": "ack", "id": reg["id"], "ok": False, "fila": True})
    assert dados.registro(reg["id"])["status"] == "fila"
    ctrl.tratar_evento({"t": "ack", "id": reg["id"], "ok": True, "da_fila": True})
    assert dados.registro(reg["id"])["status"] == "enviado"


def test_sem_esp32_fica_pendente(dados):
    esp = EspFalsa(conectada=False)
    c = Controlador({}, dados, esp)
    c.identificar(UID_RODRIGO)
    c.confirmar_inventario("P001", contar_pecas(104, 10.4), 104, 0, 10.4)
    assert len(dados.pendentes()) == 2   # contagem + estoque


def test_pedidos_pendentes(ctrl):
    assert list(ctrl.pedidos_pendentes()) == ["PED001"]


def test_conferencia_ok_desconta_estoque_e_libera_pedido(ctrl, esp, dados):
    ctrl.identificar(UID_RODRIGO)
    reg, res = ctrl.conferir_item("PED001", "P001", contar_pecas(104, 10.4), 10, 104, 0, 10.4)
    assert res.resultado == "OK" and reg["pedido_id"] == "PED001"
    assert ctrl.finalizar_conferencia("PED001", [reg])
    assert dados.cadastro("produtos", "P001")["estoque_atual"] == 40   # 50 - 10
    assert dados.cadastro("pedidos", "PED001")["status"] == "conferido"
    pedido = [x for x in esp.de_tipo("atualizar") if x["path"] == "pedidos/PED001"][0]
    assert pedido["dados"]["status"] == "conferido"


def test_conferencia_com_falta_nao_libera(ctrl, dados):
    ctrl.identificar(UID_RODRIGO)
    reg, res = ctrl.conferir_item("PED001", "P001", contar_pecas(83.2, 10.4), 10, 83.2, 0, 10.4)
    assert res.resultado == "FALTA" and res.diferenca == -2
    assert not ctrl.finalizar_conferencia("PED001", [reg])
    assert dados.cadastro("produtos", "P001")["estoque_atual"] == 50
    assert dados.cadastro("pedidos", "PED001")["status"] == "pendente"


def test_qr_vira_link_do_dashboard(dados, esp):
    c = Controlador({"url_dashboard": "https://exemplo.streamlit.app/"}, dados, esp)
    assert c.conteudo_qr("PED001") == "https://exemplo.streamlit.app/?pedido=PED001"
    assert Controlador({}, dados, esp).conteudo_qr("PED001") == "PED001"


def test_display_mostra_numero_do_operador(dados, esp):
    dados.salvar_cadastros("operadores", {"AA:01": {"nome": "Ana", "ativo": True, "numero": 7},
                                          "AA:02": {"nome": "Bia", "ativo": True}})
    c = Controlador({}, dados, esp)
    c.identificar("AA:01")
    assert esp.de_tipo("display")[-1] == {"c": "display", "valor": 7}
    c.identificar("AA:02")                                   # sem numero cadastrado
    assert esp.de_tipo("display")[-1]["valor"] == "--"
    c.identificar("ZZ:99")                                   # desconhecido (sem wifi: decide na hora)
    assert esp.de_tipo("display")[-1] == {"c": "display", "valor": "E", "segundos": 3}
    c.sair()
    assert esp.de_tipo("display")[-1]["valor"] == "--"
