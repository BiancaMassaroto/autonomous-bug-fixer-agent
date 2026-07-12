import os
from github import Github
from state import BugFixerState

def criar_pr_node(state: BugFixerState):
    print("\n--- CONEXÃO COM API DO GITHUB ---")
    
    token_github = os.getenv("GITHUB_TOKEN")
    codigo_corrigido = state.get("code_correction", "")
    arquivo_alvo = state.get("file_path", "calculadora.py")
    
    repo_slug = "BiancaMassaroto/autonomous-bug-fixer-agent"
    
    if not token_github:
        print("    ❌ ERRO: GITHUB_TOKEN não encontrado no arquivo .env!")
        return {}
    
    try:
        g = Github(token_github)
        repo = g.get_repo(repo_slug)
        
        nome_branch_nova = f"fix/ai-fixing-bug-{state.get('iterations', 1)}"
        branch_principal = "main"
        
        print(f"   -> Criando branch de correção: {nome_branch_nova}...")
        sb = repo.get_branch(branch_principal)
        repo.create_git_ref(
            ref = f"refs/heads/{nome_branch_nova}",
            sha = sb.commit.sha
        )
        
        contents = repo.get_contents(arquivo_alvo, ref = nome_branch_nova)
        
        print(f"   -> Commitando as alterações da IA no arquivo: {arquivo_alvo}...")
        repo.update_file(
            path = arquivo_alvo,
            message = "fix(ai-agent): correção automática de bug via LangGraph Sandbox",
            content = codigo_corrigido,
            sha = contents.sha,
            branch = nome_branch_nova
        )
        
        print("Abrindo o Pull Request oficial no GitHub...")
        titulo_pr = "[AI] Correção automatizada de falha crítica"
        corpo_pr = (
            f"Este Pull Request foi aberto de forma 100% autônoma pelo Agente de IA.\n\n"
            f"**Problema corrigido**: Falha relatada na issue.\n"
            f"**Validação**: O código passou por verificação e teste em Sandbox Docker com sucesso.\n"
            f"**Arquivo modificado**: `{arquivo_alvo}`"
        )
        
        pr = repo.create_pull(
            title = titulo_pr,
            body = corpo_pr,
            head = nome_branch_nova,
            base = branch_principal
        )
        
        print(f"    ✅ SUCESSO TOTAL! Pull Request criado com sucesso!")
        print(f"    Link do PR: {pr.html_url}")
    except Exception as e:
        print(f"    ⚠️ Erro crítico ao interagir com a API do GitHub: {e}")
        print("    (Verifique se o seu repo_slug e o seu GITHUB_TOKEN estão corretos).")
    
    return {}