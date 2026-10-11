import chromadb

def resetar_todas_colecoes(pasta_persistente="./vector_database"):
    
    # 1. Lista e apaga TODAS as coleções via API do ChromaDB
    try:
        client = chromadb.PersistentClient(path=pasta_persistente)
        colecoes = client.list_collections()

        if not colecoes:
            print("Nenhuma coleção foi encontrada no banco.")
        else:
            for col in colecoes:
                # Trata a variação de versão do ChromaDB (objeto Collection vs String)
                nome_colecao = col.name if hasattr(col, "name") else str(col)
                client.delete_collection(name=nome_colecao)
                print(f"Coleção '{nome_colecao}' removida com sucesso!")

    except Exception as e:
        print(f"Aviso ao acessar a lista de coleções: {e}")

if __name__ == "__main__":
    resetar_todas_colecoes()