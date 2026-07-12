from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from state import BugFixerState
from nodes.analise import analisar_issue_node
from nodes.execucao import executar_teste_node
from nodes.correcao import corrigir_codigo_node
from nodes.github_pr import criar_pr_node

load_dotenv()

# 0. inicializa o Grafo utilizando a memoria construida
workflow = StateGraph(BugFixerState)

# 1. registro de todos os nodes
workflow.add_node("analisar_issue", analisar_issue_node)
workflow.add_node("executar_teste", executar_teste_node)
workflow.add_node("corrigir_codigo", corrigir_codigo_node)
#workflow.add_node("criar_pr", criar_pr_node_simulado)
workflow.add_node("criar_pr", criar_pr_node)

# 2. criar as "setas" (edges) -> relacoes entre os nodes
workflow.add_edge(START, "analisar_issue") # definir primeiro node

workflow.add_edge("analisar_issue", "executar_teste")
workflow.add_edge("corrigir_codigo", "executar_teste")
workflow.add_edge("criar_pr", END)

# 2.1 definir logica das setas condicionais
def roteador_do_teste(state: BugFixerState):
    if state["test_passed"]:
        return "ir_para_pr"
    elif state["iterations"] >= 5:
        return "desistir"
    else:
        return "tentar_corrigir"

workflow.add_conditional_edges(
    "executar_teste",
    roteador_do_teste,
    {
        "ir_para_pr": "criar_pr",
        "tentar_corrigir": "corrigir_codigo",
        "desistir": END
    }
)

# 3. compila o Grafo para transforma-lo em uma aplicacao executavel
app = workflow.compile()
print("Grafo do LangGraph compilado com sucesso!")

if __name__ == "__main__":
    dados_iniciais = {
        "issue_title": "Crash ao dividir por zero na calculadora",
        "issue_body": (
            "Quando chamo a funcao dividir no arquivo calculadora.py passando o segundo "
            "argumento como zero, o sistema quebra com ZeroDivisionError. "
            "O comportamento esperado era retornar 0. Rode o comando pytest para validar."
        ),
        "file_path": "calculadora.py", # Forçamos o caminho correto para o teste
        "test_command": "pytest teste_calculadora.py", # Forçamos o comando correto
        "terminal_output": "",
        "code_correction": "",
        "test_passed": False,
        "iterations": 0
    }
    
    print("\nInicializando agende de IA...")
    app.invoke(dados_iniciais)