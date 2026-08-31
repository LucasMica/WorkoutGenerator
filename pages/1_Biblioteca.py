import os

import streamlit as st
import time

st.set_page_config(
    page_title="Biblioteca", 
    page_icon="📚", 
    layout="centered"
    )

st.title("Adicionar documentos à biblioteca")
st.write("Página para administração dos documentos que a IA usa de referência")

destiny_folder = "./docs"

if not os.path.exists(destiny_folder):
    os.makedirs(destiny_folder)

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

uploaded_file = st.file_uploader(
    label="Insira aqui um novo documento",
    type="application/pdf",
    accept_multiple_files=True,
    key=f"uploader_{st.session_state['uploader_key']}"
)

if st.button("Inserir documentos ao banco", type="primary"):
    if uploaded_file: 
        for file in uploaded_file:
            completed_path = os.path.join(destiny_folder, file.name)

            with open(completed_path, "wb") as f:
                f.write(file.read())  

        st.session_state["uploader_key"] += 1
        st.info("Documentos adicionados")

        time.sleep(2)
        st.rerun()

    else:
        st.error("Nenhum documento inserido, insira pelo menos um para adicionar ao banco")



