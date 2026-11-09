"""Cadastros (so perfil admin): produtos, operadores (chaveiros) e pedidos."""
import pandas as pd
import streamlit as st

import dados_firebase as fb
import transformacoes as tr
from paginas.estoque import colunas_estoque


def pagina():
    if st.session_state.get("perfil") != "admin":
        st.error("Acesso só para administradores.")
        return
    st.title("Cadastros")
    aba_prod, aba_oper, aba_ped = st.tabs(["Produtos", "Operadores", "Pedidos"])
    with aba_prod:
        produtos()
    with aba_oper:
        operadores()
    with aba_ped:
        pedidos()


def _aviso_ok(texto):
    st.toast(texto, icon=":material/check_circle:")


# ---------------- produtos ----------------
def produtos():
    cadastrados = fb.ler("produtos")
    st.dataframe(tr.estoque_df(cadastrados), hide_index=True, use_container_width=True,
                 column_config=colunas_estoque())
    st.subheader("Novo produto ou alterar")
    opcoes = ["(novo)"] + sorted(cadastrados)
    escolha = st.selectbox("Produto", opcoes, key="prod_escolha")
    atual = cadastrados.get(escolha, {}) if escolha != "(novo)" else {}
    with st.form("form_produto", clear_on_submit=False):
        codigo = st.text_input("Código", value="" if escolha == "(novo)" else escolha,
                               disabled=escolha != "(novo)")
        nome = st.text_input("Nome", value=atual.get("nome", ""))
        c1, c2, c3 = st.columns(3)
        peso = c1.number_input("Peso de 1 peça (g)", min_value=0.0, step=0.1, format="%.2f",
                               value=float(atual.get("peso_unit_g") or 0.0))
        minimo = c2.number_input("Estoque mínimo", min_value=0, step=1,
                                 value=int(atual.get("estoque_minimo") or 0))
        estoque = c3.number_input("Estoque atual", min_value=0, step=1,
                                  value=int(atual.get("estoque_atual") or 0))
        salvar = st.form_submit_button("Salvar produto", type="primary")
    if salvar:
        codigo = (codigo or escolha).strip()
        if not tr.chave_valida(codigo) or not nome.strip():
            st.error("Preencha código e nome. O código não pode ter . # $ [ ] /")
            return
        dados = {"nome": nome.strip(), "estoque_minimo": minimo, "estoque_atual": estoque}
        if peso > 0:
            dados["peso_unit_g"] = round(peso, 4)
        fb.atualizar("produtos/" + codigo, dados)
        _aviso_ok("Produto %s salvo" % codigo)
        st.rerun()


# ---------------- operadores ----------------
def operadores():
    cadastrados = fb.ler("operadores")
    desconhecidos = fb.ler("rfid_desconhecidos")

    st.subheader("Chaveiros ainda não cadastrados")
    if not desconhecidos:
        st.caption("Nenhum. Encoste um chaveiro novo na balança: ele aparece aqui.")
    for uid in sorted(desconhecidos):
        c1, c2, c3 = st.columns([2, 3, 1])
        c1.code(uid)
        nome = c2.text_input("Nome", key="nome_" + uid, label_visibility="collapsed",
                             placeholder="Nome do operador")
        if c3.button("Cadastrar", key="cad_" + uid, use_container_width=True):
            if not nome.strip():
                st.error("Digite o nome.")
            else:
                fb.gravar("operadores/" + uid, {"nome": nome.strip(), "ativo": True})
                fb.apagar("rfid_desconhecidos/" + uid)
                _aviso_ok("%s cadastrado" % nome.strip())
                st.rerun()

    st.subheader("Operadores")
    if not cadastrados:
        st.caption("Nenhum operador.")
    for uid, op in sorted(cadastrados.items(), key=lambda x: x[1].get("nome", "")):
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write("**%s**" % op.get("nome", uid))
        c2.code(uid)
        ativo = op.get("ativo", True) not in (False, "false")
        if c3.button("Desativar" if ativo else "Ativar", key="atv_" + uid, use_container_width=True):
            fb.atualizar("operadores/" + uid, {"ativo": not ativo})
            st.rerun()


# ---------------- pedidos ----------------
def pedidos():
    todos = fb.ler("pedidos")
    produtos_cad = fb.ler("produtos")

    st.subheader("Pedidos")
    for pid, p in sorted(todos.items()):
        c1, c2, c3 = st.columns([2, 3, 1])
        itens = ", ".join("%s × %s" % (c, v.get("qtd")) for c, v in (p.get("itens") or {}).items())
        c1.write("**%s** · %s" % (pid, p.get("status", "pendente")))
        c2.write("%s — %s" % (p.get("destino", ""), itens))
        if p.get("status") == "conferido" and c3.button("Reabrir", key="reabrir_" + pid,
                                                         use_container_width=True,
                                                         help="Volta para pendente (útil para repetir a demo)"):
            fb.atualizar("pedidos/" + pid, {"status": "pendente"})
            st.rerun()

    st.subheader("Novo pedido")
    if not produtos_cad:
        st.info("Cadastre produtos primeiro.")
        return
    with st.form("form_pedido", clear_on_submit=True):
        c1, c2 = st.columns([1, 3])
        pid = c1.text_input("Número", value=tr.proximo_id_pedido(todos))
        destino = c2.text_input("Destino", placeholder="Ex.: Correios - SEDEX")
        nomes = {c: "%s · %s" % (c, p.get("nome", c)) for c, p in produtos_cad.items()}
        tabela = st.data_editor(
            pd.DataFrame({"produto": pd.Series(dtype="str"), "qtd": pd.Series(dtype="int")}),
            num_rows="dynamic", use_container_width=True, key="itens_novo",
            column_config={"produto": st.column_config.SelectboxColumn(
                               "Produto", options=sorted(produtos_cad), required=True,
                               help="; ".join(nomes.values())),
                           "qtd": st.column_config.NumberColumn("Quantidade", min_value=1, step=1,
                                                                required=True)})
        criar = st.form_submit_button("Criar pedido", type="primary")
    if criar:
        itens = {}
        for _, linha in tabela.dropna().iterrows():
            itens[linha["produto"]] = {"qtd": int(linha["qtd"])}
        if not tr.chave_valida(pid.strip()) or not destino.strip() or not itens:
            st.error("Preencha número, destino e pelo menos um item.")
            return
        if pid.strip() in todos:
            st.error("Já existe um pedido %s." % pid.strip())
            return
        fb.gravar("pedidos/" + pid.strip(), {"destino": destino.strip(), "status": "pendente",
                                             "itens": itens})
        _aviso_ok("Pedido %s criado" % pid.strip())
        st.rerun()
