from typing import TypedDict

# Memoria global -> o que agente precisa carregar na memoria
class BugFixerState(TypedDict):
    issue_title: str    # Titulo da issue do GitHub
    issue_body: str     # Descricao do bug
    file_path: str      # O arquivo que IA descobriu que esta com bug
    test_command: str   # O comando para rodar o teste
    terminal_output: str # O erro que o terminal Docker retornou
    code_correction: str # O código corrigido pela IA
    test_passed: bool   # Se o teste passou ou não
    iterations: int     # Contador para não entrar no loop infinito