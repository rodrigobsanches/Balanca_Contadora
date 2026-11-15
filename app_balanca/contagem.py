"""Regras de contagem de pecas por peso.

Funcoes puras (sem tela, sem balanca, sem internet), para poderem ser testadas no PC.
"""
from dataclasses import dataclass

LIMITE_INCERTEZA = 0.3       # quanto a divisao pode "sobrar" antes de virar contagem incerta
MIN_DIVISOES_PECA = 5        # peca deve pesar pelo menos 5 divisoes da balanca
MIN_DIVISOES_AMOSTRA = 20    # amostra deve pesar pelo menos 20 divisoes


@dataclass
class ResultadoContagem:
    quantidade: int
    quantidade_bruta: float
    peso_liquido_g: float
    incerta: bool


@dataclass
class ResultadoConferencia:
    resultado: str      # "OK", "FALTA" ou "SOBRA"
    diferenca: int      # contada - esperada
    mensagem: str


def contar_pecas(peso_total_g, peso_unit_g, tara_g=0.0, limite_incerteza=LIMITE_INCERTEZA):
    """Calcula quantas pecas existem a partir do peso total."""
    if peso_unit_g <= 0:
        raise ValueError("O peso de 1 peça precisa ser maior que zero.")
    peso_liquido = peso_total_g - tara_g
    if peso_liquido <= 0:
        return ResultadoContagem(0, 0.0, max(peso_liquido, 0.0), False)
    bruta = peso_liquido / peso_unit_g
    quantidade = int(round(bruta))
    incerta = abs(bruta - quantidade) > limite_incerteza or quantidade == 0
    return ResultadoContagem(quantidade, bruta, peso_liquido, incerta)


def peso_unitario_por_amostra(peso_amostra_g, quantidade_amostra):
    """Peso de 1 peca a partir de uma amostra com N pecas."""
    if quantidade_amostra <= 0:
        raise ValueError("A amostra precisa ter pelo menos 1 peça.")
    if peso_amostra_g <= 0:
        raise ValueError("A amostra precisa ter peso maior que zero.")
    return peso_amostra_g / quantidade_amostra


def peso_unitario_por_etapas(medidas):
    """Cadastro pela balanca: medidas = [(pecas, peso_g), ...] (ex.: 1, 5 e 10 pecas).

    Peso de 1 peca = peso total / total de pecas (as medidas com mais pecas pesam mais na
    conta, e o erro de 1 divisao some aos poucos). Devolve (peso_unit, maior_diferenca),
    onde maior_diferenca e a maior distancia (0,10 = 10%) entre o peso de 1 peca de cada
    medida e o resultado: grande demais = alguma etapa teve o numero errado de pecas."""
    if not medidas or any(n <= 0 or peso <= 0 for n, peso in medidas):
        raise ValueError("Cada etapa precisa de pecas e de peso maior que zero.")
    peso_unit = sum(peso for _, peso in medidas) / sum(n for n, _ in medidas)
    diferenca = max(abs(peso / n - peso_unit) / peso_unit for n, peso in medidas)
    return peso_unit, diferenca


def avisos_de_precisao(peso_unit_g, divisao_g, peso_amostra_g=None):
    """Lista de avisos quando a balanca nao tem resolucao suficiente."""
    avisos = []
    if divisao_g > 0 and peso_unit_g < MIN_DIVISOES_PECA * divisao_g:
        avisos.append("Peça leve demais para uma contagem confiável nesta balança.")
    if peso_amostra_g is not None and divisao_g > 0 \
            and peso_amostra_g < MIN_DIVISOES_AMOSTRA * divisao_g:
        avisos.append("Amostra leve demais: coloque mais peças na amostra.")
    return avisos


def conferir(quantidade_contada, quantidade_esperada):
    """Compara a quantidade contada com a do pedido."""
    diferenca = quantidade_contada - quantidade_esperada
    if diferenca == 0:
        return ResultadoConferencia("OK", 0, "Quantidade conferida.")
    if diferenca < 0:
        faltam = -diferenca
        texto = "Falta 1 peça." if faltam == 1 else f"Faltam {faltam} peças."
        return ResultadoConferencia("FALTA", diferenca, texto)
    texto = "Sobra 1 peça." if diferenca == 1 else f"Sobram {diferenca} peças."
    return ResultadoConferencia("SOBRA", diferenca, texto)
