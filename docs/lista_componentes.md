# Lista de componentes e materiais

Tudo o que foi usado na montagem do protótipo "balança contadora de peças" (estado em 13/11/2026).
Pinagem detalhada: [ligacoes.md](ligacoes.md).

> As quantidades de **fios jumper** são as da montagem final, contadas por ligação. Confira na
> protoboard antes de entregar, porque alguns fios podem ter sido trocados durante os testes.

## 1. Eletrônica (montagem na protoboard)

| # | Componente | Qtd | Função no projeto | Ligação |
|---|---|---|---|---|
| 1 | **ESP32-S3 DevKitC** (MicroPython 1.29, duas portas USB-C: "COM" e "USB") | 1 | Microcontrolador: lê RFID e presença, controla LEDs e display, envia dados ao Firebase pelo Wi-Fi, fala com o app pela USB | Ao lado da protoboard, por jumpers |
| 2 | LED RGB endereçável WS2812 (já vem na placa da ESP32-S3) | 1 | Sinalização (cores por estado) | GPIO 48 |
| 3 | **Protoboard 830 pontos** | 1 | Base da montagem | — |
| 4 | **Módulo leitor RFID/NFC PN532** (13,56 MHz, modo I2C) | 1 | Sensor: identifica o operador pelo chaveiro | SDA GPIO 8, SCL GPIO 9, 3V3, GND |
| 5 | Barra de pinos 4 vias (soldada no PN532) | 1 | Ligação do PN532 | — |
| 6 | **Chaveiros RFID 13,56 MHz (Mifare)** | 1 + kit | Identificação de cada operador | — |
| 7 | **Sensor ultrassônico HC-SR04** | 1 | Sensor de presença ("acorda" o sistema quando alguém chega perto) | TRIG GPIO 17, ECHO GPIO 18 (com divisor), 5V, GND |
| 8 | **Display 7 segmentos vermelho, cátodo comum** (CTK D168K) | 1 | Atuador: dezena do número do operador | GPIO 1, 2, 42, 41, 40, 39, 38; comum no GND |
| 9 | **Display 7 segmentos verde, ânodo comum** (ELS-512GWA) | 1 | Atuador: unidade do número do operador | GPIO 4, 5, 15, 16, 10, 11, 13; comum no 3V3 |
| 10 | **LED de alto brilho verde** | 1 | Sinalização (OK) | GPIO 6 |
| 11 | **LED de alto brilho azul** | 1 | Sinalização (aguardando / atenção) | GPIO 7 |
| 12 | **Resistor 100 Ω** (¼ W) | **16** | 14 nos segmentos dos displays (um por segmento) + 2 nos LEDs | — |
| 13 | **Resistor 10 kΩ** (¼ W) | **3** | Divisor de tensão do ECHO do HC-SR04 (5 V → 3,3 V): 1 em cima + 2 em série embaixo | — |
| 14 | **Fios jumper** | **≈ 32** | Ver a divisão abaixo | — |
| 15 | **Cabo USB-C** | 1 | ESP32-S3 ↔ balança (porta USB nativa da placa) | — |

**Fios jumper por ligação (≈ 32):**

| Ligação | Qtd | Tipo |
|---|---|---|
| Display vermelho: 7 segmentos → ESP32 | 7 | macho-fêmea |
| Display verde: 7 segmentos → ESP32 | 7 | macho-fêmea |
| Comum de cada display → trilho (GND / 3V3) | 2 | macho-macho |
| Alimentação dos trilhos: 3V3 → trilho +, GND → trilho − (e 5V do HC-SR04) | 3 | macho-fêmea |
| PN532: GND, VCC, SDA, SCL | 4 | fêmea-fêmea ou macho-fêmea |
| HC-SR04: VCC, GND, TRIG, ECHO (para o divisor) + divisor → GPIO 18 | 5 | macho-fêmea |
| LEDs verde e azul → GPIO 6 e 7 + GND | 3 | macho-fêmea |
| Ligações curtas na protoboard (resistores/divisor), se usadas | ~1 | macho-macho |

## 2. Equipamento de pesagem e saídas

| # | Item | Qtd | Função |
|---|---|---|---|
| 16 | **Balança comercial** com computador embutido (Windows 11 IoT, tela de toque 1280 × 800, impressora térmica de etiquetas) | 1 | Sensor de peso (célula de carga), tela do operador, roda o app em Python e **imprime a etiqueta** (atuador). Emprestada |
| 17 | **Rolo de etiquetas** térmicas (58 mm) | 1 | Etiqueta de pedido conferido com QR code |
| 18 | **Caixa de som** (entrada P2) | 1 | Atuador: voz com as mensagens do sistema |
| 19 | **Adaptador de áudio USB → P2** (placa de som USB) | 1 | Liga a caixa de som na balança |
| 20 | **Celular com roteador (hotspot)** | 1 | Internet da ESP32-S3 na feira |

## 3. Comprados e não usados

| Item | Motivo |
|---|---|
| Buzzer | O modelo comprado é de 12 V. A caixa de som cobre os avisos sonoros (o código aceita buzzer em GPIO 12) |
| 2º sensor HC-SR04 | Reserva |
| Resistores sobrando (kit de 100 Ω) | Reserva |

## 4. Ferramentas usadas na montagem

| Ferramenta | Uso |
|---|---|
| Multímetro (Fluke 114) | Conferir resistores, divisor de tensão, tensões dos trilhos e dos pinos |
| Ferro de solda + estanho | Soldar a barra de pinos do PN532 |

## 5. Software e nuvem (custo zero)

| Item | Uso |
|---|---|
| MicroPython 1.29 (ESP32-S3) + Thonny | Firmware da ESP32 |
| Python 3.14 + PySide6, pyserial, qrcode, pywin32 | App da balança (telas, contagem, impressão) |
| Firebase Realtime Database (plano gratuito Spark) | Banco de dados na nuvem |
| Streamlit Community Cloud | Dashboard web (celular): https://balanca-contadora.streamlit.app |
| GitHub | Código-fonte: https://github.com/rodrigobsanches/Balanca_Contadora |
| Voz pt-BR do Windows (gerada uma vez em arquivos WAV) | Mensagens faladas |
