# Protocolo serial: app da balança ↔ ESP32-S3

- Ligação por **cabo USB** (porta serial).
- Uma mensagem **JSON por linha**, terminada em `\n`, UTF-8.
- O app **ignora** linhas que não sejam JSON válido (ex.: mensagens de boot do MicroPython).
- Mensagens que precisam de confirmação levam um `id` (uuid4 gerado pelo app).

## App → ESP32 (comandos, campo `c`)

| Comando | Exemplo | O que a ESP32 faz |
|---|---|---|
| `ping` | `{"c":"ping"}` | responde `{"t":"pong"}` |
| `sinal` | `{"c":"sinal","estado":"ok"}` | LED e buzzer: `ocioso`, `aguardando`, `ok`, `erro`, `atencao` |
| `enviar` | `{"c":"enviar","id":"<uuid>","path":"contagens/<uuid>","dados":{...}}` | **PUT** no Firebase; se falhar, guarda na fila offline |
| `atualizar` | `{"c":"atualizar","id":"<uuid>","path":"produtos/P001","dados":{"estoque_atual":120}}` | **PATCH** no Firebase |
| `sync` | `{"c":"sync"}` | baixa operadores, produtos e pedidos e responde com `t:"sync"` |

## ESP32 → App (eventos, campo `t`)

| Evento | Exemplo |
|---|---|
| `hello` | `{"t":"hello","fw":"0.1","id":"esp32-01"}` |
| `rfid` | `{"t":"rfid","uid":"04:A2:3B:1C"}` |
| `presenca` | `{"t":"presenca","perto":true,"cm":42}` |
| `ack` | `{"t":"ack","id":"<uuid>","ok":true}` / `{"t":"ack","id":"<uuid>","ok":false,"fila":true}` |
| `sync` | `{"t":"sync","operadores":{...},"produtos":{...},"pedidos":{...}}` |
| `status` | `{"t":"status","wifi":true,"rssi":-61,"fila":0}` |
| `log` | `{"t":"log","msg":"..."}` |

**Por que `PUT` com o `id` do app:** se a mesma mensagem for reenviada (queda de Wi-Fi ou
falta de `ack`), ela sobrescreve o mesmo registro em vez de duplicar.

## Padrões de sinalização

| Estado | LED RGB | Buzzer (se instalado) |
|---|---|---|
| `ocioso` | apagado | — |
| `aguardando` | azul | — |
| `ok` | verde por 2 s | 1 bipe curto |
| `erro` | vermelho por 3 s | 3 bipes longos |
| `atencao` | amarelo | 2 bipes curtos |
