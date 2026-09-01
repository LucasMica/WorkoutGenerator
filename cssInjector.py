import os

import streamlit as st

def load_css(file_name):
    # 1. Pega o caminho absoluto da pasta onde ESTE arquivo (cssInjector.py) está salvo
    diretorio_raiz = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Junta a raiz com o nome do arquivo CSS
    caminho_completo = os.path.join(diretorio_raiz, file_name)
    
    try:
        with open(caminho_completo, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo de estilo não encontrado no caminho: {caminho_completo}")