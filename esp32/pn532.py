# pn532.py - driver minimo do leitor RFID/NFC PN532 via I2C (MicroPython)
# Chaves do modulo em modo I2C: chave 1 = ON, chave 2 = OFF. Endereco 0x24.
# Versao inicial, ainda sem teste em placa: ajustar se necessario.
import time

ENDERECO = 0x24
ACK = b"\x00\x00\xff\x00\xff\x00"


class PN532:
    def __init__(self, i2c):
        self.i2c = i2c

    def _pronto(self, timeout_ms):
        inicio = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), inicio) < timeout_ms:
            try:
                if self.i2c.readfrom(ENDERECO, 1)[0] == 0x01:
                    return True
            except OSError:
                pass
            time.sleep_ms(5)
        return False

    def _enviar(self, cmd, params=b""):
        dados = bytes([0xD4, cmd]) + bytes(params)
        tam = len(dados)
        quadro = (bytes([0x00, 0x00, 0xFF, tam, (~tam + 1) & 0xFF])
                  + dados
                  + bytes([(~sum(dados) + 1) & 0xFF, 0x00]))
        self.i2c.writeto(ENDERECO, quadro)
        if not self._pronto(100):
            raise OSError("PN532 nao confirmou o comando")
        if self.i2c.readfrom(ENDERECO, 7)[1:] != ACK:
            raise OSError("Resposta inesperada do PN532")

    def _receber(self, cmd, tamanho, timeout_ms):
        if not self._pronto(timeout_ms):
            return None
        bruto = self.i2c.readfrom(ENDERECO, tamanho + 1)[1:]
        for i in range(len(bruto) - 1):
            if bruto[i] == 0x00 and bruto[i + 1] == 0xFF:
                n = bruto[i + 2]
                corpo = bruto[i + 4:i + 4 + n]
                if len(corpo) >= 2 and corpo[0] == 0xD5 and corpo[1] == cmd + 1:
                    return corpo[2:]
                return None
        return None

    def comando(self, cmd, params=b"", tamanho=32, timeout_ms=500):
        self._enviar(cmd, params)
        return self._receber(cmd, tamanho, timeout_ms)

    def versao(self):
        """Devolve (ic, versao, revisao, suporte) ou None se o leitor nao responder."""
        for _ in range(3):
            try:
                r = self.comando(0x02, tamanho=14)
                if r:
                    return r
            except OSError:
                time.sleep_ms(200)
        return None

    def configurar(self):
        """Modo normal de leitura (SAMConfiguration)."""
        self.comando(0x14, b"\x01\x14\x01", tamanho=10)

    def ler_uid(self, timeout_ms=100):
        """Procura um chaveiro por ate timeout_ms. Devolve o UID em texto ou None.
        Use timeout curto no laco principal para nao travar o resto do programa."""
        try:
            r = self.comando(0x4A, b"\x01\x00", tamanho=26, timeout_ms=timeout_ms)
        except OSError:
            return None
        if not r or r[0] != 1:
            return None
        n = r[5]
        return ":".join("%02X" % b for b in r[6:6 + n])
