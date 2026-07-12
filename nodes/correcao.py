import json
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


def corrigir_codigo_node(state: BugFixerState):
    print("--- GEMINI APLICANDO A CORRECAO DO BUG ---")
    
    # 1. Entrada e Preparação: Resgatamos o contexto do erro vindo do Docker
    erro_terminal = state.get("terminal_output", "Nenhum erro vindo do Docker")
    caminho_arquivo = state.get("file_path", "src/codigo.py")
    tentativas_atuais = state.get("iterations", 0)
    
    # 2. Processamento e Regras Estritas: Configuramos a LLM
    # Usamos o Gemini 2.5 Pro se quisermos raciocínio lógico avançado para código,
    # mantendo a temperatura quase zerada para precisão absoluta.
    llm = ChatGoogleGenerativeAI(
        model = "gemini-2.5-flash",
        temperature = 0.05,
        model_kwargs={"response_format": {"type": "json_object"}}
    )
    
    prompt_sistema = (
        "Você é um Engenheiro de Software Sênior especialista em refatoração.\n"
        "Sua missão é analisar o erro do terminal e corrigir APENAS a função com problema.\n\n"
        "Regras estritas:\n"
        "1. Mantenha exatamente o mesmo nome da função original em português (use 'dividir').\n"
        "2. Se o segundo argumento (b) for zero, faça a função retornar o número 0 diretamente, sem levantar erros (raise).\n"
        "3. Forneça APENAS o código corrigido completo que deve substituir o arquivo original.\n"
        "4. Não inclua nenhuma explicação antes ou depois do código.\n"
        "5. Sua resposta deve ser estruturada estritamente em formato JSON com a chave 'code_correction'."
    )
    
    mensagem_usuario = (
        f"Arquivo com bug: {caminho_arquivo}\n"
        f"Erro apresentado no terminal Docker:\n{erro_terminal}\n\n"
        f"Por favor, reescreva o código corrigindo o erro acima"
    )
    
    # 3. Invocação: Enviamos o pacote para a Google
    resposta = llm.invoke([
        ("system", prompt_sistema),
        ("user", mensagem_usuario)
    ])
    
    try:
        # PULO DO GATO: Passamos a resposta de correção pela nossa limpeza também
        texto_limpo = limpar_json_ia(resposta.content)
        
        dados_extraidos = json.loads(texto_limpo)
        novo_codigo = dados_extraidos.get("code_correction", "")
        
        proxima_iteracao = tentativas_atuais + 1
        print(f"   -> Correção gerada com sucesso (Tentativa {proxima_iteracao}/5).")
        
        if novo_codigo and caminho_arquivo != "desconhecido":
            with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
                arquivo.write(novo_codigo)
            print(f"   💾 ARQUIVO REESCRITO COM SUCESSO: {caminho_arquivo}")

        return {
            "code_correction": novo_codigo,
            "iterations": proxima_iteracao
        }
        
    except Exception as e:
        print(f"    ⚠️ Erro ao processar a resposta de correção da IA: {e}")
        return {
            "iterations": tentativas_atuais + 1
        }

    
    # 4. Atualização de Segurança e Formatação do Retorno
    #try:
        #dados_extraidos = json.loads(resposta.content)
        #novo_codigo = dados_extraidos.get("code_correction", "")
        
        #proxima_iteracao = tentativas_atuais + 1
        #print(f"   -> Correção gerada com sucesso (Tentativa {proxima_iteracao}/3).")
        
        # ===================================================================
        # PULO DO GATO: Reescrever o arquivo local com a correção da IA
        # ===================================================================
        #if novo_codigo and caminho_arquivo != "desconhecido":
            #with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
                #arquivo.write(novo_codigo)
            #print(f"   💾 ARQUIVO REESCRITO COM SUCESSO: {caminho_arquivo}")
        # ===================================================================
        
        #return {
            #"code_correction": novo_codigo,
            #"iterations": proxima_iteracao
        #}
    #except Exception as e:
        #print(f"    ⚠️ Erro ao processar a resposta de correção da IA: {e}")
        #return {
            #"iterations": tentativas_atuais + 1
        #}