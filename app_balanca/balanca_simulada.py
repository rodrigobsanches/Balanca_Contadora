"""Balanca simulada: o peso e definido pelo app (ex.: controle deslizante na tela).

Imita o comportamento de uma balanca real: o peso so e considerado estavel
depois de ficar parado por um tempo.
"""
import time

from balanca_base import Balanca


class BalancaSimulada(Balanca):
    nome = "simulada"

    def __init__(self, divisao=1, tempo_estavel_s=0.7):
        self._divisao = divisao
        self._tempo_estavel_s = tempo_estavel_s
        self._peso_bruto = 0.0
        self._tara = 0.0
        self._mudou_em = time.monotonic()

    def conectar(self):
        return True

    def desconectar(self):
        pass

    def definir_peso(self, gramas):
        """Usado pela tela de simulacao para colocar peso no prato."""
        if gramas != self._peso_bruto:
            self._peso_bruto = float(gramas)
            self._mudou_em = time.monotonic()

    def peso_estavel_g(self):
        if time.monotonic() - self._mudou_em < self._tempo_estavel_s:
            return None
        liquido = self._peso_bruto - self._tara
        return round(liquido / self._divisao) * self._divisao

    def tarar(self):
        self._tara = self._peso_bruto
        return True

    def zerar(self):
        self._tara = 0.0
        return True

    def divisao_g(self):
        return self._divisao
