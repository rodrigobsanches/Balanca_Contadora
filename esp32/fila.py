# fila.py - fila offline em arquivo (uma operacao JSON por linha)
# Quando o Wi-Fi ou o Firebase falham, a operacao fica guardada aqui e e
# reenviada depois. Fica na memoria flash: sobrevive se a placa desligar.
# So a primeira linha e lida por vez, para gastar pouca memoria RAM.
import json
import os


class Fila:
    def __init__(self, arquivo="fila.jsonl", limite=500):
        self.arquivo = arquivo
        self.limite = limite
        self.tamanho = self._contar()

    def _contar(self):
        n = 0
        try:
            with open(self.arquivo) as f:
                for linha in f:
                    if linha.strip():
                        n += 1
        except OSError:
            pass  # arquivo ainda nao existe
        return n

    def adicionar(self, operacao):
        """Guarda a operacao no fim da fila. Devolve False se a fila estiver cheia."""
        if self.tamanho >= self.limite:
            return False
        with open(self.arquivo, "a") as f:
            f.write(json.dumps(operacao) + "\n")
        self.tamanho += 1
        return True

    def primeira(self):
        """Devolve a primeira operacao (sem remover) ou None se a fila estiver vazia."""
        if self.tamanho == 0:
            return None
        try:
            with open(self.arquivo) as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha:
                        continue
                    try:
                        return json.loads(linha)
                    except ValueError:
                        # linha estragada (ex.: placa desligou no meio da gravacao)
                        return {"estragada": True}
        except OSError:
            pass
        self.tamanho = 0
        return None

    def remover_primeira(self):
        """Apaga a primeira linha, copiando o resto para um arquivo novo."""
        temporario = self.arquivo + ".tmp"
        pulou = False
        restantes = 0
        try:
            with open(self.arquivo) as origem, open(temporario, "w") as destino:
                for linha in origem:
                    if not linha.strip():
                        continue
                    if not pulou:
                        pulou = True
                        continue
                    destino.write(linha)
                    restantes += 1
        except OSError:
            self.tamanho = 0
            return
        os.remove(self.arquivo)
        os.rename(temporario, self.arquivo)
        self.tamanho = restantes
