"""Estoque: quantidade de cada produto, com destaque para o que esta abaixo do minimo."""
import streamlit as st

import dados_firebase as fb
import transformacoes as tr

ATUALIZAR_S = 5


def pagina():
    st.title("Estoque")
    conteudo()


def colunas_estoque():
    """Nomes das colunas da tabela de produtos (usado aqui e em Cadastros)."""
    return {"codigo": "Código", "nome": "Produto",
            "estoque_atual": st.column_config.NumberColumn("Estoque", format="%d"),
            "estoque_minimo": st.column_config.NumberColumn("Mínimo", format="%d"),
            "peso_unit_g": st.column_config.NumberColumn("Peso de 1 peça (g)", format="%.2f"),
            "situacao": "Situação"}


def _destacar(linha):
    cor = "background-color: #FDECEA; color: #B71C1C" if linha["situacao"] != "OK" else ""
    return [cor] * len(linha)


@st.fragment(run_every=ATUALIZAR_S)
def conteudo():
    df = tr.estoque_df(fb.ler("produtos"))
    if df.empty:
        st.info("Nenhum produto cadastrado.")
        return
    abaixo = df[df["situacao"] != "OK"]
    c1, c2 = st.columns(2)
    c1.metric("Produtos", len(df))
    c2.metric("Abaixo do mínimo", len(abaixo))
    if not abaixo.empty:
        st.warning("Repor: " + ", ".join("%s (%s)" % (n, c) for c, n in zip(abaixo["codigo"], abaixo["nome"])))

    st.dataframe(df.style.apply(_destacar, axis=1), hide_index=True, use_container_width=True,
                 column_config=colunas_estoque())
    st.subheader("Estoque × mínimo")
    grafico = df.set_index("nome")[["estoque_atual", "estoque_minimo"]]
    st.bar_chart(grafico.rename(columns={"estoque_atual": "Estoque", "estoque_minimo": "Mínimo"}),
                 stack=False, color=["#1565C0", "#90A4AE"], x_label="", y_label="Peças")
    st.caption("Atualiza sozinho a cada %d s." % ATUALIZAR_S)
