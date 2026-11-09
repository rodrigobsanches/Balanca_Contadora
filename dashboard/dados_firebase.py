"""Acesso ao Firebase pelo dashboard (conta de servico, nos secrets do Streamlit).

A leitura fica em cache por alguns segundos e e COMPARTILHADA entre todos que estao
olhando: o Firebase e consultado no maximo uma vez a cada CACHE_S, nao importa quantas
pessoas abram o dashboard (fica bem dentro do plano gratuito).
"""
import firebase_admin
import streamlit as st
from firebase_admin import credentials, db

CACHE_S = 5
NOME_APP = "dashboard-balanca"


@st.cache_resource
def _app_firebase():
    cfg = st.secrets["firebase"]
    cred = credentials.Certificate(dict(cfg["conta_servico"]))
    try:
        return firebase_admin.get_app(NOME_APP)
    except ValueError:
        return firebase_admin.initialize_app(cred, {"databaseURL": cfg["database_url"]},
                                             name=NOME_APP)


@st.cache_data(ttl=CACHE_S, show_spinner=False)
def ler(caminho):
    """Le um caminho do banco (ex.: 'contagens'). Devolve {} se nao existir."""
    return db.reference(caminho, app=_app_firebase()).get() or {}


def limpar_cache():
    ler.clear()


# ---------- escrita (so a pagina Cadastros, perfil admin) ----------
def gravar(caminho, dados):
    db.reference(caminho, app=_app_firebase()).set(dados)
    limpar_cache()


def atualizar(caminho, dados):
    db.reference(caminho, app=_app_firebase()).update(dados)
    limpar_cache()


def apagar(caminho):
    db.reference(caminho, app=_app_firebase()).delete()
    limpar_cache()
