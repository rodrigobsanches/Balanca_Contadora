"""Cores, fontes e estilo (QSS) de todas as telas. Mudou uma cor? Muda so aqui.

Telas de toque: botoes grandes, letras grandes, pouco texto.
"""
COR = {
    "fundo": "#F3F5F8",
    "cartao": "#FFFFFF",
    "texto": "#1B1F24",
    "texto_suave": "#5F6B7A",
    "primaria": "#1565C0",
    "primaria_escura": "#0D47A1",
    "sucesso": "#2E7D32",
    "erro": "#C62828",
    "atencao": "#E65100",
    "desativado": "#B0BEC5",
    "visor": "#1E272E",
    "visor_texto": "#E8F5E9",
    "borda": "#D5DCE4",
}


def formatar_numero(valor, casas=0):
    """1234.5 -> '1.234,5' (padrao brasileiro)."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_peso(gramas):
    if gramas is None:
        return "--- g"
    casas = 0 if float(gramas).is_integer() else 1
    return formatar_numero(gramas, casas) + " g"


QSS = f"""
QWidget {{
    background: {COR['fundo']};
    color: {COR['texto']};
    font-family: 'Segoe UI', 'Arial';
    font-size: 20px;
}}
QPushButton {{
    border: none;
    border-radius: 14px;
    padding: 16px 24px;
    font-size: 26px;
    font-weight: 600;
    color: white;
    background: {COR['primaria']};
}}
QPushButton:pressed {{ background: {COR['primaria_escura']}; }}
QPushButton:disabled {{ background: {COR['desativado']}; color: #ECEFF1; }}
QPushButton[tipo="secundario"] {{
    background: {COR['cartao']};
    color: {COR['primaria']};
    border: 3px solid {COR['primaria']};
}}
QPushButton[tipo="secundario"]:pressed {{ background: #E3F2FD; }}
QPushButton[tipo="sucesso"] {{ background: {COR['sucesso']}; }}
QPushButton[tipo="perigo"] {{ background: {COR['erro']}; }}
QPushButton[tipo="produto"] {{
    background: {COR['cartao']};
    color: {COR['texto']};
    border: 2px solid {COR['borda']};
    font-size: 22px;
    font-weight: 500;
    text-align: left;
    padding: 14px 20px;
}}
QPushButton[tipo="produto"]:pressed {{ background: #E3F2FD; border-color: {COR['primaria']}; }}
QPushButton[tipo="pequeno"] {{ font-size: 20px; padding: 10px 16px; }}

QLabel {{ background: transparent; }}
QLabel[papel="titulo"] {{ font-size: 40px; font-weight: 700; }}
QLabel[papel="subtitulo"] {{ font-size: 26px; color: {COR['texto_suave']}; }}
QLabel[papel="gigante"] {{ font-size: 130px; font-weight: 800; color: {COR['primaria']}; }}
QLabel[papel="peso"] {{ font-size: 28px; font-weight: 600; }}
QLabel[papel="aviso"] {{
    font-size: 22px; font-weight: 600; color: {COR['atencao']};
    background: #FFF3E0; border-radius: 10px; padding: 8px 14px;
}}
QLabel[papel="erro"] {{
    font-size: 26px; font-weight: 700; color: white;
    background: {COR['erro']}; border-radius: 12px; padding: 14px 20px;
}}
QLabel[papel="info"] {{
    font-size: 26px; font-weight: 600; color: white;
    background: {COR['primaria']}; border-radius: 12px; padding: 14px 20px;
}}

QFrame#cartao {{ background: {COR['cartao']}; border: 1px solid {COR['borda']}; border-radius: 18px; }}
QFrame#barra_status {{ background: {COR['cartao']}; border-bottom: 1px solid {COR['borda']}; }}
QFrame#barra_status QLabel {{ font-size: 16px; color: {COR['texto_suave']}; padding: 0 10px; }}
QFrame#visor {{ background: {COR['visor']}; }}
QFrame#visor QLabel {{ color: {COR['visor_texto']}; }}
QScrollArea {{ border: none; }}
"""
