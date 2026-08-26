import os
import sys
from dotenv import load_dotenv

# Garante que as importações a partir da raiz do projeto funcionem
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application.use_cases import ProcessPostCareIntentUseCase

def main():
    load_dotenv()
    
    if not os.getenv("GEMINI_API_KEY"):
        print("ERRO: GEMINI_API_KEY não encontrada.")
        print("Crie um arquivo .env na raiz do projeto com GEMINI_API_KEY=sua_chave")
        return

    print("Iniciando o caso de uso...")
    try:
        use_case = ProcessPostCareIntentUseCase()
    except Exception as e:
        print(f"Erro ao inicializar UseCase: {e}")
        return

    prompt = (
        "Gera um pós atendimento pro Rex, tutor é o João. "
        "Eles precisam voltar em 7 dias pra tirar os pontos. "
        "Manda junto a receita do anti-inflamatório e diz que tá tudo bem. "
        "Pode mandar o prontuário também pra ele ter."
    )
    
    print(f"\nPrompt de entrada:\n\"{prompt}\"")
    print("\nProcessando com Gemini API...\n")
    
    try:
        result = use_case.execute(prompt)
        print("SUCESSO! Resposta estruturada:\n")
        print(result.model_dump_json(indent=4))
    except Exception as e:
        print(f"Erro durante a execução: {e}")

if __name__ == "__main__":
    main()
