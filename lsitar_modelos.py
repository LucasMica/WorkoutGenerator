from google import genai
from dotenv import load_dotenv

def listar_modelos():
    load_dotenv()
    client = genai.Client()
    
    print("Modelos disponíveis para a sua chave de API:")
    print("-" * 40)
    
    # Percorre todos os modelos e imprime apenas os que geram conteúdo (texto)
    for model in client.models.list():
        if "generateContent" in model.supported_actions:
            # Pega o nome limpo, removendo o prefixo "models/" se houver
            nome_limpo = model.name.replace("models/", "")
            print(nome_limpo)

if __name__ == "__main__":
    listar_modelos()