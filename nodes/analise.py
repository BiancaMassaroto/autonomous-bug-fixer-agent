import json
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from state import BugFixerState

def limpar_json_ia(texto_puro: str) -> str:
    """Remove marcações de Markdown (```json) que quebram o json.loads."""
    texto = texto_puro.strip()
    if texto.startswith("```json"):
        texto = texto[7:]
    elif texto.startswith("```"):
        texto = texto[3:]
    if texto.endswith("```"):
        texto = texto[:-3]
    return texto.strip()

# 1. Entrada (receber o Estado Global)
# No LangGraph, todo nó é uma funcao que recebe um estado atual e retorna um estado modificado
def analisar_issue_node(state: BugFixerState):
    print("--- GEMINI ANALISANDO ISSUE ---")
    
    # 3. Processamento (Configurar a LLM e dar regras estritas)
    # Inicializar Gemini
    # temperatura controla criatividade do modelo, para agentes de engenharia ou automacao queremos consistência absoluta e zero "invenção". Usamos valores próximos de 0 para que a IA seja determinista (responda quase sempre igual para o mesmo problema).
    llm = ChatGoogleGenerativeAI(
        model = "gemini-2.5-flash",
        temperature = 0.1,
        model_kwargs = {"response_format": {"type": "json_object"}}
    )
    
    # Prompt de quem é a IA 
    prompt_sistema = (
        "Você é um Engenheiro de IA sênior especialista em triagem de erros.\n"
        "Analise o título e a descrição da issue fornecida pelo usuário e identifique:\n"
        "1. O caminho exato do arquivo que contém o bug.\n"
        "2. O comando exato de terminal necessário para rodar o teste desse arquivo específico.\n\n"
        "Sua resposta deve ser estritamente um objeto JSON com as chaves 'file_path' e 'test_command'."
    )
    
    # 2. Preparação (Extrair os dados que importam)
    # define o que a IA deve fazer -> como se fosse um usuario digitando pra IA
    mensagem_usuario = f"Título: {state['issue_title']}\nDescrição: {state['issue_body']}"
    
    # ===================================================================
    # MECANISMO DE RETRY CONTRA ERRO 429 (Maturidade de Engenharia)
    # ===================================================================
    resposta = None
    for tentativa in range(3): # Tenta até 3 vezes se a Google bloquear
        try:
            resposta = llm.invoke([
                ("system", prompt_sistema),
                ("user", mensagem_usuario)
            ])
            break # Se funcionou, sai do loop de tentativas
        except Exception as error:
            if "429" in str(error) and tentativa < 2:
                print(f"   ⚠️ API da Google congestionada (429). Aguardando 15s para tentar novamente...")
                time.sleep(15)
            else:
                raise error # Se for outro erro ou estourar as 3 vezes, joga a falha na tela
    # ===================================================================
    
    try:
        # PULO DO GATO: Passamos a resposta do Gemini pela nossa limpeza
        texto_limpo = limpar_json_ia(resposta.content)
        
        dados_extraidos = json.loads(texto_limpo)
        print(f"   -> Arquivo identificado: {dados_extraidos.get('file_path')}")
        print(f"   -> Comando de teste: {dados_extraidos.get('test_command')}")
        
        # Se o estado já veio com um comando de teste predefinido (dos dados iniciais), 
        # nós mantemos ele. Caso contrário, usamos o que a IA deduziu.
        comando_final = state.get("test_command") if state.get("test_command") else dados_extraidos.get("test_command", "pytest")

        return {
            "file_path": dados_extraidos.get("file_path", "calculadora.py"),
            "test_command": comando_final,
            "iterations": 0
        }

    except Exception as e:
        print(f" Erro ao processar resposta da IA: {e}")
        # Fallback de segurança para o teste da calculadora não quebrar se o nó falhar
        return {
            "file_path": "calculadora.py",
            "test_command": "pytest test_calculadora.py",
            "iterations": 0
        }