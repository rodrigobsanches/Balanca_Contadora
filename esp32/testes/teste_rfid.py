# teste_rfid.py - le os chaveiros e mostra o UID (anote o UID de cada chaveiro)
from machine import Pin, I2C
import time
import config
from pn532 import PN532

i2c = I2C(0, sda=Pin(config.PINO_SDA), scl=Pin(config.PINO_SCL), freq=100000)
print("Dispositivos I2C:", [hex(e) for e in i2c.scan()], "(o PN532 e o 0x24)")
time.sleep_ms(500)

leitor = PN532(i2c)
v = leitor.versao()
if not v:
    raise SystemExit("PN532 nao respondeu. Confira fios e chavinhas (1 ON, 2 OFF).")
print("PN532 pronto. Firmware %d.%d" % (v[1], v[2]))
leitor.configurar()

print("Aproxime um chaveiro...")
ultimo = None
while True:
    uid = leitor.ler_uid(timeout_ms=500)
    if uid and uid != ultimo:
        print("Chaveiro:", uid)
    ultimo = uid
    time.sleep_ms(100)
