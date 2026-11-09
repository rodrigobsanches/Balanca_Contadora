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

# Controle de envio. A ESP32 so guarda ~256 caracteres recebidos enquanto esta ocupada
# (leitor RFID, sensor e, principalmente, as chamadas HTTPS, que travam 1 a 3 s).
# Uma contagem tem ~650 caracteres: mandada de uma vez, o resto se perde. Por isso:
#   1. cada comando sai em pedacos pequenos, com uma pausa entre eles;
#   2. comandos que fazem a ESP32 usar a internet (enviar, atualizar, sync) vao um por vez:
#      o proximo so sai depois da resposta (ack / sync) ou de um tempo limite.
#   Comandos curtos (sinal, ping...) nao esperam: cabem na entrada da ESP32.
TAMANHO_PEDACO = 64
PAUSA_PEDACO_S = 0.04
TEMPO_LIMITE_RESPOSTA_S = 15.0
COMANDOS_COM_RESPOSTA = ("enviar", "atualizar", "sync")

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


class ControleEnvio:
    """Decide qual comando sai agora (sem threads: facil de testar).

    adicionar(cmd)       -> entra na fila de saida
    proximo(agora)       -> devolve o comando que pode sair agora, ou None
    resposta(evento)     -> avisa que chegou um evento (libera a espera, se for a resposta)
    limpar()             -> esvazia tudo (a ESP32 desconectou)
    """

    def __init__(self, tempo_limite_s=TEMPO_LIMITE_RESPOSTA_S):
        self.tempo_limite_s = tempo_limite_s
        self.fila = []
        self.esperando = None       # ("ack", id) ou ("sync", None)
        self.esperando_desde = 0.0

    def adicionar(self, comando):
        self.fila.append(comando)

    def limpar(self):
        self.fila.clear()
        self.esperando = None

    def proximo(self, agora):
        if self.esperando and agora - self.esperando_desde > self.tempo_limite_s:
            self.esperando = None   # a resposta nao veio: segue (o registro continua pendente)
        for i, cmd in enumerate(self.fila):
            longo = cmd.get("c") in COMANDOS_COM_RESPOSTA
            if longo and self.esperando:
                continue            # espera a resposta do anterior
            del self.fila[i]
            if longo:
                self.esperando = ("sync", None) if cmd["c"] == "sync" else ("ack", cmd.get("id"))
                self.esperando_desde = agora
            return cmd
        return None

    def resposta(self, evento):
        if not self.esperando:
            return
        tipo, id_ = self.esperando
        if tipo == "ack" and evento.get("t") == "ack" and evento.get("id") == id_:
            self.esperando = None
        elif tipo == "sync" and evento.get("t") == "sync":
            self.esperando = None
        elif evento.get("t") == "hello":
            self.esperando = None   # a placa reiniciou: a resposta nunca vai chegar


class LigacaoESP32:
    """Roda em duas threads (leitura e escrita). Use iniciar(), enviar(comando) e parar().

    ao_evento(evento: dict)    -> chamado para cada evento da ESP32
    ao_conexao(conectado: bool, porta: str|None) -> chamado quando conecta/desconecta
    ao_texto(linha: str)       -> linhas que NAO sao eventos (boot, ">>>", erros); para depurar
    Atencao: os callbacks rodam na thread da serial, nao na thread da tela.
    """

    def __init__(self, ao_evento, ao_conexao=None, porta_config="auto", ao_texto=None):
        self.ao_evento = ao_evento
        self.ao_conexao = ao_conexao or (lambda conectado, porta: None)
        self.ao_texto = ao_texto or (lambda linha: None)
        self.porta_config = porta_config
        self.porta = None
        self._serial = None
        self._controle = ControleEnvio()
        self._cond = threading.Condition()     # protege _controle e acorda a escrita
        self._trava_escrita = threading.Lock()  # um so escritor por vez na porta
        self._rodando = False
        self._threads = []

    @property
    def conectado(self):
        return self._serial is not None

    def iniciar(self):
        self._rodando = True
        for alvo, nome in ((self._laco_leitura, "esp32-leitura"),
                           (self._laco_escrita, "esp32-escrita")):
            t = threading.Thread(target=alvo, name=nome, daemon=True)
            t.start()
            self._threads.append(t)

    def parar(self):
        self._rodando = False
        with self._cond:
            self._cond.notify_all()
        self._fechar()
        for t in self._threads:
            t.join(timeout=3)

    def enviar(self, comando):
        """Coloca o comando na fila de saida. Devolve False se a ESP32 nao estiver conectada
        (quem chamou mantem o registro pendente e reenvia quando ela voltar)."""
        if self._serial is None:
            return False
        with self._cond:
            self._controle.adicionar(comando)
            self._cond.notify_all()
        return True

    def reiniciar_programa(self):
        """Faz a ESP32 (re)comecar o main.py: Ctrl+C interrompe o que estiver rodando
        e Ctrl+D faz o 'soft reboot', que roda o main.py de novo.
        Serve para quando a placa ficou parada no prompt >>> (ex.: depois do Thonny)."""
        try:
            self._escrever(b"\r\x03\x03")
            time.sleep(0.2)
            return self._escrever(b"\x04")
        except (serial.SerialException, OSError):
            self._fechar()
            return False

    # ---------- parte interna ----------
    def _escrever(self, dados):
        """Escreve na porta em pedacos pequenos, com pausa (ver TAMANHO_PEDACO)."""
        s = self._serial
        if s is None:
            return False
        with self._trava_escrita:
            for i in range(0, len(dados), TAMANHO_PEDACO):
                s.write(dados[i:i + TAMANHO_PEDACO])
                if i + TAMANHO_PEDACO < len(dados):
                    time.sleep(PAUSA_PEDACO_S)
        return True

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
        # um "fim de linha" solto descarta qualquer pedaco de comando que tenha
        # ficado incompleto na entrada da ESP32 (ex.: o app fechou no meio do envio)
        s.write(b"\n")
        self._serial = s
        self.porta = porta
        self.ao_conexao(True, porta)
        return True

    def _fechar(self):
        s = self._serial
        if s is None:
            return
        self._serial = None
        with self._cond:
            self._controle.limpar()
        try:
            s.close()
        except Exception:
            pass
        self.ao_conexao(False, self.porta)

    def _laco_escrita(self):
        while self._rodando:
            with self._cond:
                comando = self._controle.proximo(time.monotonic())
                if comando is None:
                    self._cond.wait(timeout=0.2)
                    continue
            dados = (json.dumps(comando, ensure_ascii=False) + "\n").encode("utf-8")
            try:
                self._escrever(dados)
            except (serial.SerialException, OSError):
                self._fechar()

    def _laco_leitura(self):
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
                continue
            with self._cond:
                self._controle.resposta(evento)
                self._cond.notify_all()
            try:
                self.ao_evento(evento)
            except Exception as erro:  # um erro no app nao pode matar a leitura
                print("Erro ao tratar evento da ESP32:", erro)
