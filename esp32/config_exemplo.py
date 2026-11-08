# config_exemplo.py
# Copie este arquivo para "config.py" e preencha com os seus dados.
# O config.py NAO vai para o GitHub (esta no .gitignore).

# --- Wi-Fi (roteador do celular na feira) ---
WIFI_SSID = "nome-da-rede"
WIFI_SENHA = "senha-da-rede"

# --- Firebase (Configuracoes do projeto no console do Firebase) ---
FIREBASE_API_KEY = "cole-aqui-a-chave-de-api-da-web"
FIREBASE_DB_URL = "https://SEU-PROJETO-default-rtdb.firebaseio.com"
FIREBASE_EMAIL = "esp32-01@balanca.local"   # usuario criado no Firebase Authentication
FIREBASE_SENHA = "senha-do-usuario-da-esp32"

# --- Identificacao ---
ID_DISPOSITIVO = "esp32-01"

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
