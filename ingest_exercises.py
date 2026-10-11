import json
import chromadb
from chromadb.utils import embedding_functions

def load_exercises_chromadb(
    path_json="exercises-ptbr-full-translation.json",
    persistent_folder="./vector_database", # Alinhe com a pasta do seu app
    colection="exercises"
):
    # 1. Carrega os dados do arquivo JSON
    with open(path_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Inicializa o cliente persistente do ChromaDB
    client = chromadb.PersistentClient(path=persistent_folder)

    # Se estiver usando um modelo de embedding específico (ex: Gemini ou padrão default)
    # Aqui usamos a collection padrão; caso use LangChain/GeminiEmbeddings, alinhe a função
    collection = client.get_or_create_collection(name=colection)

    documents = []
    metadata = []
    ids = []

    for item in data:
        # Mapeamento dos campos do schema do repositório
        item_id = item.get("id")
        nome = item.get("name", "Exercício sem nome")
        forca = item.get("force", "não especificado")
        nivel = item.get("level", "não especificado")
        mecanica = item.get("mechanic", "não especificado")
        equipamento = item.get("equipment", "peso-do-corpo")
        categoria = item.get("category", "geral")
        
        # Converte listas para strings estruturadas
        musculos_principais = ", ".join(item.get("primaryMuscles", [])) or "não especificado"
        musculos_secundarios = ", ".join(item.get("secondaryMuscles", [])) or "nenhum"
        instrucoes = " ".join(item.get("instructions", [])) or "Sem instruções descritas."

        # Bloco de texto semântico otimizado para o embeddings/RAG
        conteudo_vetorial = (
            f"Exercício: {nome}\n"
            f"Categoria: {categoria} | Nível: {nivel} | Mecânica: {mecanica}\n"
            f"Tipo de Força: {forca} | Equipamento: {equipamento}\n"
            f"Músculos Principais: {musculos_principais}\n"
            f"Músculos Secundários: {musculos_secundarios}\n"
            f"Instruções e Execução: {instrucoes}"
        )

        documents.append(conteudo_vetorial)
        
        # Metadados para filtragem exata no ChromaDB
        metadata.append({
            "nome": nome,
            "equipamento": equipamento,
            "nivel": nivel,
            "categoria": categoria,
            "musculo_principal": musculos_principais,
            "origem": "exercicios-bd-ptbr"
        })
        
        # Usa o próprio ID nativo do JSON (ex: "3_4_Sit-Up") como chave primária
        ids.append(item_id)

    # 3. Processamento em lote (Batch Ingestion)
    tamanho_lote = 200
    total = len(documents)
    
    for i in range(0, total, tamanho_lote):
        fim = i + tamanho_lote
        collection.upsert(
            documents=documents[i:fim],
            metadatas=metadata[i:fim],
            ids=ids[i:fim]
        )
        print(f"Inseridos {min(fim, total)} de {total} exercícios...")

    print("Carga direta finalizada com sucesso no ChromaDB!")

if __name__ == "__main__":
    load_exercises_chromadb()