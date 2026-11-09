"""Visao geral: contagens e divergencias do dia, status da ESP32, ultimas operacoes."""
import pandas as pd
import streamlit as st

import dados_firebase as fb
import transformacoes as tr

ATUALIZAR_S = 5
CORES_RESULTADO = ["#2E7D32", "#C62828", "#E65100"]   # na ordem de tr.RESULTADOS: OK, FALTA, SOBRA


def pagina():
    st.title("Visão geral")
    conteudo()


@st.fragment(run_every=ATUALIZAR_S)
def conteudo():
    df = tr.contagens_df(fb.ler("contagens"))
    hoje = pd.Timestamp.now(tz=tr.FUSO).date()
    do_dia = tr.do_dia(df, hoje)
    esp = tr.status_esp32(fb.ler("dispositivos/esp32-01"))
    pendentes = tr.pedidos_pendentes(fb.ler("pedidos"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Contagens hoje", len(do_dia))
    c2.metric("Divergências hoje", len(tr.divergencias(do_dia)))
    c3.metric("Pedidos pendentes", len(pendentes))
    if esp["online"]:
        c4.metric("ESP32", "Online")
        c4.caption("fila offline: %s · sinal %s dBm" % (esp["fila"], esp["rssi"]))
    elif esp["segundos"] is None:
        c4.metric("ESP32", "Sem dados")
    else:
        c4.metric("ESP32", "Offline")
        c4.caption("último contato há %d min" % (esp["segundos"] // 60))

    st.subheader("Contagens dos últimos 7 dias")
    if df.empty:
        st.info("Nenhuma contagem ainda.")
    else:
        st.bar_chart(tr.contagens_por_dia(df, hoje), stack=True, color=CORES_RESULTADO, sort=False,
                     x_label="Dia", y_label="Contagens")

    st.subheader("Últimas operações")
    if not df.empty:
        ultimas = df.head(10)[["quando", "operador", "modo", "produto_nome", "pedido",
                               "quantidade", "resultado"]]
        st.dataframe(ultimas, hide_index=True, use_container_width=True,
                     column_config={"quando": st.column_config.DatetimeColumn("Quando", format="DD/MM HH:mm:ss"),
                                    "produto_nome": "Produto", "pedido": "Pedido",
                                    "quantidade": "Qtd", "resultado": "Resultado",
                                    "operador": "Operador", "modo": "Modo"})
    st.caption("Atualiza sozinho a cada %d s." % ATUALIZAR_S)
