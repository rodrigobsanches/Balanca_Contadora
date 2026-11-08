import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contagem import (avisos_de_precisao, conferir, contar_pecas,  # noqa: E402
                      peso_unitario_por_amostra)


def test_contagem_exata():
    r = contar_pecas(1040, 10.4)
    assert r.quantidade == 100
    assert not r.incerta


def test_contagem_com_tara():
    r = contar_pecas(1140, 10.4, tara_g=100)
    assert r.quantidade == 100


def test_contagem_incerta_quando_sobra_meia_peca():
    r = contar_pecas(105, 10)   # 10,5 pecas
    assert r.incerta


def test_prato_vazio():
    r = contar_pecas(0, 10)
    assert r.quantidade == 0
    assert not r.incerta


def test_peso_unitario_invalido():
    with pytest.raises(ValueError):
        contar_pecas(100, 0)


def test_amostra():
    assert peso_unitario_por_amostra(104, 10) == pytest.approx(10.4)


def test_amostra_invalida():
    with pytest.raises(ValueError):
        peso_unitario_por_amostra(100, 0)


def test_avisos_de_precisao():
    assert avisos_de_precisao(20, 2) == []
    assert len(avisos_de_precisao(4, 2)) == 1
    assert len(avisos_de_precisao(20, 2, peso_amostra_g=30)) == 1


def test_conferencia():
    assert conferir(10, 10).resultado == "OK"
    falta = conferir(8, 10)
    assert falta.resultado == "FALTA" and falta.diferenca == -2
    assert falta.mensagem == "Faltam 2 peças."
    sobra = conferir(11, 10)
    assert sobra.resultado == "SOBRA" and sobra.mensagem == "Sobra 1 peça."
