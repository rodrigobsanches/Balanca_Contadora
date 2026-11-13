"""Voz da balanca: toca frases gravadas (arquivos WAV em audios/).

Por que gravado e nao "texto para fala" na hora: o Windows da balanca so tem vozes em
ingles. Os WAVs sao gerados uma vez, num PC com a voz pt-BR, pelo
scripts/gerar_audios.py, que le as frases daqui (FRASES e a unica fonte das frases).

Liga/desliga: "voz" no config.json. Sem o arquivo, sem placa de som ou fora do Windows,
simplesmente fica em silencio (nunca quebra o app).
"""
import os
import time

import config_app

# chave -> frase falada. Mudou uma frase? Rode de novo: python scripts/gerar_audios.py
FRASES = {
    "aproxime": "Aproxime seu chaveiro",
    "bem_vindo": "Bem-vindo",
    "nao_cadastrado": "Chaveiro não cadastrado",
    "contagem_registrada": "Contagem registrada. Retire tudo da balança",
    "item_conferido": "Item conferido. Retire tudo da balança",
    "divergente": "Quantidade divergente. Retire tudo da balança",
    "pedido_conferido": "Pedido conferido",
    "pedido_divergente": "Pedido com divergência",
    "ate_logo": "Até logo",
}

PASTA_AUDIOS = os.path.join(config_app.PASTA_APP, "audios")
INTERVALO_MESMA_FRASE_S = {"aproxime": 15}   # nao repetir "aproxime" a cada passo na frente
INTERVALO_PADRAO_S = 2


def arquivo_da_frase(chave, pasta=PASTA_AUDIOS):
    return os.path.join(pasta, chave + ".wav")


class Voz:
    def __init__(self, config, pasta=PASTA_AUDIOS, tocar=None, segundos=None):
        self.ligada = bool(config.get("voz", False))
        self.pasta = pasta
        self.tocar = tocar or _tocar_wav
        self.segundos = segundos or time.monotonic
        self._ultima = {}   # chave -> quando tocou

    def falar(self, chave):
        """Toca a frase sem travar a tela. Devolve True se mandou tocar."""
        if not self.ligada or chave not in FRASES:
            return False
        agora = self.segundos()
        intervalo = INTERVALO_MESMA_FRASE_S.get(chave, INTERVALO_PADRAO_S)
        if agora - self._ultima.get(chave, -1e9) < intervalo:
            return False
        arquivo = arquivo_da_frase(chave, self.pasta)
        if not os.path.exists(arquivo):
            print("Voz: falta o arquivo %s (rode scripts/gerar_audios.py)" % arquivo)
            return False
        self._ultima[chave] = agora
        try:
            self.tocar(arquivo)
            return True
        except Exception as erro:   # sem placa de som, por exemplo
            print("Voz: nao consegui tocar %s: %s" % (arquivo, erro))
            return False


def _tocar_wav(arquivo):
    import winsound   # so existe no Windows; a balanca e o PC de desenvolvimento sao Windows
    # ASYNC: nao trava a tela; uma frase nova interrompe a anterior
    winsound.PlaySound(arquivo, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
