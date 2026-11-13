# display7.py - dois displays de 7 segmentos (0 a 99) ligados direto na ESP32
# Cada segmento (a..g) vai num pino, com um resistor de 100 Ohm. Sem multiplexacao:
# os dois digitos ficam acesos o tempo todo e o laco principal nao precisa fazer nada.
#
#   aaa
#  f   b        catodo comum: comum no GND, segmento acende com o pino em 1
#   ggg         anodo comum : comum no 3V3, segmento acende com o pino em 0
#  e   c
#   ddd
import time

SEGMENTOS = "abcdefg"

# quais segmentos acendem para cada caractere
CARACTERES = {
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
    "-": "g", "E": "adefg", " ": "",
}


def texto_para_dois(valor):
    """Transforma o que o app mandou em 2 caracteres para os displays.
    12 -> '12', 7 -> ' 7', '--' -> '--', 'E' -> ' E'; fora de 0..99 -> '--'."""
    if isinstance(valor, int) and not isinstance(valor, bool):
        return "%2d" % valor if 0 <= valor <= 99 else "--"
    texto = str(valor).upper()[-2:]
    texto = ("  " + texto)[-2:]
    return "".join(c if c in CARACTERES else "-" for c in texto)


class Digito:
    def __init__(self, pinos, catodo, criar_pino):
        # pinos: {"a": gpio, ..., "g": gpio}; criar_pino(numero) -> objeto com .value(v)
        self.catodo = catodo
        self.pinos = {s: criar_pino(pinos[s]) for s in SEGMENTOS}
        self.mostrar(" ")

    def mostrar(self, caractere):
        acesos = CARACTERES.get(caractere, CARACTERES["-"])
        for s, pino in self.pinos.items():
            ligado = s in acesos
            pino.value(1 if ligado == self.catodo else 0)


class Display2Digitos:
    """mostrar(12) / mostrar('--') / mostrar_por(' E', 3000) e atualizar() no laco."""

    def __init__(self, dezena, unidade):
        self.dezena = dezena
        self.unidade = unidade
        self.base = "--"           # o que volta a aparecer depois de uma mensagem temporaria
        self._volta_em = None
        self._escrever(self.base)

    def _escrever(self, dois):
        if self.dezena:
            self.dezena.mostrar(dois[0])
        if self.unidade:
            self.unidade.mostrar(dois[1])

    def mostrar(self, valor):
        self.base = texto_para_dois(valor)
        self._volta_em = None
        self._escrever(self.base)

    def mostrar_por(self, valor, ms):
        """Mostra algo por um tempo (ex.: 'E' de chaveiro desconhecido) e depois volta."""
        self._escrever(texto_para_dois(valor))
        self._volta_em = time.ticks_add(time.ticks_ms(), int(ms))

    def atualizar(self):
        if self._volta_em is not None and time.ticks_diff(time.ticks_ms(), self._volta_em) >= 0:
            self._volta_em = None
            self._escrever(self.base)


def criar_display(config):
    """Monta o display a partir do config.py. Devolve None se nao houver display configurado."""
    from machine import Pin

    def criar_pino(numero):
        return Pin(numero, Pin.OUT)

    def digito(nome):
        pinos = getattr(config, "DISPLAY_%s_PINOS" % nome, None)
        if not pinos:
            return None
        return Digito(pinos, getattr(config, "DISPLAY_%s_CATODO" % nome, True), criar_pino)

    dezena, unidade = digito("DEZENA"), digito("UNIDADE")
    if not dezena and not unidade:
        return None
    return Display2Digitos(dezena, unidade)
