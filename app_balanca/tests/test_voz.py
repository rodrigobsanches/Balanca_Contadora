"""Testes da voz (frases gravadas), sem tocar som de verdade."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voz import FRASES, PASTA_AUDIOS, Voz, arquivo_da_frase  # noqa: E402


def test_todas_as_frases_tem_audio_gravado():
    faltando = [c for c in FRASES if not os.path.exists(arquivo_da_frase(c, PASTA_AUDIOS))]
    assert faltando == [], "rode: python scripts/gerar_audios.py"


def test_voz_desligada_fica_em_silencio():
    tocados = []
    assert not Voz({"voz": False}, tocar=tocados.append).falar("bem_vindo")
    assert tocados == []


def test_voz_toca_e_nao_repete_em_seguida():
    agora, tocados = [100.0], []
    v = Voz({"voz": True}, tocar=tocados.append, segundos=lambda: agora[0])
    assert v.falar("aproxime")
    agora[0] += 5
    assert not v.falar("aproxime")        # "aproxime" so a cada 15 s
    agora[0] += 15
    assert v.falar("aproxime")
    assert not v.falar("frase_que_nao_existe")
    assert [os.path.basename(t) for t in tocados] == ["aproxime.wav", "aproxime.wav"]


def test_falha_no_som_nao_quebra(tmp_path):
    (tmp_path / "bem_vindo.wav").write_bytes(b"x")

    def sem_placa(arquivo):
        raise RuntimeError("sem dispositivo de som")
    assert not Voz({"voz": True}, pasta=str(tmp_path), tocar=sem_placa).falar("bem_vindo")
