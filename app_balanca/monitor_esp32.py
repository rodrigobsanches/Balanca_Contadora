"""Monitor da ESP32 no terminal (teste da Fase 3a, sem telas).

Mostra tudo o que chega da ESP32 e o que o controlador faz com isso.
Feche o Thonny antes (ele ocupa a porta). Rodar na pasta do projeto:

    .venv\\Scripts\\python app_balanca\\monitor_esp32.py

Comandos que voce pode digitar:
    sync                      pede os cadastros ao Firebase
    cadastros                 mostra operadores, produtos e pedidos guardados no PC
    inventario P001 1040      conta P001 com 1040 g no prato e registra (precisa de operador logado)
    pendentes                 mostra o estado dos registros
    wifi on | wifi off        liga/desliga o Wi-Fi da ESP32 (teste da fila)
    reiniciar                 reinicia o main.py da ESP32 (se ela ficou parada no >>>)
    sair                      fecha o monitor
"""
import json
import os
import sys

PASTA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PASTA)

from config_app import caminho_dados, carregar_config  # noqa: E402
from contagem import contar_pecas  # noqa: E402
from controlador import Controlador  # noqa: E402
from dados_locais import DadosLocais  # noqa: E402
from esp32_serial import LigacaoESP32  # noqa: E402


def main():
    config = carregar_config()
    dados = DadosLocais(caminho_dados(config))

    def avisar(tipo, info):
        print("  [app] %-12s %s" % (tipo, info if info is not None else ""))

    ligacao = None

    def enviar(cmd):
        print("  >>> ESP32:", json.dumps(cmd, ensure_ascii=False)[:150])
        return ligacao.enviar(cmd) if ligacao else False

    ctrl = Controlador(config, dados, enviar, avisar)

    def ao_evento(ev):
        print("  <<< ESP32:", json.dumps(ev, ensure_ascii=False)[:150])
        ctrl.tratar_evento(ev)

    def ao_texto(linha):
        print("  ... ESP32 (texto):", linha[:150])

    ligacao = LigacaoESP32(ao_evento, ctrl.ao_conexao, config.get("porta_esp32", "auto"), ao_texto)
    ligacao.iniciar()
    print("Procurando a ESP32... (digite 'sair' para fechar)")

    while True:
        try:
            partes = input().strip().split()
        except (EOFError, KeyboardInterrupt):
            break
        if not partes:
            continue
        cmd = partes[0].lower()
        if cmd == "sair":
            break
        elif cmd == "sync":
            enviar({"c": "sync"})
        elif cmd == "reiniciar":
            print("Reiniciando o programa da ESP32 (Ctrl+C, Ctrl+D)...")
            ligacao.reiniciar_programa()
        elif cmd == "cadastros":
            for tipo in ("operadores", "produtos", "pedidos"):
                print(tipo, json.dumps(dados.cadastros(tipo), ensure_ascii=False, indent=1))
        elif cmd == "pendentes":
            print(dados.contar_por_status())
        elif cmd == "wifi" and len(partes) == 2:
            enviar({"c": "wifi", "ligado": partes[1] == "on"})
        elif cmd == "inventario" and len(partes) == 3:
            if not ctrl.operador:
                print("Encoste um chaveiro cadastrado primeiro.")
                continue
            produto = dados.cadastro("produtos", partes[1])
            if not produto:
                print("Produto nao encontrado. Rode 'sync' ou 'cadastros'.")
                continue
            peso = float(partes[2])
            c = contar_pecas(peso, produto["peso_unit_g"])
            print("Contagem: %d pecas (incerta: %s)" % (c.quantidade, c.incerta))
            ctrl.confirmar_inventario(partes[1], c, peso, 0, produto["peso_unit_g"])
        else:
            print(__doc__)

    ligacao.parar()
    dados.fechar()


if __name__ == "__main__":
    main()
