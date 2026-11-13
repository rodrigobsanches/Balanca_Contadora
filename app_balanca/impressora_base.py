"""Interface da impressora de etiquetas.

O app so conversa com esta interface. A impressora de verdade (a da balanca) fica no
adaptador privado balanca_privada/impressao.py (fora do GitHub). Sem ele, o app so mostra
a previa da etiqueta na tela.

A etiqueta chega como um dicionario (ver Controlador.dados_etiqueta):
    titulo, pedido_id, destino, endereco, itens [{produto, nome, quantidade}], peso_bruto_g, peso_liquido_g,
    operador, data_hora (ISO), qr (texto do QR code), balanca
"""


class Impressora:
    nome = "impressora"

    def imprimir_etiqueta(self, etiqueta):
        """Imprime. Devolve True se deu certo."""
        raise NotImplementedError


def criar_impressora(config):
    """Devolve a impressora da balanca, ou None (so previa na tela)."""
    if not config.get("imprimir_etiqueta"):
        return None
    try:
        from balanca_privada.impressao import ImpressoraLocal
        return ImpressoraLocal(config)
    except ImportError:
        print("Adaptador de impressao nao encontrado. So a previa da etiqueta sera mostrada.")
        return None
