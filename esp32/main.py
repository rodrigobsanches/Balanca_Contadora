# main.py - Fase 1: integra os perifericos da ESP32-S3
#   - presenca (HC-SR04) acende o azul quando alguem chega
#   - chaveiro RFID (PN532) gera um evento e um bipe de OK
# Cada evento e impresso como JSON numa linha: e o comeco do protocolo
# com o app da balanca (ver docs/protocolo_serial.md).
# Fases seguintes: leitura de comandos pela serial, Wi-Fi, Firebase e fila offline.
from machine import Pin, I2C
import json
import time

import config
from pn532 import PN532
from presenca import Presenca
from sinalizacao import Sinalizacao

VERSAO_FW = "0.1"


def enviar(evento):
    print(json.dumps(evento))


sinal = Sinalizacao(config.PINO_RGB, config.PINO_LED_VERDE, config.PINO_LED_AZUL,
                    config.PINO_BUZZER, config.BUZZER_PASSIVO)

presenca = Presenca(config.PINO_TRIG, config.PINO_ECHO,
                    config.DISTANCIA_PERTO_CM, config.DISTANCIA_LONGE_CM,
                    config.TEMPO_CHEGOU_MS, config.TEMPO_SAIU_MS)

i2c = I2C(0, sda=Pin(config.PINO_SDA), scl=Pin(config.PINO_SCL), freq=100000)
time.sleep_ms(500)
leitor = PN532(i2c)
if leitor.versao():
    leitor.configurar()
else:
    leitor = None
    enviar({"t": "log", "msg": "PN532 nao respondeu"})
    sinal.definir("atencao")

enviar({"t": "hello", "fw": VERSAO_FW, "id": config.ID_DISPOSITIVO})

ultimo_uid = None
ultimo_uid_ms = 0

while True:
    sinal.atualizar()

    mudou = presenca.atualizar()
    if mudou is not None:
        enviar({"t": "presenca", "perto": mudou, "cm": int(presenca.ultima_cm)})
        sinal.definir("aguardando" if mudou else "ocioso")

    if leitor:
        uid = leitor.ler_uid(timeout_ms=50)
        agora = time.ticks_ms()
        # evita repetir o mesmo chaveiro enquanto ele continua encostado
        if uid and (uid != ultimo_uid or time.ticks_diff(agora, ultimo_uid_ms) > 3000):
            enviar({"t": "rfid", "uid": uid})
            sinal.definir("ok")
            ultimo_uid = uid
        if uid:
            ultimo_uid_ms = agora

    time.sleep_ms(10)
