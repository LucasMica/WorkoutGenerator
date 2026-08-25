import streamlit as st
import time # Apenas para simular o tempo de carregamento

# 1. Configuração inicial da página (deve ser o primeiro comando)
st.set_page_config(page_title="Gerador de Treinos RAG", page_icon="🏋️‍♂️", layout="centered")

st.title("🏋️‍♂️ Prescrição Inteligente de Treinos")
st.write("Baseado em diretrizes clínicas e literatura atualizada.")

# 2. Criando o formulário na barra lateral (Sidebar)
with st.sidebar:
    st.header("📋 Perfil do Paciente")
    
    idade = st.number_input("Idade", min_value=12, max_value=100, value=45)
    
    objetivo = st.selectbox(
        "Objetivo Principal", 
        ["Fortalecimento", "Hipertrofia", "Emagrecimento", "Reabilitação"]
    )
    
    limitacoes = st.text_area(
        "Limitações ou Observações", 
        placeholder="Ex: Dor lombar leve, condromalácia patelar...",
        height=100
    )

# 3. O botão de ação na tela principal
if st.button("Gerar Treino", type="primary", use_container_width=True):
    
    # Tratamento caso o usuário deixe a limitação em branco
    if not limitacoes:
        limitacoes = "Nenhuma limitação relatada."
        
    # O st.spinner cria aquela animação de "Carregando..." na tela
    with st.spinner("Buscando evidências no banco e montando o treino..."):
        
        # =========================================================
        # AQUI ENTRA A MÁGICA DO SEU BACKEND (O código que já fizemos)
        # 1. Você usaria as variáveis 'objetivo' e 'limitacoes' para buscar no ChromaDB
        # 2. Pegaria o resultado e enviaria para o Gemini gerar o JSON
        # =========================================================
        
        time.sleep(2) # Pausa falsa só para simular o RAG pensando
        
        # Simulando o JSON que o Gemini te devolveria:
        treino_gerado_pelo_gemini = [
            {
                "nome_exercicio": "Prancha Isométrica",
                "series": 3,
                "repeticoes": "30 a 45 segundos",
                "justificativa": "Fortalecimento do core evitando sobrecarga discal."
            },
            {
                "nome_exercicio": "Elevação Pélvica",
                "series": 3,
                "repeticoes": "12 a 15",
                "justificativa": "Ativação de glúteos sem compressão axial da coluna lombar."
            }
        ]

    # 4. Renderizando o resultado na tela
    st.success("Treino gerado com sucesso!")
    
    st.subheader("Plano de Exercícios:")
    
    # O st.expander cria "sanfonas" clicáveis, deixando a interface limpa
    for exercicio in treino_gerado_pelo_gemini:
        with st.expander(f"💪 {exercicio['nome_exercicio']}", expanded=True):
            # Organiza Séries e Repetições lado a lado em colunas
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Séries:** {exercicio['series']}")
            with col2:
                st.write(f"**Repetições:** {exercicio['repeticoes']}")
                
            st.info(f"**Por que este exercício?** {exercicio['justificativa']}")