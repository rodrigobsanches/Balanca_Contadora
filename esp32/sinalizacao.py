# sinalizacao.py - LED RGB, LEDs e buzzer (atuadores da ESP32)
# O buzzer e opcional: com pino_buzzer=None, so os LEDs funcionam.
# Os padroes rodam sem travar o programa: chame atualizar() a cada volta do laco.
from machine import Pin, PWM
import neopixel
import time

# Cada padrao e uma lista de passos: (cor_rgb, led_verde, led_azul, buzzer, duracao_ms)
APAGADO = (0, 0, 0)
AZUL = (0, 0, 40)
VERDE = (0, 40, 0)
VERMELHO = (40, 0, 0)
AMARELO = (40, 25, 0)

PADROES = {
    # estado fixo (sem fim): ultimo passo com duracao 0
    "ocioso": [(APAGADO, 0, 0, 0, 0)],
    "aguardando": [(AZUL, 0, 1, 0, 0)],
    # estados temporarios: depois voltam para "aguardando"
    "ok": [(VERDE, 1, 0, 1, 120), (VERDE, 1, 0, 0, 1880)],
    "erro": [(VERMELHO, 0, 0, 1, 400), (VERMELHO, 0, 0, 0, 200),
             (VERMELHO, 0, 0, 1, 400), (VERMELHO, 0, 0, 0, 200),
             (VERMELHO, 0, 0, 1, 400), (VERMELHO, 0, 0, 0, 1400)],
    "atencao": [(AMARELO, 0, 0, 1, 100), (AMARELO, 0, 0, 0, 100),
                (AMARELO, 0, 0, 1, 100), (AMARELO, 0, 0, 0, 1700)],
}
ESTADOS_FIXOS = ("ocioso", "aguardando")


class Sinalizacao:
    def __init__(self, pino_rgb, pino_verde, pino_azul, pino_buzzer=None,
                 buzzer_passivo=False, frequencia_hz=2500):
        self.rgb = neopixel.NeoPixel(Pin(pino_rgb), 1)
        self.verde = Pin(pino_verde, Pin.OUT, value=0)
        self.azul = Pin(pino_azul, Pin.OUT, value=0)
        self.passivo = buzzer_passivo
        if pino_buzzer is None:
            self.buzzer = None
        elif buzzer_passivo:
            self.buzzer = PWM(Pin(pino_buzzer), freq=frequencia_hz, duty_u16=0)
        else:
            self.buzzer = Pin(pino_buzzer, Pin.OUT, value=0)
        self.estado_base = "ocioso"
        self._passos = []
        self._indice = 0
        self._inicio_passo = 0
        self.definir("ocioso")

    def _som(self, ligado):
        if self.buzzer is None:
            return
        if self.passivo:
            self.buzzer.duty_u16(32768 if ligado else 0)
        else:
            self.buzzer.value(1 if ligado else 0)

    def _aplicar(self, passo):
        cor, verde, azul, som, _ = passo
        self.rgb[0] = cor
        self.rgb.write()
        self.verde.value(verde)
        self.azul.value(azul)
        self._som(som)

    def definir(self, estado):
        """Muda o estado: ocioso, aguardando, ok, erro ou atencao."""
        if estado not in PADROES:
            return False
        if estado in ESTADOS_FIXOS:
            self.estado_base = estado
        self._passos = PADROES[estado]
        self._indice = 0
        self._inicio_passo = time.ticks_ms()
        self._aplicar(self._passos[0])
        return True

    def atualizar(self):
        """Avanca o padrao atual. Chamar em toda volta do laco principal."""
        passo = self._passos[self._indice]
        duracao = passo[4]
        if duracao == 0:
            return
        if time.ticks_diff(time.ticks_ms(), self._inicio_passo) >= duracao:
            self._indice += 1
            if self._indice >= len(self._passos):
                # terminou um padrao temporario: volta ao estado fixo
                self.definir(self.estado_base)
                return
            self._inicio_passo = time.ticks_ms()
            self._aplicar(self._passos[self._indice])
