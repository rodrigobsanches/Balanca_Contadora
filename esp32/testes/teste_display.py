# teste_display.py - testa os dois displays de 7 segmentos
# 1) acende um segmento por vez em cada digito (a, b, c, d, e, f, g) - confira a ligacao
# 2) conta de 00 a 99
# 3) mostra "--" e " E"
import time
import config
from display7 import criar_display, SEGMENTOS

d = criar_display(config)
if d is None:
    raise SystemExit("Sem display no config.py (DISPLAY_DEZENA_PINOS / DISPLAY_UNIDADE_PINOS)")

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
