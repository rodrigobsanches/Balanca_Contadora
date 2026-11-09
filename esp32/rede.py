# rede.py - Wi-Fi que nao trava o programa
# Tenta as redes da lista uma de cada vez. Chame atualizar() a cada volta do laco:
# ela so confere o estado e, se precisar, passa para a proxima rede.
import network
import time


class Rede:
    def __init__(self, redes, tempo_tentativa_s=15):
        self.redes = redes                  # lista de (nome, senha)
        self.tempo_tentativa_ms = tempo_tentativa_s * 1000
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.indice = -1                    # rede que esta sendo tentada
        self.inicio_tentativa = None
        self.conectado = False

    def nome_atual(self):
        if 0 <= self.indice < len(self.redes):
            return self.redes[self.indice][0]
        return None

    def rssi(self):
        """Forca do sinal em dBm (ex.: -60 e bom, -85 e fraco). None se desconectado."""
        try:
            return self.wlan.status("rssi") if self.conectado else None
        except Exception:
            return None

    def _tentar_proxima(self):
        if not self.redes:
            return
        self.indice = (self.indice + 1) % len(self.redes)
        nome, senha = self.redes[self.indice]
        try:
            self.wlan.disconnect()
        except Exception:
            pass
        self.wlan.connect(nome, senha)
        self.inicio_tentativa = time.ticks_ms()

    def atualizar(self):
        """Devolve True quando acabou de conectar, False quando acabou de cair,
        ou None quando nada mudou."""
        agora_conectado = self.wlan.isconnected()
        if agora_conectado != self.conectado:
            self.conectado = agora_conectado
            if agora_conectado:
                self.inicio_tentativa = None
            return agora_conectado

        if not agora_conectado:
            if self.inicio_tentativa is None:
                self._tentar_proxima()
            elif time.ticks_diff(time.ticks_ms(), self.inicio_tentativa) > self.tempo_tentativa_ms:
                self._tentar_proxima()
        return None
