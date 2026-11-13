"""Gera os arquivos WAV da voz da balanca (app_balanca/audios/<chave>.wav).

Rodar num PC Windows que tenha uma voz em portugues (ex.: "Microsoft Maria"):
    python scripts/gerar_audios.py

As frases ficam em app_balanca/voz.py (FRASES). Usa a voz do Windows (SAPI) pelo pywin32.
Nao vai para a balanca: so os WAVs gerados vao.
"""
import os
import sys

PASTA_APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_balanca")
sys.path.insert(0, PASTA_APP)

from voz import FRASES, PASTA_AUDIOS, arquivo_da_frase  # noqa: E402

FORMATO_22KHZ_16BIT_MONO = 22   # SpeechAudioFormatType SAFT22kHz16BitMono
CRIAR_PARA_ESCREVER = 3         # SpeechStreamFileMode SSFMCreateForWrite
IDIOMA_PT_BR = "416"            # codigo do idioma pt-BR na SAPI (hexadecimal de 1046)


def escolher_voz_pt_br(voz):
    vozes = voz.GetVoices("Language=%s" % IDIOMA_PT_BR)
    if vozes.Count == 0:
        nomes = [voz.GetVoices().Item(i).GetDescription() for i in range(voz.GetVoices().Count)]
        sys.exit("Nenhuma voz em portugues neste PC. Vozes instaladas: %s" % ", ".join(nomes))
    return vozes.Item(0)


def main():
    import win32com.client

    voz = win32com.client.Dispatch("SAPI.SpVoice")
    voz.Voice = escolher_voz_pt_br(voz)
    print("Voz:", voz.Voice.GetDescription())
    os.makedirs(PASTA_AUDIOS, exist_ok=True)
    for chave, frase in FRASES.items():
        arquivo = arquivo_da_frase(chave)
        saida = win32com.client.Dispatch("SAPI.SpFileStream")
        saida.Format.Type = FORMATO_22KHZ_16BIT_MONO
        saida.Open(arquivo, CRIAR_PARA_ESCREVER)
        voz.AudioOutputStream = saida
        voz.Speak(frase)
        saida.Close()
        print("  %-22s %s" % (os.path.basename(arquivo), frase))
    print("Pronto: %d arquivos em %s" % (len(FRASES), PASTA_AUDIOS))


if __name__ == "__main__":
    main()
