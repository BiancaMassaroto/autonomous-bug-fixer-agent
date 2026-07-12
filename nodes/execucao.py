import subprocess # permite que o script python abra um terminal oculto no sistema operacional e digite comandos nele
import os
import time
from state import BugFixerState

def executar_teste_node(state: BugFixerState):
    print("--- EXECUTANDO TESTE ---")
    
    #excluir dps do fim dos testes
    time.sleep(1.5)
    
    # Entrada e Preparação: Buscar comando gerado pelo Gemini no Nó 1
    comando_teste = state.get("test_command", "pytest") # Se o Nó 1 tiver falhado tragicamente e não tiver gerado o comando, o código adota "pytest" como padrão e continua rodando de forma segura
    diretorio_atual = os.getcwd() # Pegar o diretório atual do seu projeto para espelhar dentro do Docker
    
    print(f"   -> Subindo Container Docker Sandbox...")
    print(f"   -> Rodando: '{comando_teste}' dentro do ambiente isolado.")
    
    # Se você passar o comando como uma string única ("docker run..."), o sistema fica vulnerável a ataques de Injeção de Comando
        # Passando como lista, o sistema operacional trata cada elemento estritamente como um parâmetro isolado
    # Montando o comando Docker:
    # --rm: Apaga o container automaticamente quando ele terminar de rodar -> Containers Efêmeros
    # -v: Espelha a pasta do seu projeto dentro do container (Modo Leitura:ro para segurança extra)
    # -w: Define a pasta de trabalho dentro do Docker
    # python:3.11-slim: Imagem oficial e leve do Python
    comando_docker = [
        "docker", "run", "--rm",
        "-v", f"{diretorio_atual}:/app", # O parâmetro -v espelha os arquivos do seu computador para dentro do Docker. O sufixo :ro significa Read-Only (Apenas Leitura). Isso garante que, se a IA gerar um código malicioso que tente deletar arquivos, o Docker vai bloquear, protegendo o seu código original
        "-w", "/app",
        "python:3.11-slim",
        "sh", "-c", f"pip install -q pytest && {comando_teste}" # Abre um terminal Unix isolado dentro do Docker, instala silenciosamente (-q de quiet) a biblioteca de testes e executa o comando que o Gemini deduziu no Nó 1
    ]
    
    try:
        resultado = subprocess.run(
            comando_docker,
            capture_output=True, # Por padrão, o terminal joga os textos na tela e o Python perde essa informação. Ativando isso, o Python cria duas "aspirações" internas: resultado.stdout (tudo o que deu certo no terminal) e resultado.stderr (tudo o que deu erro)
            text=True, # Converte os bits e bytes puros do terminal em texto legível (Strings do Python).
            timeout=25
        )
        
        if resultado.returncode == 0: # qualquer programa que termina com sucesso absoluto retorna o número de status 0
            print("    ✅ SUCESSO: O código passou nos testes dentro do Docker!")
            
            return {
                "terminal_output": "All tests passed inside the Docker sandbox",
                "test_passed": True
            }
        else:
            print("    ❌ FALHA: O teste quebrou dentro do Docker. Capturando logs.")
            
            # Se o teste falhar (código diferente de 0), capturamos o erro exato do terminal (stderr) e salvamos em terminal_output
            erro = resultado.stderr if resultado.stderr else resultado.stdout
            
            # O estado test_passed vira False 
            # A beleza do LangGraph acontece aqui: o fluxo jogará essa string de erro direto na cara do Gemini no Nó 3 (Correção), dando a ele o contexto perfeito do que precisa ser consertado.
            return {
                "terminal_output": erro,
                "test_passed": False
            }
            
    except subprocess.TimeoutExpired:
        print("    ⚠️ GUARDRAIL: O container Docker demorou demais (Loop infinito detectado).")
        
        return {
            "terminal_output": "TimeoutError: Execution exceeded 25 seconds in Docker sandbox.",
            "test_passed": False
        }
        
    except Exception as e:
        print(f"    ⚠️ Erro ao tentar acionar o Docker: {e}")
        return {
            "terminal_output": f"DockerError: Failed to launch sandbox. Details: {e}",
            "test_passed": False
        }