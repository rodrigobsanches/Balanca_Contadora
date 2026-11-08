# presenca.py - sensor ultrassonico HC-SR04 como detector de presenca
# ATENCAO: o HC-SR04 e alimentado em 5 V e o pino ECHO devolve 5 V.
# Use divisor de tensao: ECHO -> 1 kOhm -> GPIO; GPIO -> 2 kOhm -> GND.
from machine import Pin, time_pulse_us
import time


class Presenca:
    def __init__(self, pino_trig, pino_echo, perto_cm=60, longe_cm=80,
                 tempo_chegou_ms=1000, tempo_saiu_ms=5000, intervalo_ms=100):
        self.trig = Pin(pino_trig, Pin.OUT, value=0)
        self.echo = Pin(pino_echo, Pin.IN)
        self.perto_cm = perto_cm
        self.longe_cm = longe_cm
        self.tempo_chegou_ms = tempo_chegou_ms
        self.tempo_saiu_ms = tempo_saiu_ms
        self.intervalo_ms = intervalo_ms
        self.alguem_perto = False
        self.ultima_cm = None
        self._leituras = []
        self._ultima_medida = 0
        self._desde = None

    def medir_cm(self):
        """Uma medida em cm, ou None se nada respondeu (fora de alcance)."""
        self.trig.value(0)
        time.sleep_us(2)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)
        duracao = time_pulse_us(self.echo, 1, 30000)  # ate ~5 m
        if duracao < 0:
            return None
        return duracao / 58.0

    def atualizar(self):
        """Chamar no laco principal. Devolve True/False quando o estado muda,
        ou None quando nada mudou."""
        agora = time.ticks_ms()
        if time.ticks_diff(agora, self._ultima_medida) < self.intervalo_ms:
            return None
        self._ultima_medida = agora

        cm = self.medir_cm()
        self._leituras.append(cm if cm is not None else 999)
        if len(self._leituras) > 5:
            self._leituras.pop(0)
        self.ultima_cm = sorted(self._leituras)[len(self._leituras) // 2]  # mediana

        if not self.alguem_perto:
            condicao = self.ultima_cm < self.perto_cm
            espera = self.tempo_chegou_ms
        else:
            condicao = self.ultima_cm > self.longe_cm
            espera = self.tempo_saiu_ms

        if not condicao:
            self._desde = None
            return None
        if self._desde is None:
            self._desde = agora
            return None
        if time.ticks_diff(agora, self._desde) >= espera:
            self.alguem_perto = not self.alguem_perto
            self._desde = None
            return self.alguem_perto
        return None
