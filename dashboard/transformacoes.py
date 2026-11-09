"""Transforma os dados do Firebase em tabelas (pandas). Sem Streamlit: testavel com pytest."""
import io
import time

import pandas as pd

FUSO = "America/Sao_Paulo"
ESP32_OFFLINE_APOS_S = 180   # sem contato ha mais de 3 min = offline (ela avisa a cada 60 s)

NOMES_MODO = {"inventario": "Inventário", "conferencia": "Conferência"}

COLUNAS_CONTAGENS = ["quando", "operador", "modo", "produto", "produto_nome", "pedido",
                     "quantidade", "esperada", "resultado", "diferenca", "incerta",
                     "peso_total_g", "peso_unit_g", "metodo", "balanca", "id"]


def _quando(registro):
    """Hora da contagem: a do servidor (confiavel); se faltar, a da balanca."""
    ts = registro.get("ts_servidor")
    if isinstance(ts, (int, float)):
        return pd.Timestamp(ts, unit="ms", tz="UTC").tz_convert(FUSO)
    try:
        return pd.Timestamp(registro.get("ts_balanca")).tz_localize(FUSO)
    except (TypeError, ValueError):
        return pd.NaT


def contagens_df(contagens):
    """{id: registro} -> tabela, mais recente primeiro."""
    linhas = []
    for id_, r in (contagens or {}).items():
        if not isinstance(r, dict):
            continue
        linhas.append({
            "quando": _quando(r),
            "operador": r.get("operador_nome") or r.get("operador_uid") or "",
            "modo": NOMES_MODO.get(r.get("modo"), r.get("modo", "")),
            "produto": r.get("produto", ""),
            "produto_nome": r.get("produto_nome", ""),
            "pedido": r.get("pedido_id") or "",
            "quantidade": r.get("quantidade"),
            "esperada": r.get("quantidade_esperada"),
            "resultado": r.get("resultado", ""),
            "diferenca": r.get("diferenca", 0),
            "incerta": bool(r.get("contagem_incerta")),
            "peso_total_g": r.get("peso_total_g"),
            "peso_unit_g": r.get("peso_unit_g"),
            "metodo": r.get("metodo_peso_unit", ""),
            "balanca": r.get("balanca", ""),
            "id": r.get("id", id_),
        })
    df = pd.DataFrame(linhas, columns=COLUNAS_CONTAGENS)
    if df.empty:
        return df
    df["quando"] = pd.to_datetime(df["quando"], utc=True).dt.tz_convert(FUSO)
    return df.sort_values("quando", ascending=False, na_position="last").reset_index(drop=True)


def estoque_df(produtos):
    linhas = []
    for codigo, p in (produtos or {}).items():
        atual = p.get("estoque_atual", 0) or 0
        minimo = p.get("estoque_minimo", 0) or 0
        linhas.append({"codigo": codigo, "nome": p.get("nome", codigo),
                       "estoque_atual": atual, "estoque_minimo": minimo,
                       "peso_unit_g": p.get("peso_unit_g"),
                       "situacao": "Abaixo do mínimo" if atual < minimo else "OK"})
    df = pd.DataFrame(linhas, columns=["codigo", "nome", "estoque_atual", "estoque_minimo",
                                       "peso_unit_g", "situacao"])
    return df.sort_values(["situacao", "codigo"]).reset_index(drop=True)


def status_esp32(dispositivo, agora_s=None):
    """Situacao da ESP32 a partir de dispositivos/<id>."""
    agora_s = agora_s if agora_s is not None else time.time()
    d = dispositivo or {}
    contato = d.get("ultimo_contato")
    if not isinstance(contato, (int, float)):
        return {"online": False, "segundos": None, "fila": d.get("fila"), "rssi": None, "fw": d.get("fw")}
    segundos = max(0, agora_s - contato / 1000)
    return {"online": segundos <= ESP32_OFFLINE_APOS_S, "segundos": segundos,
            "fila": d.get("fila", 0), "rssi": d.get("rssi"), "fw": d.get("fw")}


def do_dia(df, dia):
    """Contagens de um dia (dia = date, no fuso de Sao Paulo)."""
    if df.empty:
        return df
    return df[df["quando"].dt.date == dia]


RESULTADOS = ["OK", "FALTA", "SOBRA"]


def contagens_por_dia(df, hoje, dias=7):
    """Tabela dia x resultado com os ultimos `dias` dias (dias sem contagem = 0)."""
    from datetime import timedelta
    rotulos = [(hoje - timedelta(days=i)).strftime("%d/%m") for i in range(dias - 1, -1, -1)]
    tabela = pd.DataFrame(0, index=rotulos, columns=RESULTADOS)
    if not df.empty:
        recentes = df[df["quando"].dt.date >= hoje - timedelta(days=dias - 1)]
        contagem = recentes.groupby([recentes["quando"].dt.strftime("%d/%m"), "resultado"]).size()
        for (dia, resultado), n in contagem.items():
            if dia in tabela.index and resultado in tabela.columns:
                tabela.loc[dia, resultado] = n
    tabela.index.name = "dia"
    return tabela


def divergencias(df):
    return df[df["resultado"].isin(["FALTA", "SOBRA"])] if not df.empty else df


def pedidos_pendentes(pedidos):
    return {k: v for k, v in (pedidos or {}).items() if v.get("status", "pendente") == "pendente"}


PROIBIDOS_NA_CHAVE = set(".#$[]/")


def chave_valida(chave):
    """O Firebase nao aceita . # $ [ ] / nas chaves (codigo de produto, id de pedido)."""
    return bool(chave) and chave == chave.strip() and not (set(chave) & PROIBIDOS_NA_CHAVE)


def proximo_id_pedido(pedidos, prefixo="PED"):
    """PED001, PED002... o proximo numero livre."""
    numeros = [int(k[len(prefixo):]) for k in (pedidos or {})
               if k.startswith(prefixo) and k[len(prefixo):].isdigit()]
    return "%s%03d" % (prefixo, max(numeros, default=0) + 1)


def para_excel(df):
    """Bytes de um .xlsx (o Excel nao aceita datas com fuso: vira texto legivel)."""
    copia = df.copy()
    if "quando" in copia and not copia.empty:
        copia["quando"] = copia["quando"].dt.strftime("%d/%m/%Y %H:%M:%S")
    saida = io.BytesIO()
    copia.to_excel(saida, index=False, sheet_name="contagens")
    return saida.getvalue()
