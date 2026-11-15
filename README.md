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

**Dashboard:** https://balanca-contadora.streamlit.app (acesso com login)

## Arquitetura

```
Balança comercial (PC embarcado)  ── USB ──  ESP32-S3 (MicroPython)  ── Wi-Fi ──  Firebase
  app Python (PySide6)                        RFID PN532                            │
  contagem, telas, etiqueta                   sensor de presença HC-SR04            ▼
  voz (frases gravadas)                       LED RGB, LEDs, display        Dashboard Streamlit
                                              de 7 segmentos (operador)
```

- **Microcontrolador:** ESP32-S3
- **Sensores:** célula de carga da balança, leitor RFID PN532, sensor ultrassônico HC-SR04
- **Atuadores:** LED RGB, LEDs, display de 7 segmentos (número do operador), impressora de
  etiquetas, voz (buzzer opcional)
- **Nuvem:** Firebase Realtime Database + Streamlit Community Cloud

## Pastas

| Pasta | Conteúdo |
|---|---|
| `esp32/` | Firmware MicroPython da ESP32-S3 |
| `app_balanca/` | App Python da balança (telas, contagem, comunicação com a ESP32) |
| `dashboard/` | Dashboard Streamlit |
| `firebase/` | Regras e dados de exemplo do banco |
| `docs/` | Documentação pública (veja abaixo) |
| `scripts/` | Ferramentas de apoio (geração dos áudios e início automático na balança) |

**Documentação:**
- [Ligações da ESP32-S3](docs/ligacoes.md): pinos, resistores e montagem
- [Protocolo serial](docs/protocolo_serial.md): mensagens JSON entre o app e a ESP32
- [Lista de componentes](docs/lista_componentes.md): tudo o que foi usado no protótipo

## Como rodar

### Testes no PC

```bash
# testes no PC: lógica de contagem e partes do firmware que não dependem do hardware
pip install -r app_balanca/requirements.txt
pytest app_balanca/tests esp32/tests_pc dashboard/tests
```

### App da balança

O app da balança roda em **modo simulado** quando não há balança conectada, então dá para
testar tudo no PC:

```bash
# copie app_balanca/config_exemplo.json para app_balanca/config.json (opcional)
python app_balanca/main.py
```

Abre a janela do app (1280 × 800, o tamanho da tela da balança) e uma janela **Simulação**
para colocar peso no prato, encostar um chaveiro e simular presença. Com a ESP32 no USB,
o chaveiro e o sensor de verdade também funcionam e os registros vão para o Firebase.

Para testar só a ESP32, sem telas (feche o Thonny antes, ele ocupa a porta):

```bash
python app_balanca/monitor_esp32.py
```

### ESP32-S3

Grave o MicroPython na placa, copie `esp32/config_exemplo.py` para `config.py` (Wi-Fi e
Firebase) e envie os arquivos de `esp32/` (menos `tests_pc/`) pelo Thonny. Os testes de cada
periférico ficam em `esp32/testes/`.

### Dashboard

```bash
pip install -r dashboard/requirements.txt
# copie dashboard/.streamlit/secrets_exemplo.toml para secrets.toml e preencha
python dashboard/gerar_senha.py        # cria a linha de cada usuário (senha guardada só como hash)
streamlit run dashboard/app.py
```

Só entra quem tem usuário e senha. Perfis: **admin** (vê tudo e altera Cadastros) e
**leitura** (só consulta). Abrir com `?pedido=PED001` leva direto ao pedido na Auditoria;
o QR code da etiqueta usa esse link quando `url_dashboard` está no config do app.

## Segurança

Senhas, chaves do Firebase e credenciais **não ficam no repositório**. Use os arquivos
`*_exemplo` como modelo e crie as suas cópias locais.
