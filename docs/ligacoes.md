# Ligações da ESP32-S3

| Função | GPIO | Ligação |
|---|---|---|
| LED RGB (da placa) | 48 | já vem na placa (em alguns clones é o 38) |
| LED verde | 6 | GPIO → resistor → perna longa; perna curta → GND. Para LED de alto brilho em 3,3 V, use **68 a 150 Ω** (ex.: 100 Ω); com 10 kΩ o LED acende muito fraco |
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
> Vale qualquer valor, desde que o resistor de baixo seja o **dobro** do de cima (proporção 1:2).
> Exemplos: 1 kΩ em cima + 2 kΩ embaixo, ou 10 kΩ em cima + dois de 10 kΩ em série embaixo.

## Display de 7 segmentos (2 dígitos: número do operador)

Pinos do display (padrão de 10 pinos), com o dígito de frente e o ponto embaixo à direita:
embaixo da esquerda para a direita **1 2 3 4 5**, em cima da direita para a esquerda **6 7 8 9 10**.
`1=e 2=d 4=c 5=dp 6=g 7=f 9=a 10=b`; **3 e 8 = comum** (ligue um deles).

Cada segmento: **GPIO → resistor 100 Ω → pino do display**. O ponto (pino 5) não é usado.

| Segmento | Pino do display | Dezena (GPIO) | Unidade (GPIO) |
|---|---|---|---|
| a | 9 | 1 | 14 |
| b | 10 | 2 | 15 |
| c | 4 | 4 | 16 |
| d | 2 | 5 | 21 |
| e | 1 | 10 | 38 |
| f | 7 | 11 | 39 |
| g | 6 | 13 | 40 |
| **comum** | 3 ou 8 | **3V3** (ânodo comum) | **GND** (cátodo comum) |

O tipo de cada display (ânodo ou cátodo comum) e os pinos ficam no `config.py`
(`DISPLAY_*_PINOS`, `DISPLAY_*_CATODO`). Teste: `esp32/testes/teste_display.py`.

## Gravar na placa

1. Copie `esp32/config_exemplo.py` para `esp32/config.py` e preencha.
2. No Thonny, envie **para a placa** (painel Arquivos → botão direito → Enviar para /):
   `config.py`, `pn532.py`, `sinalizacao.py`, `presenca.py`, `rede.py`, `fila.py`,
   `firebase.py`, `serial_app.py`, `display7.py` e, por último, `main.py`.
3. Os arquivos da pasta `esp32/testes/` são rodados direto do Thonny (F5), um de cada vez,
   **depois** de salvar os módulos acima na placa.
4. Com o Thonny conectado, o `main.py` é interrompido no boot. Para rodá-lo, digite
   `import main` no Shell. Sem o Thonny, ele roda sozinho ao ligar a placa.
5. A pasta `esp32/tests_pc/` **não** vai para a placa: são testes para rodar no PC
   (`pytest esp32/tests_pc`).
