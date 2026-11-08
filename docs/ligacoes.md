# Ligações da ESP32-S3

| Função | GPIO | Ligação |
|---|---|---|
| LED RGB (da placa) | 48 | já vem na placa (em alguns clones é o 38) |
| LED verde | 6 | GPIO → resistor (47 a 330 Ω) → perna longa; perna curta → GND |
| LED azul | 7 | igual ao verde |
| PN532 SDA | 8 | modo I2C: chave 1 = ON, chave 2 = OFF |
| PN532 SCL | 9 | |
| PN532 VCC / GND | 3V3 / GND | |
| Buzzer (opcional, ainda não instalado) | 12 | `+` no GPIO 12, `−` no GND. Sem buzzer: `PINO_BUZZER = None` no `config.py` |
| HC-SR04 TRIG | 17 | ligação direta |
| HC-SR04 ECHO | 18 | **com divisor**: ECHO → 1 kΩ → GPIO 18; GPIO 18 → 2 kΩ → GND |
| HC-SR04 VCC / GND | 5V / GND | pino `5V` da placa |

**Evitar:** GPIO 0, 3, 45, 46 (boot), 19 e 20 (USB), 35, 36 e 37 (memória PSRAM).

> O divisor no ECHO é obrigatório: o HC-SR04 devolve 5 V e a ESP32 aceita no máximo 3,3 V.
> Sem resistor de 2 kΩ, use dois de 1 kΩ em série.

## Gravar na placa

1. Copie `esp32/config_exemplo.py` para `esp32/config.py` e preencha.
2. No Thonny, salve **na placa** (Arquivo → Salvar como → Dispositivo MicroPython):
   `config.py`, `pn532.py`, `sinalizacao.py`, `presenca.py` e `main.py`.
3. Os arquivos da pasta `esp32/testes/` são rodados direto do Thonny (F5), um de cada vez,
   **depois** de salvar os módulos acima na placa.
