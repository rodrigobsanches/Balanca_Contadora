"""Dashboard da Balanca Contadora (Streamlit).

Rodar no PC:  .venv\\Scripts\\python -m streamlit run dashboard/app.py
Credenciais:  dashboard/.streamlit/secrets.toml (modelo: secrets_exemplo.toml)

So entra quem tem usuario e senha (ver autenticacao.py). Abrir com ?pedido=PED001 leva
direto ao detalhe do pedido na Auditoria (o QR code da etiqueta usa esse link).
"""
import time

import streamlit as st

from autenticacao import autenticar
from paginas import auditoria, cadastros, estoque, visao_geral

st.set_page_config(page_title="Balança Contadora", page_icon="⚖️", layout="wide")


def tela_login():
    st.title("Balança Contadora de Peças")
    st.caption("Acesso restrito. Entre com o seu usuário.")
    with st.form("login"):
        nome = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)
    if entrar:
        perfil = autenticar(st.secrets.get("usuarios", {}), nome, senha)
        if perfil:
            st.session_state["usuario"] = nome.strip().lower()
            st.session_state["perfil"] = perfil
            st.rerun()
        time.sleep(1.5)   # atrasa tentativas seguidas de adivinhar a senha
        st.error("Usuário ou senha incorretos.")


def sair():
    for chave in ("usuario", "perfil"):
        st.session_state.pop(chave, None)
    st.rerun()


CAMINHOS = ("visao-geral", "estoque", "auditoria", "cadastros")


def main():
    if not st.session_state.get("perfil"):
        # Qualquer endereco (ex.: /estoque) mostra o login; depois de entrar, a pagina
        # pedida abre normalmente. (Recarregar o navegador pede o login de novo.)
        login = [st.Page(tela_login, title="Entrar", icon=":material/lock:", default=True)]
        login += [st.Page(tela_login, title="Entrar", url_path=c) for c in CAMINHOS]
        st.navigation(login, position="hidden").run()
        return

    paginas = [
        st.Page(visao_geral.pagina, title="Visão geral", icon=":material/dashboard:",
                url_path="visao-geral", default=not st.query_params.get("pedido")),
        st.Page(estoque.pagina, title="Estoque", icon=":material/inventory_2:", url_path="estoque"),
        st.Page(auditoria.pagina, title="Auditoria", icon=":material/fact_check:",
                url_path="auditoria", default=bool(st.query_params.get("pedido"))),
    ]
    if st.session_state["perfil"] == "admin":
        paginas.append(st.Page(cadastros.pagina, title="Cadastros", icon=":material/edit:",
                               url_path="cadastros"))
    with st.sidebar:
        st.write("**%s** (%s)" % (st.session_state["usuario"], st.session_state["perfil"]))
        if st.button("Sair", icon=":material/logout:"):
            sair()
    st.navigation(paginas).run()


main()
