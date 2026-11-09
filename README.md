# Balança Contadora de Peças

**Implementação de um protótipo de balança automatizado utilizando micro controladores,
sensores e atuadores para medição de peso e controle de quantidade de peças.**

Projeto acadêmico da disciplina **Aplicação Cloud e Indústria 4.0 em Python**.

## O que faz

O operador coloca várias peças iguais sobre a balança e o sistema informa **quantas peças
existem**, a partir do peso total. Serve para:

- **Inventário de estoque:** contar peças e atualizar o estoque.
- **Conferência de despacho:** conferir a quantidade de um pedido antes do envio e imprimir
  uma etiqueta de "conferido" com QR code.

Cada operação registra **quem fez** (chaveiro RFID), **quando** e **o resultado**, e é enviada
para a **nuvem**. Um **dashboard** mostra estoque, histórico e auditoria, inclusive no celular.

## Arquitetura

```
Balança comercial (PC embarcado)  ── USB ──  ESP32-S3 (MicroPython)  ── Wi-Fi ──  Firebase
  app Python (PySide6)                        RFID PN532                            │
  contagem, telas, etiqueta                   sensor de presença HC-SR04            ▼
                                              LED RGB, LEDs                 Dashboard Streamlit
```

- **Microcontrolador:** ESP32-S3
- **Sensores:** célula de carga da balança, leitor RFID PN532, sensor ultrassônico HC-SR04
- **Atuadores:** LED RGB, LEDs, impressora de etiquetas, voz (buzzer opcional)
- **Nuvem:** Firebase Realtime Database + Streamlit Community Cloud

## Pastas

| Pasta | Conteúdo |
|---|---|
| `esp32/` | Firmware MicroPython da ESP32-S3 |
| `app_balanca/` | App Python da balança (telas, contagem, comunicação com a ESP32) |
| `dashboard/` | Dashboard Streamlit |
| `firebase/` | Regras e dados de exemplo do banco |
| `docs/` | Documentação pública (protocolo serial, ligações) |
| `scripts/` | Ferramentas de apoio |

## Como rodar

Cada pasta terá o seu passo a passo. Por enquanto:

```bash
# testes no PC: lógica de contagem e partes do firmware que não dependem do hardware
pip install -r app_balanca/requirements.txt
pytest app_balanca/tests esp32/tests_pc
```

O app da balança roda em **modo simulado** quando não há balança conectada, então dá para
testar tudo no PC:

```bash
# copie app_balanca/config_exemplo.json para app_balanca/config.json (opcional)
python app_balanca/main.py
```

Abre a janela do app (1366 × 768, o tamanho da tela da balança) e uma janela **Simulação**
para colocar peso no prato, encostar um chaveiro e simular presença. Com a ESP32 no USB,
o chaveiro e o sensor de verdade também funcionam e os registros vão para o Firebase.

## Segurança

Senhas, chaves do Firebase e credenciais **não ficam no repositório**. Use os arquivos
`*_exemplo` como modelo e crie as suas cópias locais.
