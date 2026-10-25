import chromadb
import json
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception
from google.genai.errors import APIError

from dataLoaded import process_data, check_loaded_exercises


class WorkoutGenerationError(RuntimeError):
    pass


def deve_tentar_novamente(exception):
    if isinstance(exception, APIError):
        return exception.code == 429 or 500 <= exception.code <= 599

    return False


@retry(
    wait=wait_random_exponential(min=2, max=5),
    stop=stop_after_attempt(5),
    retry=retry_if_exception(deve_tentar_novamente),
    reraise=True
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


def _parse_workout_response(response):
    raw_text = response.text
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise WorkoutGenerationError("O Gemini retornou uma resposta vazia.")

    raw_text = raw_text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    try:
        workout_generated = json.loads(raw_text.strip())
    except json.JSONDecodeError as exc:
        raise WorkoutGenerationError("O Gemini retornou um JSON inválido.") from exc

    if not isinstance(workout_generated, dict) or not isinstance(workout_generated.get("treino"), list):
        raise WorkoutGenerationError("A resposta do Gemini não contém uma lista de exercícios válida.")

    required_fields = ("nome_exercicio", "series", "repeticoes", "instrucoes", "justificativa")
    for index, exercise in enumerate(workout_generated["treino"], start=1):
        if not isinstance(exercise, dict) or any(
            field not in exercise or exercise[field] is None for field in required_fields
        ):
            raise WorkoutGenerationError(
                f"O exercício {index} não contém todos os campos obrigatórios."
            )
        if not all(
            isinstance(exercise[field], str)
            for field in ("nome_exercicio", "instrucoes", "justificativa")
        ) or not all(
            isinstance(exercise[field], (str, int, float))
            for field in ("series", "repeticoes")
        ):
            raise WorkoutGenerationError(f"Os campos do exercício {index} têm formato inválido.")

    return workout_generated


def _generate_workout_with_fallback(client, prompt, config):
    models = ("gemini-3.8-flash", "gemini-3.6-flash")
    last_error = None

    for model_name in models:
        try:
            logging.info("Tentando gerar o treino com o modelo %s.", model_name)
            response = chamar_gemini_com_retry(client, model_name, prompt, config)
            return _parse_workout_response(response)
        except APIError as exc:
            last_error = exc
            if deve_tentar_novamente(exc) or exc.code == 404:
                logging.warning(
                    "O modelo %s falhou com erro HTTP %s; tentando o próximo modelo.",
                    model_name,
                    exc.code,
                )
                continue

            raise WorkoutGenerationError(
                f"Falha ao chamar o modelo {model_name} (HTTP {exc.code})."
            ) from exc
        except WorkoutGenerationError as exc:
            last_error = exc
            logging.warning("Resposta inválida do modelo %s: %s", model_name, exc)

    raise WorkoutGenerationError(
        "Não foi possível gerar uma lista de exercícios com os modelos configurados."
    ) from last_error


def generate_workout(age, objective, limitations, sexo):
    client_db = chromadb.PersistentClient(path="./vector_database")
    collection_articles = client_db.get_or_create_collection(name="articles")
    collection_exercises = client_db.get_or_create_collection(name="exercises")

    load_dotenv()
    client = genai.Client()

    user_age = age
    user_objetive = objective
    user_limitations = limitations
    user_sex = sexo

    pacient_profile = {
        "idade": user_age,
        "sexo": user_sex,
        "objetivo": user_objetive,
        "limitacao": user_limitations,
    }

    clinical_query = (
        f"Diretrizes clínicas, volume de treino, repetições, instruções e contraindicações "
        f"para paciente de sexo biológico {sexo}, idade {age}, com objetivo de {objective}, "
        f"considerando a limitação: {limitations}"
    )
    exercises_query = (
        f"Exercícios adequados para paciente de sexo biológico {sexo}, idade {age}, "
        f"com objetivo de {objective}, seguros para a limitação: {limitations}"
    )

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
    3. USO DO SEXO BIOLÓGICO: Considere o sexo biológico como uma característica auxiliar de contexto. Só aplique recomendações específicas por sexo quando elas estiverem apoiadas pelos documentos recuperados; se não houver evidências suficientes, não presuma diferenças nem deixe de prescrever exercícios adequados por causa do sexo.
    4. EXCLUSÃO DE ATIVIDADES GERAIS: Ignore recomendações de estilo de vida, atividades domésticas ou esportes recreativos. Prescreva APENAS exercícios físicos biomecânicos.
    5. ADAPTAÇÃO: Se o documento não especificar séries e repetições, deduza-as clinicamente com base no objetivo e idade do paciente descritos no perfil.
    6. VOLUME DA SESSÃO: Gere um treino COMPLETO contendo entre 5 e 8 exercícios variados. Selecione múltiplos movimentos diferentes do catálogo que façam sentido juntos. NUNCA retorne apenas um exercício, a menos que o catálogo restrinja severamente as opções.
    7. INSUFICIÊNCIA DE DADOS: Se o catálogo não contiver exercícios estruturados compatíveis, retorne a lista de treino vazia.

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
                "instrucoes": "string (Explique a escolha baseada APENAS no documento)",
                "justificativa": "string (Explique a escolha baseada APENAS no documento)"
            }}
        ]
    }}
    """

    # response = client.models.generate_content(
    #     model="gemini-3.7-flash",
    #     contents=prompt,
    #     config=types.GenerateContentConfig(
    #         response_mime_type="application/json",
    #         # Lower temperature, to incrise its analitcs researchs and prevent alucinations
    #         temperature=0.2,
    #     ),
    # )

    # Configuração de comportamento do modelo
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.2,
    )

    return _generate_workout_with_fallback(client, prompt, config)
