"""Leitura do config do app (uma fonte so, usada pelo main.py e pelo monitor_esp32.py).

Usa app_balanca/config.json (seu, fora do Git). Se nao existir, usa o config_exemplo.json.
"""
import json
import os

PASTA_APP = os.path.dirname(os.path.abspath(__file__))


def carregar_config():
    for nome in ("config.json", "config_exemplo.json"):
        caminho = os.path.join(PASTA_APP, nome)
        if os.path.exists(caminho):
            with open(caminho, encoding="utf-8") as f:
                return json.load(f)
    return {}


def caminho_dados(config):
    """Arquivo SQLite dos dados locais, dentro da pasta do app."""
    return os.path.join(PASTA_APP, config.get("arquivo_dados", "dados_locais.db"))
