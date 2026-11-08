# teste_sinalizacao.py - mostra cada padrao de LED (e do buzzer, se houver) por alguns segundos
import time
import config
from sinalizacao import Sinalizacao

s = Sinalizacao(config.PINO_RGB, config.PINO_LED_VERDE, config.PINO_LED_AZUL,
                config.PINO_BUZZER, config.BUZZER_PASSIVO)

for estado in ("aguardando", "ok", "erro", "atencao", "ocioso"):
    print("Estado:", estado)
    s.definir(estado)
    fim = time.ticks_add(time.ticks_ms(), 3500)
    while time.ticks_diff(fim, time.ticks_ms()) > 0:
        s.atualizar()
        time.sleep_ms(10)
print("Fim do teste")
