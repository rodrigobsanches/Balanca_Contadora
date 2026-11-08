# teste_presenca.py - mostra a distancia medida e quando alguem chega ou sai
import time
import config
from presenca import Presenca

p = Presenca(config.PINO_TRIG, config.PINO_ECHO,
             config.DISTANCIA_PERTO_CM, config.DISTANCIA_LONGE_CM,
             config.TEMPO_CHEGOU_MS, config.TEMPO_SAIU_MS)

ultimo_print = 0
while True:
    mudou = p.atualizar()
    if mudou is True:
        print(">>> Alguem chegou")
    elif mudou is False:
        print("<<< Foi embora")
    if time.ticks_diff(time.ticks_ms(), ultimo_print) > 500 and p.ultima_cm is not None:
        print("Distancia: %d cm" % p.ultima_cm)
        ultimo_print = time.ticks_ms()
    time.sleep_ms(10)
