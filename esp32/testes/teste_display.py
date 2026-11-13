# teste_display.py - testa os dois displays de 7 segmentos
# 1) acende um segmento por vez em cada digito (a, b, c, d, e, f, g) - confira a ligacao
# 2) conta de 00 a 99
# 3) mostra "--" e " E"
import time
import config
from display7 import criar_display, SEGMENTOS

print("Teste do display iniciado")
d = criar_display(config)
# Obs.: nao usar SystemExit aqui: no MicroPython ele reinicia a placa e a mensagem some.
if d is None:
    print("ERRO: o config.py DA PLACA nao tem DISPLAY_DEZENA_PINOS / DISPLAY_UNIDADE_PINOS.")
    print("Copie o bloco do display do config_exemplo.py para o config.py e envie para a placa.")
    while True:
        time.sleep(1)

for nome, digito in (("dezena", d.dezena), ("unidade", d.unidade)):
    if not digito:
        continue
    for s in SEGMENTOS:
        print("%s: segmento %s" % (nome, s))
        for seg, pino in digito.pinos.items():
            ligado = seg == s
            pino.value(1 if ligado == digito.catodo else 0)
        time.sleep(0.6)
    digito.mostrar(" ")

print("Contando de 00 a 99...")
for n in range(100):
    d.mostrar("%02d" % n)
    time.sleep(0.08)

for valor in ("--", "E"):
    print("Mostrando:", valor)
    d.mostrar(valor)
    time.sleep(1.5)
print("Fim do teste")
