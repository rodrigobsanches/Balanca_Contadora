"""Auditoria: todas as contagens com filtros, detalhe do pedido (QR) e exportacao."""
from datetime import timedelta

import pandas as pd
import streamlit as st

import dados_firebase as fb
import transformacoes as tr

COLUNAS = {"quando": st.column_config.DatetimeColumn("Quando", format="DD/MM/YYYY HH:mm:ss"),
           "operador": "Operador", "modo": "Modo", "produto": "Código", "produto_nome": "Produto",
           "pedido": "Pedido", "quantidade": "Qtd", "esperada": "Esperada",
           "resultado": "Resultado", "diferenca": "Diferença", "incerta": "Incerta",
           "peso_total_g": "Peso (g)", "peso_unit_g": "1 peça (g)", "metodo": "Peso unit. por",
           "balanca": "Balança", "id": "ID"}


def pagina():
    st.title("Auditoria")
    if st.button("Atualizar", icon=":material/refresh:"):
        fb.limpar_cache()
    df = tr.contagens_df(fb.ler("contagens"))

    pedido_id = st.query_params.get("pedido")
    if pedido_id:
        detalhe_pedido(pedido_id, df)
        st.divider()

    if df.empty:
        st.info("Nenhuma contagem ainda.")
        return
    filtrado = filtros(df)
    st.write("%d registro(s)" % len(filtrado))
    st.dataframe(filtrado, hide_index=True, use_container_width=True, column_config=COLUNAS)
    c1, c2 = st.columns(2)
    c1.download_button("Baixar CSV", filtrado.to_csv(index=False, sep=";").encode("utf-8-sig"),
                       "contagens.csv", "text/csv", use_container_width=True)
    c2.download_button("Baixar Excel", tr.para_excel(filtrado), "contagens.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)


def filtros(df):
    hoje = pd.Timestamp.now(tz=tr.FUSO).date()
    with st.expander("Filtros", expanded=True):
        c1, c2 = st.columns(2)
        periodo = c1.date_input("Período", (hoje - timedelta(days=7), hoje), format="DD/MM/YYYY")
        modos = c2.multiselect("Modo", sorted(df["modo"].dropna().unique()))
        c3, c4, c5 = st.columns(3)
        operadores = c3.multiselect("Operador", sorted(df["operador"].dropna().unique()))
        produtos = c4.multiselect("Produto", sorted(df["produto_nome"].dropna().unique()))
        resultados = c5.multiselect("Resultado", ["OK", "FALTA", "SOBRA"])
    f = df
    if isinstance(periodo, (tuple, list)) and len(periodo) == 2:
        f = f[(f["quando"].dt.date >= periodo[0]) & (f["quando"].dt.date <= periodo[1])]
    for coluna, escolhidos in (("modo", modos), ("operador", operadores),
                               ("produto_nome", produtos), ("resultado", resultados)):
        if escolhidos:
            f = f[f[coluna].isin(escolhidos)]
    return f


def detalhe_pedido(pedido_id, df):
    pedido = fb.ler("pedidos/" + pedido_id)
    st.subheader("Pedido %s" % pedido_id)
    if not pedido:
        st.error("Pedido não encontrado.")
        return
    status = pedido.get("status", "pendente")
    (st.success if status == "conferido" else st.warning)(
        "Situação: **%s**%s" % (status, ("  ·  conferido por %s" % pedido["conferido_por"])
                                if pedido.get("conferido_por") else ""))
    st.write("Destino: %s" % pedido.get("destino", ""))
    itens = pd.DataFrame([{"Código": c, "Quantidade": v.get("qtd")}
                          for c, v in (pedido.get("itens") or {}).items()])
    st.dataframe(itens, hide_index=True)
    deste = df[df["pedido"] == pedido_id] if not df.empty else df
    st.write("Contagens deste pedido (todas, inclusive recontagens):")
    st.dataframe(deste, hide_index=True, use_container_width=True, column_config=COLUNAS)
    if st.button("Fechar detalhe"):
        del st.query_params["pedido"]
        st.rerun()
