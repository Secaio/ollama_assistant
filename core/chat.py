import ollama
from ollama_assistant.embeddings.generator import gerar_embedding
from ollama_assistant.db.memory import save_vector_memory, search_memory

def montar_prompt(contexto, user_text):
    return f"""
Você é Makesluke, um assistente técnico com memória semântica.

Memórias relevantes do usuário:
{contexto}

Usuário disse:
{user_text}

Responda levando em conta as memórias acima.
"""

def interactive():
    print("Makesluke pronto. Digite sua pergunta:")

    while True:
        u = input("Você: ")

        if u.lower() == "sair":
            break

        # 1. gerar embedding da entrada
        embedding = gerar_embedding(u)

        # 2. salvar memória se o usuário pedir
        if "salve" in u.lower() or "guardar" in u.lower():
            save_vector_memory("romeu", u, embedding)
            print("Memória salva!")
            continue

        # 3. buscar memórias relevantes
        memorias = search_memory("romeu", embedding)

        contexto = ""
        for m in memorias:
            contexto += f"- {m['content']}\n"

        # 4. montar prompt final
        prompt_final = montar_prompt(contexto, u)

        # 5. chamar o modelo principal
        print("Makesluke: ", end="", flush=True)
        for chunk in ollama.generate(
            model="Makesluke",
            prompt=prompt_final,
            stream=True
        ):    
            if "response" in chunk:
                print(chunk["response"], end="", flush=True)

        print()
