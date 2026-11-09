"""Ligacao com a ESP32 pelo cabo USB (porta serial), em segundo plano.

- Encontra a porta sozinha (config "porta_esp32": "auto") ou usa a porta informada.
- Le uma mensagem JSON por linha e entrega cada evento para quem pediu (callback).
- Ignora linhas que nao sao JSON (ex.: mensagens de boot do MicroPython).
- Se o cabo sair ou a porta falhar, tenta reconectar a cada poucos segundos.

Protocolo: docs/protocolo_serial.md
"""
import json
import threading
import time

import serial
from serial.tools import list_ports

VELOCIDADE = 115200
ESPERA_RECONEXAO_S = 2.0

# Fabricantes (VID) dos chips USB das placas ESP32-S3:
#   0x303A = USB nativa da Espressif (sem driver)
#   0x1A86 = chip CH343 da porta COM/UART (precisa de driver)
VIDS_ESP32 = (0x303A, 0x1A86)


def escolher_porta(portas, porta_config="auto"):
    """Escolhe a porta da ESP32 numa lista de portas do pyserial.
    Prefere a USB nativa (0x303A). Devolve o nome (ex.: 'COM5') ou None."""
    if porta_config and porta_config != "auto":
        return porta_config
    candidatas = [p for p in portas if p.vid in VIDS_ESP32]
    candidatas.sort(key=lambda p: VIDS_ESP32.index(p.vid))
    return candidatas[0].device if candidatas else None


def interpretar_linha(linha):
    """Transforma uma linha recebida em evento (dict) ou None se nao for evento."""
    linha = linha.strip()
    if not linha.startswith("{"):
        return None
    try:
        evento = json.loads(linha)
    except ValueError:
        return None
    if isinstance(evento, dict) and "t" in evento:
        return evento
    return None


class LigacaoESP32:
    """Roda numa thread. Use iniciar(), enviar(comando) e parar().

    ao_evento(evento: dict)    -> chamado para cada evento da ESP32
    ao_conexao(conectado: bool, porta: str|None) -> chamado quando conecta/desconecta
    Atencao: os callbacks rodam na thread da serial, nao na thread da tela.
    """

    def __init__(self, ao_evento, ao_conexao=None, porta_config="auto", ao_texto=None):
        self.ao_evento = ao_evento
        self.ao_conexao = ao_conexao or (lambda conectado, porta: None)
        # ao_texto(linha): linhas que NAO sao eventos (boot, ">>>", erros). Util para depurar.
        self.ao_texto = ao_texto or (lambda linha: None)
        self.porta_config = porta_config
        self.porta = None
        self._serial = None
        self._trava_escrita = threading.Lock()
        self._rodando = False
        self._thread = None

    @property
    def conectado(self):
        return self._serial is not None

    def iniciar(self):
        self._rodando = True
        self._thread = threading.Thread(target=self._laco, name="esp32-serial", daemon=True)
        self._thread.start()

    def parar(self):
        self._rodando = False
        self._fechar()
        if self._thread:
            self._thread.join(timeout=3)

    def enviar(self, comando):
        """Manda um comando (dict) para a ESP32. Devolve False se nao estiver conectada."""
        s = self._serial
        if s is None:
            return False
        dados = (json.dumps(comando, ensure_ascii=False) + "\n").encode("utf-8")
        try:
            with self._trava_escrita:
                s.write(dados)
            return True
        except (serial.SerialException, OSError):
            self._fechar()
            return False

    def reiniciar_programa(self):
        """Faz a ESP32 (re)comecar o main.py: Ctrl+C interrompe o que estiver rodando
        e Ctrl+D faz o 'soft reboot', que roda o main.py de novo.
        Serve para quando a placa ficou parada no prompt >>> (ex.: depois do Thonny)."""
        s = self._serial
        if s is None:
            return False
        try:
            with self._trava_escrita:
                s.write(b"\r\x03\x03")
                time.sleep(0.2)
                s.write(b"\x04")
            return True
        except (serial.SerialException, OSError):
            self._fechar()
            return False

    # ---------- parte interna (thread) ----------
    def _abrir(self):
        porta = escolher_porta(list_ports.comports(), self.porta_config)
        if not porta:
            return False
        s = serial.Serial()
        s.port = porta
        s.baudrate = VELOCIDADE
        s.timeout = 0.2
        # DTR/RTS desligados: evita reiniciar a placa ao abrir a porta
        s.dtr = False
        s.rts = False
        s.open()
        self._serial = s
        self.porta = porta
        self.ao_conexao(True, porta)
        return True

    def _fechar(self):
        s = self._serial
        if s is None:
            return
        self._serial = None
        try:
            s.close()
        except Exception:
            pass
        self.ao_conexao(False, self.porta)

    def _laco(self):
        while self._rodando:
            if self._serial is None:
                try:
                    if not self._abrir():
                        time.sleep(ESPERA_RECONEXAO_S)
                        continue
                except (serial.SerialException, OSError):
                    time.sleep(ESPERA_RECONEXAO_S)
                    continue
            try:
                bruto = self._serial.readline()
            except (serial.SerialException, OSError, AttributeError):
                self._fechar()
                continue
            if not bruto:
                continue
            texto = bruto.decode("utf-8", errors="replace")
            evento = interpretar_linha(texto)
            if evento is None:
                if texto.strip():
                    self.ao_texto(texto.rstrip())
            else:
                try:
                    self.ao_evento(evento)
                except Exception as erro:  # um erro no app nao pode matar a leitura
                    print("Erro ao tratar evento da ESP32:", erro)
