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

# --- Presenca ---
DISTANCIA_PERTO_CM = 60   # abaixo disso, "alguem chegou"
DISTANCIA_LONGE_CM = 80   # acima disso, "foi embora" (histerese)
TEMPO_CHEGOU_MS = 1000    # precisa ficar perto este tempo
TEMPO_SAIU_MS = 5000      # precisa ficar longe este tempo
