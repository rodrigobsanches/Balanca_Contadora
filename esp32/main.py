# main.py - Fase 2: periféricos + comandos pela serial + Wi-Fi + Firebase + fila offline
#   - presenca (HC-SR04) e chaveiro (PN532) viram eventos JSON para o app
#   - o app manda comandos JSON pela serial (ver docs/protocolo_serial.md)
#   - "enviar" e "atualizar" vao para o Firebase; sem internet, ficam na fila e sobem depois
#   - a cada INTERVALO_STATUS_S, atualiza dispositivos/<id> no Firebase
# Regra de ouro: o laco nunca espera sem motivo. So as chamadas HTTPS demoram (1 a 3 s).
from machine import Pin, I2C
import time

import config
from firebase import Firebase, ErroFirebase, caminho_valido
from fila import Fila
from pn532 import PN532
from presenca import Presenca
from rede import Rede
from serial_app import SerialApp, enviar
from sinalizacao import Sinalizacao, PADROES

VERSAO_FW = "0.2"
ESPERA_APOS_FALHA_MS = 10000   # depois de uma falha de envio, espera antes de tentar de novo
INTERVALO_STATUS_SERIAL_MS = 30000


def log(msg):
    enviar({"t": "log", "msg": msg})


# ---------------- periféricos ----------------
sinal = Sinalizacao(config.PINO_RGB, config.PINO_LED_VERDE, config.PINO_LED_AZUL,
                    config.PINO_BUZZER, config.BUZZER_PASSIVO)

presenca = Presenca(config.PINO_TRIG, config.PINO_ECHO,
                    config.DISTANCIA_PERTO_CM, config.DISTANCIA_LONGE_CM,
                    config.TEMPO_CHEGOU_MS, config.TEMPO_SAIU_MS)

i2c = I2C(0, sda=Pin(config.PINO_SDA), scl=Pin(config.PINO_SCL), freq=100000)
time.sleep_ms(500)
leitor = PN532(i2c)
if leitor.versao():
    leitor.configurar()
else:
    leitor = None
    log("PN532 nao respondeu")
    sinal.definir("atencao")

# ---------------- comunicação ----------------
serial = SerialApp()
rede = Rede(config.WIFI_REDES, config.WIFI_TEMPO_TENTATIVA_S)
fb = Firebase(config.FIREBASE_API_KEY, config.FIREBASE_DB_URL,
              config.FIREBASE_EMAIL, config.FIREBASE_SENHA)
fila = Fila()

proxima_tentativa = time.ticks_ms()   # quando pode tentar enviar a fila de novo
proximo_status_fb = time.ticks_ms()
proximo_status_serial = time.ticks_ms()


def executar(op):
    """Faz a operacao no Firebase. Levanta excecao se falhar."""
    if op["op"] == "put":
        fb.gravar(op["path"], op["dados"])
    else:
        fb.atualizar(op["path"], op["dados"])


def status_serial():
    enviar({"t": "status", "wifi": rede.conectado, "rede": rede.nome_atual(),
            "rssi": rede.rssi(), "fila": fila.tamanho})


def guardar_na_fila(op):
    if fila.adicionar(op):
        enviar({"t": "ack", "id": op["id"], "ok": False, "fila": True})
    else:
        enviar({"t": "ack", "id": op["id"], "ok": False, "fila": False, "erro": "fila cheia"})


def receber_operacao(cmd):
    """Comandos enviar (PUT) e atualizar (PATCH)."""
    global proxima_tentativa
    op = {"op": "put" if cmd["c"] == "enviar" else "patch",
          "id": cmd.get("id"), "path": cmd.get("path"), "dados": cmd.get("dados")}
    if not op["id"] or op["dados"] is None or not caminho_valido(op["path"]):
        enviar({"t": "ack", "id": op["id"], "ok": False, "erro": "comando invalido"})
        return
    # so envia na hora se a fila estiver vazia (para manter a ordem das operacoes)
    if rede.conectado and fila.tamanho == 0:
        try:
            executar(op)
            enviar({"t": "ack", "id": op["id"], "ok": True})
            return
        except ErroFirebase as e:
            if e.permanente:
                enviar({"t": "ack", "id": op["id"], "ok": False, "erro": str(e)})
                return
            log("Firebase: %s" % e)
        except Exception as e:
            log("Falha de rede: %s" % e)
        proxima_tentativa = time.ticks_add(time.ticks_ms(), ESPERA_APOS_FALHA_MS)
    guardar_na_fila(op)


def sincronizar():
    """Baixa os cadastros e repassa ao app."""
    if not rede.conectado:
        enviar({"t": "sync", "ok": False, "erro": "sem wifi"})
        return
    try:
        enviar({"t": "sync", "ok": True,
                "operadores": fb.ler("operadores") or {},
                "produtos": fb.ler("produtos") or {},
                "pedidos": fb.ler("pedidos") or {}})
    except Exception as e:
        enviar({"t": "sync", "ok": False, "erro": str(e)})


def tratar_comando(cmd):
    c = cmd["c"]
    if c == "ping":
        enviar({"t": "pong", "fw": VERSAO_FW})
    elif c == "sinal":
        if cmd.get("estado") in PADROES:
            sinal.definir(cmd["estado"])
        else:
            log("estado de sinal desconhecido: %s" % cmd.get("estado"))
    elif c in ("enviar", "atualizar"):
        receber_operacao(cmd)
    elif c == "sync":
        sincronizar()
    elif c == "status":
        status_serial()
    elif c == "wifi":
        # {"c":"wifi","ligado":false} derruba o Wi-Fi de proposito (teste da fila / demo)
        ligado = cmd.get("ligado", True)
        rede.pausar(not ligado)
        log("Wi-Fi %s pelo comando" % ("religado" if ligado else "desligado"))
    elif c == "invalido":
        log("linha ignorada (nao e um comando JSON): %s" % cmd.get("linha"))
    else:
        log("comando desconhecido: %s" % c)


def processar_fila():
    """Envia UMA operacao da fila por vez (para nao travar o laco)."""
    global proxima_tentativa
    if fila.tamanho == 0 or time.ticks_diff(proxima_tentativa, time.ticks_ms()) > 0:
        return
    op = fila.primeira()
    if op is None:
        return
    if op.get("estragada"):
        log("linha estragada removida da fila")
        fila.remover_primeira()
        return
    try:
        executar(op)
    except ErroFirebase as e:
        if e.permanente:
            log("operacao descartada: %s" % e)
            enviar({"t": "ack", "id": op.get("id"), "ok": False, "erro": str(e)})
            fila.remover_primeira()
        else:
            log("Firebase: %s (tento de novo em %d s)" % (e, ESPERA_APOS_FALHA_MS // 1000))
            proxima_tentativa = time.ticks_add(time.ticks_ms(), ESPERA_APOS_FALHA_MS)
        return
    except Exception as e:
        log("Falha de rede: %s (tento de novo em %d s)" % (e, ESPERA_APOS_FALHA_MS // 1000))
        proxima_tentativa = time.ticks_add(time.ticks_ms(), ESPERA_APOS_FALHA_MS)
        return
    fila.remover_primeira()
    enviar({"t": "ack", "id": op["id"], "ok": True, "da_fila": True})
    if fila.tamanho == 0:
        status_serial()


def status_firebase():
    """Mostra no Firebase que a ESP32 esta viva (dispositivos/<id>)."""
    try:
        fb.atualizar("dispositivos/" + config.ID_DISPOSITIVO, {
            "online": True,
            "ultimo_contato": {".sv": "timestamp"},  # hora do servidor do Firebase
            "fila": fila.tamanho,
            "rssi": rede.rssi(),
            # o nome da rede NAO vai para a nuvem: o dashboard e mostrado ao publico
            "fw": VERSAO_FW,
        })
    except Exception as e:
        log("status no Firebase falhou: %s" % e)


# ---------------- laço principal ----------------
enviar({"t": "hello", "fw": VERSAO_FW, "id": config.ID_DISPOSITIVO})
if fila.tamanho:
    log("%d operacao(oes) na fila desde a ultima vez" % fila.tamanho)

ultimo_uid = None
ultimo_uid_ms = 0

while True:
    sinal.atualizar()

    mudou = presenca.atualizar()
    if mudou is not None:
        enviar({"t": "presenca", "perto": mudou, "cm": int(presenca.ultima_cm)})
        sinal.definir("aguardando" if mudou else "ocioso")

    if leitor:
        uid = leitor.ler_uid(timeout_ms=50)
        agora = time.ticks_ms()
        # evita repetir o mesmo chaveiro enquanto ele continua encostado
        if uid and (uid != ultimo_uid or time.ticks_diff(agora, ultimo_uid_ms) > 3000):
            enviar({"t": "rfid", "uid": uid})
            sinal.definir("ok")
            ultimo_uid = uid
        if uid:
            ultimo_uid_ms = agora

    cmd = serial.ler_comando()
    if cmd:
        tratar_comando(cmd)

    estado_wifi = rede.atualizar()
    if estado_wifi is True:
        log("Wi-Fi conectado: %s" % rede.nome_atual())
        proxima_tentativa = time.ticks_ms()
        proximo_status_fb = time.ticks_ms()   # avisa o Firebase logo que conectar
        status_serial()
    elif estado_wifi is False:
        log("Wi-Fi caiu")
        status_serial()

    if rede.conectado:
        processar_fila()
        if time.ticks_diff(time.ticks_ms(), proximo_status_fb) >= 0:
            status_firebase()
            proximo_status_fb = time.ticks_add(time.ticks_ms(), config.INTERVALO_STATUS_S * 1000)

    if time.ticks_diff(time.ticks_ms(), proximo_status_serial) >= 0:
        status_serial()
        proximo_status_serial = time.ticks_add(time.ticks_ms(), INTERVALO_STATUS_SERIAL_MS)

    time.sleep_ms(10)
