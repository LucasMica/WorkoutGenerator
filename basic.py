import chromadb
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
from google.genai.errors import ServerError

from dataLoaded import process_data, check_loaded_exercises

@retry(
    wait=wait_random_exponential(min=2, max=10),
    stop=stop_after_attempt(4),
    retry=retry_if_exception_type(ServerError)
)
def chamar_gemini_com_retry(client, model_name, prompt, config):
    return client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )

def update_collection():
    check_loaded_exercises()
    process_data()


def generate_workout(age, objective, limitations):
    client_db = chromadb.PersistentClient(path="./vector_database")
    collection_articles = client_db.get_or_create_collection(name="articles")
    collection_exercises = client_db.get_or_create_collection(name="exercises")

    load_dotenv()
    client = genai.Client()

    user_age = age
    user_objetive = objective
    user_limitations = limitations

    pacient_profile = {
        "idade": user_age,
        "objetivo": user_objetive,
        "limitacao": user_limitations,
    }

    clinical_query = f"Regras, volume de treino, repetições e contraindicações para objetivo de {objective}, considerando limitação: {limitations}"
    exercises_query = f"Exercícios para {objective}, seguros para limitação: {limitations}"

    res_articles = collection_articles.query(query_texts=[clinical_query], n_results=3)
    res_exercises = collection_exercises.query(query_texts=[exercises_query], n_results=20)

    docs_clinicos = "\n\n".join(res_articles["documents"][0]) if res_articles["documents"] and res_articles["documents"][0] else "No clinical researchs"
    docs_exercicios = "\n\n".join(res_exercises["documents"][0]) if res_exercises["documents"] and res_exercises["documents"][0] else "No catologed exercises"

    documents_rag = f"--- REGRAS CLÍNICAS (Séries e Repetições) ---\n{docs_clinicos}\n\n--- CATÁLOGO DE EXERCÍCIOS (Movimentos) ---\n{docs_exercicios}"

    prompt = f"""
    Você é um sistema especialista em prescrição clínica de exercícios. Sua única função é extrair e cruzar dados paramétricos.

    Siga estas regras RIGOROSAMENTE:
    1. ZERO ALUCINAÇÃO: Escolha os movimentos EXCLUSIVAMENTE da seção "CATÁLOGO DE EXERCÍCIOS".
    2. REGRAS CLÍNICAS: Utilize a seção "REGRAS CLÍNICAS" para definir as séries, repetições e formular a justificativa técnica.
    3. EXCLUSÃO DE ATIVIDADES GERAIS: Ignore recomendações de estilo de vida, atividades domésticas ou esportes recreativos. Prescreva APENAS exercícios físicos biomecânicos.
    4. ADAPTAÇÃO: Se o documento não especificar séries e repetições, deduza-as clinicamente com base no objetivo e idade do paciente descritos no perfil.
    5. VOLUME DA SESSÃO: Gere um treino COMPLETO contendo entre 5 e 8 exercícios variados. Selecione múltiplos movimentos diferentes do catálogo que façam sentido juntos. NUNCA retorne apenas um exercício, a menos que o catálogo restrinja severamente as opções.
    6. INSUFICIÊNCIA DE DADOS: Se o catálogo não contiver exercícios estruturados compatíveis, retorne a lista de treino vazia.

    Perfil do Paciente: {pacient_profile}
    Documentos Técnicos: {documents_rag}
    
    FORMATO DE SAÍDA OBRIGATÓRIO:
    Retorne APENAS um JSON válido, seguindo o esquema abaixo. NUNCA adicione crases de formatação (```json), explicações, introduções ou qualquer texto fora das chaves.
    
    {{
        "treino": [
            {{
                "nome_exercicio": "string",
                "series": "string ou numero",
                "repeticoes": "string ou numero",
                "justificativa": "string (Explique a escolha baseada APENAS no documento)"
            }}
        ]
    }}
    """

    response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            # Lower temperature, to incrise its analitcs researchs and prevent alucinations
            temperature=0.2,
        ),
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
        return {"treino": []}
