"""Dashboard da Balança Contadora (Streamlit).

Fase 4 do projeto: visão geral, estoque, auditoria e cadastros.
Para rodar no PC:  streamlit run dashboard/app.py
"""
import streamlit as st

st.set_page_config(page_title="Balança Contadora", page_icon="⚖️", layout="wide")

st.title("Balança Contadora de Peças")
st.info("Dashboard em construção (fase 4). Os dados virão do Firebase Realtime Database.")
