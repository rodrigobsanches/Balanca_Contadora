"""Testes do dashboard sem Firebase: login, transformacoes e a tela de entrada."""
import os
import sys

import pandas as pd

PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PASTA)

from autenticacao import autenticar, conferir_senha, gerar_hash  # noqa: E402
import transformacoes as tr  # noqa: E402


# ---------------- login ----------------
def test_hash_confere_so_com_a_senha_certa():
    h = gerar_hash("senha-forte-123")
    assert h.startswith("pbkdf2_sha256$")
    assert "senha-forte-123" not in h
    assert conferir_senha("senha-forte-123", h)
    assert not conferir_senha("senha-errada", h)
    assert not conferir_senha("qualquer", "lixo")
    assert gerar_hash("x") != gerar_hash("x")          # sal diferente a cada vez


def test_autenticar_devolve_o_perfil():
    usuarios = {"rodrigo": {"perfil": "admin", "senha": gerar_hash("abc12345")},
                "ana": {"perfil": "estranho", "senha": gerar_hash("zzz12345")}}
    assert autenticar(usuarios, " Rodrigo ", "abc12345") == "admin"
    assert autenticar(usuarios, "rodrigo", "errada") is None
    assert autenticar(usuarios, "ninguem", "abc12345") is None
    assert autenticar(usuarios, "ana", "zzz12345") == "leitura"   # perfil invalido vira leitura
    assert autenticar({}, "rodrigo", "abc12345") is None


def test_tela_de_login_bloqueia_sem_credencial():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(os.path.join(PASTA, "app.py"))
    at.secrets["usuarios"] = {"rodrigo": {"perfil": "admin", "senha": gerar_hash("abc12345")}}
    at.run(timeout=30)
    assert at.title[0].value == "Balança Contadora de Peças"
    at.text_input[0].input("rodrigo")
    at.text_input[1].input("errada")
    at.button[0].click()
    at.run(timeout=30)
    assert at.error and "incorretos" in at.error[0].value
    assert "perfil" not in at.session_state


# ---------------- transformacoes ----------------
REGISTROS = {
    # "a" = 13:33 em Sao Paulo, depois do "b" (12:00)
    "a": {"id": "a", "ts_servidor": 1762706000000, "operador_nome": "Rodrigo", "modo": "inventario",
          "produto": "P001", "produto_nome": "Parafuso", "quantidade": 100, "resultado": "OK"},
    "b": {"id": "b", "ts_balanca": "2025-11-09T12:00:00", "ts_servidor": {".sv": "timestamp"},
          "operador_nome": "Ana", "modo": "conferencia", "produto": "P002", "pedido_id": "PED001",
          "quantidade": 8, "quantidade_esperada": 10, "resultado": "FALTA", "diferenca": -2},
}


def test_contagens_df():
    df = tr.contagens_df(REGISTROS)
    assert list(df["id"]) == ["a", "b"]                 # mais recente primeiro
    assert str(df["quando"].dt.tz) == tr.FUSO
    assert df.loc[df["id"] == "b", "modo"].item() == "Conferência"
    assert len(tr.divergencias(df)) == 1
    assert tr.contagens_df({}).empty


def test_estoque_e_pedidos():
    df = tr.estoque_df({"P1": {"nome": "A", "estoque_atual": 5, "estoque_minimo": 10},
                        "P2": {"nome": "B", "estoque_atual": 50, "estoque_minimo": 10}})
    assert df.iloc[0]["situacao"] == "Abaixo do mínimo"
    assert list(tr.pedidos_pendentes({"X": {"status": "pendente"},
                                      "Y": {"status": "conferido"}})) == ["X"]
    assert tr.proximo_id_pedido({"PED001": {}, "PED007": {}, "OUTRO": {}}) == "PED008"
    assert tr.proximo_id_pedido({}) == "PED001"


def test_status_esp32():
    agora = 1_000_000.0
    assert tr.status_esp32({"ultimo_contato": (agora - 30) * 1000, "fila": 2}, agora)["online"]
    assert not tr.status_esp32({"ultimo_contato": (agora - 600) * 1000}, agora)["online"]
    assert tr.status_esp32({}, agora)["segundos"] is None


def test_chave_valida_e_excel():
    assert tr.chave_valida("P001") and tr.chave_valida("36:BD:9A:AC")
    assert not tr.chave_valida("P.01") and not tr.chave_valida("") and not tr.chave_valida("a/b")
    dados = tr.para_excel(tr.contagens_df(REGISTROS))
    assert dados[:2] == b"PK"                           # .xlsx e um zip
    assert isinstance(pd.read_excel(__import__("io").BytesIO(dados)), pd.DataFrame)


def test_contagens_por_dia_tem_sempre_7_dias():
    df = tr.contagens_df(REGISTROS)
    tabela = tr.contagens_por_dia(df, df["quando"].max().date())
    assert len(tabela) == 7 and list(tabela.columns) == tr.RESULTADOS
    assert tabela.values.sum() == 2
