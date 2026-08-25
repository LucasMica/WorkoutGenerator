import streamlit as st
import time

import pandas as pd

from basic import update_collection
from basic import generate_workout

# initial website configuration
st.set_page_config(
    page_title="Gerador de Treinos RAG", 
    page_icon="🏋️‍♂️", 
    layout="centered"
    )

st.title("Prescrição Inteligente de Treinos")
st.write("Baseado em diretrizes clínicas e literatura atualizada.")

# form on a sidebar
with st.sidebar:
    st.header("Perfil do aluno")
    
    age = st.number_input("Idade", min_value=12, max_value=100, value=45)
    
    objective = st.selectbox(
        "Objetivo Principal", 
        ["Fortalecimento", "Hipertrofia", "Emagrecimento", "Reabilitação"],
        index=None,
        placeholder="Insira o seu objetivo",
        accept_new_options=True
    )
    
    limitations = st.text_area(
        "Limitações ou Observações", 
        placeholder="Ex: Dor lombar leve, condromalácia patelar...",
        height=100
    )


    st.divider()
    if st.button("Sincronizar dados do banco", type="primary", use_container_width=True):
        with st.spinner():
            update_collection()
            st.success("Concluído")


# button to generate workout
if st.button("Gerar Treino", type="primary", use_container_width=True):

    with st.spinner("Buscando evidências no banco e montando o treino..."):
        
        time.sleep(2)
        workout_generated = generate_workout(age, objective, limitations)

    st.success("Treino gerado com sucesso!")

    exercises_list = workout_generated.get("treino", [])
        
    st.subheader("Plano de Exercícios:")

    for exercise in exercises_list:
        with st.expander(f"💪 {exercise['nome_exercicio']}", expanded=True):

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Séries:** {exercise['series']}")
            with col2:
                st.write(f"**Repetições:** {exercise['repeticoes']}")
                
            st.info(f"**Por que este exercício?** {exercise['justificativa']}")

    st.divider()

    st.subheader("Exportart dados")
    table_workout = pd.DataFrame(exercises_list)

    table_workout.rename(columns = {
        "nome_exercicio": "Exercício",
        "series": "Séries",
        "repeticoes": "Repetições",
        "justificativa": "Justificativa Clínica"
    }, inplace=True)

    st.dataframe(table_workout, use_container_width=True, hide_index=True)

    csv = table_workout.to_csv(index=False, sep=";").encode('utf-8-sig')

    st.download_button(
        label="Baixar planilha de treino",
        data=csv,
        file_name=f"prescricao_{objective.lower()}.csv",
        mime="text/csv",
        type="primary"
    )
