# serial_app.py - le os comandos JSON que o app da balanca manda pela serial (USB)
# Le um caractere por vez, so quando ha algo para ler: o laco principal nunca trava.
# No Thonny, tudo o que voce digita no Shell com o programa rodando chega aqui.
import json
import select
import sys

TAMANHO_MAXIMO = 4096  # uma linha maior que isso e descartada (protege a memoria)


class SerialApp:
    def __init__(self):
        self._poll = select.poll()
        self._poll.register(sys.stdin, select.POLLIN)
        self._buffer = []
        self._tamanho = 0

    def ler_comando(self):
        """Devolve um comando (dict) quando uma linha JSON completa chega,
        ou None se ainda nao chegou nada completo."""
        while self._poll.poll(0):
            c = sys.stdin.read(1)
            if not c:
                break
            if c in "\r\n":
                if self._buffer:
                    linha = "".join(self._buffer)
                    self._buffer = []
                    self._tamanho = 0
                    return interpretar(linha)
                continue
            if self._tamanho < TAMANHO_MAXIMO:
                self._buffer.append(c)
                self._tamanho += 1
        return None


def interpretar(linha):
    """Transforma uma linha em comando. Linhas que nao sao JSON com campo "c"
    viram {"c": "invalido"}, para o main responder com um log."""
    try:
        comando = json.loads(linha)
    except ValueError:
        return {"c": "invalido", "linha": linha[:80]}
    if not isinstance(comando, dict) or "c" not in comando:
        return {"c": "invalido", "linha": linha[:80]}
    return comando


def enviar(evento):
    """Manda um evento para o app: um JSON por linha."""
    print(json.dumps(evento))
