import os

from cssInjector import load_css

import pymupdf
import streamlit as st
import time

st.set_page_config(
    page_title="Biblioteca", 
    page_icon="📚", 
    layout="centered"
    )

load_css("styles.css")

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

def updateFileList():
    fileList = os.listdir(destiny_folder)
    return fileList

if st.button("Inserir documentos ao banco", type="primary"):
    if uploaded_file: 
        folder_updated = False
        for file in uploaded_file:
            fileList = updateFileList()
            if file.name in fileList:
                st.info(f"Documento {file.name} já está no banco ou possui o mesmo nome")
                time.sleep(2)
            else:
                folder_updated = True
                completed_path = os.path.join(destiny_folder, file.name)
                with open(completed_path, "wb") as f:
                    f.write(file.read())  

        st.session_state["uploader_key"] += 1
        message = "Documentos adicionados" if folder_updated else "Nenhum documento novo adicionado"

        st.info(message)
        time.sleep(2)
        st.rerun()

    else:
        st.error("Nenhum documento inserido, insira pelo menos um para adicionar ao banco")
        time.sleep(2)
        st.rerun()

st.divider()
show = st.toggle("Visualizar Documentos da Biblioteca")
if show:
    st.divider()
    st.subheader("Documentos na Biblioteca")

    fileList = updateFileList()

    if not fileList:
        st.info("A biblioteca está vazia.")
    else:
        # create an box for each file
        for file in fileList:
            if file.endswith(".pdf"):
                completed_path = os.path.join(destiny_folder, file)

                col_img, col_data = st.columns([1, 4])
                
                with col_img:
                    doc = pymupdf.open(completed_path)

                    first_page = doc.load_page(0)
        
                    tumb = first_page.get_pixmap(matrix=pymupdf.Matrix(0.2, 0.2))

                    st.image(tumb.tobytes("png"), width='content')
                    
                    doc.close()
                    
                with col_data:
                    st.write(f"{file.removesuffix(".pdf")}")
                    
                    with st.popover("Deletar arquivo"):
                        st.write(f"Tem certeza de que deseja excluir o arquivo {file}?")

                        if st.button("Sim, excluir", type="primary", key=f"confirm_delete_{file}"):
                            os.remove(completed_path)
                            st.success("Documento removido do banco")
                            time.sleep(2)
                            st.rerun()
                    
                st.divider()

