import chromadb
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

from dataLoaded import process_data

def update_collection():
    process_data()

def generate_workout(age, objective, limitations):
    client_db = chromadb.PersistentClient(path="./vector_database")
    colection = client_db.get_or_create_collection(name="articles")

    load_dotenv()
    client = genai.Client()

    user_age = age
    user_objetive = objective
    user_limitations = limitations

    pacient_profile = {
        "idade": user_age,
        "objetivo": user_objetive,
        "limitacao": user_limitations}

    query = f"Exercícios recomendados e contraindicações para {user_objetive}, considerando a(s) limitação(ões): {user_limitations}"

    results = colection.query(
        query_texts=[query],
        n_results=3
    )

    documents_rag = ""

    if results['documents'] and results['documents'][0]:
        documents_rag = "\n\n".join(results['documents'][0])

    if not documents_rag:
        documents_rag = "Source insufficient"

    prompt = f"""
    Crie uma proposta de treino baseada ESTRITAMENTE nos documentos fornecidos.
    Perfil do Paciente: {pacient_profile}
    Documentos Técnicos: {documents_rag}

    Retorne APENAS um JSON válido contendo uma lista chamada "treino", onde cada item possui os campos "nome_exercicio", "series", "repeticoes" e "justificativa". Não adicione blocos de código ou markdown.
    """

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",

            # Lower temperature, to incrise its analitcs researchs and prevent alucinations
            temperature=0.2 
        )
    )

    raw_text = response.text.strip()

    # Just cleaning the text that is generated 
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    raw_text = raw_text.strip()

    try:
        workout_generated = json.loads(raw_text)

        return workout_generated
    
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar o JSON: {e}")
        print("O que o modelo tentou devolver foi:")
        print(raw_text)