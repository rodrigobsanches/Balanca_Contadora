"""Testes no PC (pytest) das partes do firmware que nao dependem do hardware:
fila offline, leitura de comandos da serial e validacao de caminhos do Firebase.

Rodar:  pytest esp32/tests_pc
"""
import os
import sys
import types

PASTA_ESP32 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PASTA_ESP32)

# O firebase.py importa "requests" (existe na ESP32). Se o PC nao tiver, um modulo vazio basta.
# (Nao substituir o requests de verdade: o Streamlit e o firebase-admin usam ele.)
try:
    import requests  # noqa: F401
except ImportError:
    sys.modules["requests"] = types.ModuleType("requests")

from fila import Fila  # noqa: E402
from firebase import caminho_valido  # noqa: E402
from serial_app import interpretar  # noqa: E402


def test_fila_guarda_e_remove_em_ordem(tmp_path):
    fila = Fila(str(tmp_path / "fila.jsonl"))
    assert fila.tamanho == 0
    assert fila.primeira() is None
    fila.adicionar({"id": "a"})
    fila.adicionar({"id": "b"})
    assert fila.tamanho == 2
    assert fila.primeira() == {"id": "a"}
    fila.remover_primeira()
    assert fila.tamanho == 1
    assert fila.primeira() == {"id": "b"}
    fila.remover_primeira()
    assert fila.tamanho == 0
    assert fila.primeira() is None


def test_fila_sobrevive_ao_reinicio(tmp_path):
    arquivo = str(tmp_path / "fila.jsonl")
    Fila(arquivo).adicionar({"id": "x"})
    assert Fila(arquivo).tamanho == 1  # "placa reiniciou": a fila continua la


def test_fila_respeita_limite(tmp_path):
    fila = Fila(str(tmp_path / "fila.jsonl"), limite=2)
    assert fila.adicionar({"id": 1})
    assert fila.adicionar({"id": 2})
    assert not fila.adicionar({"id": 3})
    assert fila.tamanho == 2


def test_fila_linha_estragada(tmp_path):
    arquivo = tmp_path / "fila.jsonl"
    arquivo.write_text('{"id": "a"\n{"id": "b"}\n')  # 1a linha cortada no meio
    fila = Fila(str(arquivo))
    assert fila.primeira() == {"estragada": True}
    fila.remover_primeira()
    assert fila.primeira() == {"id": "b"}


def test_interpretar_comandos():
    assert interpretar('{"c":"ping"}') == {"c": "ping"}
    assert interpretar("MPY: soft reboot")["c"] == "invalido"
    assert interpretar('{"t":"hello"}')["c"] == "invalido"  # sem campo "c"
    assert interpretar("[1, 2]")["c"] == "invalido"


def test_caminhos_do_firebase():
    assert caminho_valido("contagens/6f1c-uuid")
    assert caminho_valido("produtos/P001")
    assert caminho_valido("rfid_desconhecidos/36:BD:9A:AC")
    assert caminho_valido("dispositivos/esp32-01")
    assert not caminho_valido("")
    assert not caminho_valido("/contagens/x")
    assert not caminho_valido("contagens/../x")
    assert not caminho_valido("outra_pasta/x")
    assert not caminho_valido("contagens/x.json?auth=1")
    assert not caminho_valido(None)
