# config_exemplo.py
# Copie este arquivo para "config.py" e preencha com os seus dados.
# O config.py NAO vai para o GitHub (esta no .gitignore).

# --- Wi-Fi: lista de redes, na ordem de preferencia ---
# A placa tenta uma de cada vez ate conectar. Ex.: a de casa e o roteador do celular.
WIFI_REDES = [
    ("nome-da-rede-de-casa", "senha-da-rede-de-casa"),
    ("nome-do-roteador-do-celular", "senha-do-celular"),
]
WIFI_TEMPO_TENTATIVA_S = 15   # tempo maximo tentando cada rede

# --- Firebase (Configuracoes do projeto no console do Firebase) ---
FIREBASE_API_KEY = "cole-aqui-a-chave-de-api-da-web"
FIREBASE_DB_URL = "https://SEU-PROJETO-default-rtdb.firebaseio.com"   # sem "/" no final
FIREBASE_EMAIL = "esp32@balanca.local"   # usuario criado no Firebase Authentication
FIREBASE_SENHA = "senha-do-usuario-da-esp32"

# --- Identificacao ---
ID_DISPOSITIVO = "esp32-01"
INTERVALO_STATUS_S = 60   # de quanto em quanto tempo atualiza dispositivos/<id> no Firebase

# --- Hardware ---
PINO_RGB = 48          # LED RGB da placa (em alguns clones e o 38)
PINO_LED_VERDE = 6
PINO_LED_AZUL = 7
PINO_SDA = 8           # PN532
PINO_SCL = 9           # PN532
PINO_BUZZER = None     # sem buzzer por enquanto. Quando tiver: 12
BUZZER_PASSIVO = False # True se o buzzer so toca com sinal PWM (passivo)
PINO_TRIG = 17         # HC-SR04
PINO_ECHO = 18         # HC-SR04 (com divisor de tensao!)

# --- Display de 7 segmentos, 2 digitos (numero do operador, 0 a 99) ---
# Segmento -> GPIO (cada segmento com um resistor de 100 Ohm). Ligacao pela posicao fisica
# (digito de frente, ponto embaixo a direita): em cima g f - a b; embaixo e d COMUM c ponto.
# CATODO = True: comum no GND (o vermelho). False: anodo comum, comum no 3V3 (o verde).
# Detalhes e desenho: docs/ligacoes.md. Sem display: *_PINOS = None.
DISPLAY_DEZENA_PINOS = {"a": 1, "b": 2, "c": 42, "d": 41, "e": 40, "f": 39, "g": 38}  # lado direito, pinos seguidos
DISPLAY_DEZENA_CATODO = True       # vermelho, catodo comum (comum no GND)
DISPLAY_UNIDADE_PINOS = {"a": 4, "b": 5, "c": 15, "d": 16, "e": 10, "f": 11, "g": 13}  # lado esquerdo (perto do 3V3)
DISPLAY_UNIDADE_CATODO = False     # verde, anodo comum (comum no 3V3)

# =====================================================================
# Calibracao: todos os ajustes finos ficam aqui (nada fixo no codigo).
# Se uma linha faltar, o programa usa o valor padrao mostrado.
# =====================================================================

# --- Presenca (sensor ultrassonico HC-SR04) ---
# Use esp32/testes/teste_presenca.py para ver a distancia medida e escolher os valores.
# Alcance do sensor: ~2 a 400 cm, em um cone estreito (~15 graus) a frente dele.
DISTANCIA_PERTO_CM = 60   # abaixo disso, "alguem chegou"
DISTANCIA_LONGE_CM = 80   # acima disso, "foi embora" (deixe uns 20 cm acima do PERTO)
TEMPO_CHEGOU_MS = 1000    # precisa ficar perto este tempo (evita alarme com quem so passa)
TEMPO_SAIU_MS = 5000      # precisa ficar longe este tempo (evita sair por um passo para tras)
PRESENCA_INTERVALO_MS = 100  # de quanto em quanto tempo mede (a decisao usa a mediana de 5)

# --- RFID (leitor PN532) ---
# O alcance NAO e ajustavel por aqui: com chaveiros de 13,56 MHz e de ~3 a 5 cm (fisica da antena).
RFID_TEMPO_LEITURA_MS = 50    # quanto tempo procura um chaveiro a cada volta do laco
RFID_IGNORAR_REPETIDO_S = 3   # o mesmo chaveiro so conta de novo depois deste tempo afastado

# --- Envio para a nuvem ---
ESPERA_APOS_FALHA_S = 10        # depois de uma falha, espera isto antes de tentar de novo
INTERVALO_STATUS_SERIAL_S = 30  # de quanto em quanto tempo manda o status para o app
