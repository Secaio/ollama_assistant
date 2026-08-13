import ollama
from ollama_assistant.db.memory import *
from ollama_assistant.embeddings.generator import gerar_embedding
from ollama_assistant.core.prompts import montar_prompt
from ollama_assistant.core.utils import *
from ollama_assistant.config import GATILHOS

def interactive():
    print("Makesluke pronto. Digite sua pergunta:")

    while True:
        u = input("Você: ")

        if u.lower() == "sair":
            break

        # 1. gerar embedding da entrada
        embedding = gerar_embedding(u)

        # 2. salvar memória se o usuário pedir
        if any(g in u.lower() for g in GATILHOS) and "#" in u:
            save_vector_memory_command("romeu", u, embedding)
            continue

        # 3. editar memória por texto
        if "editar" in u.lower() and "#" in u:
            parsed = parse_edit_memory_command(u) #jeito antigo funcionava
            if parsed:
                editar_memoria_por_texto(parsed)
            else:
                print("⚠️ Comando inválido para editar memória.")
            continue                
        
        # 4. excluir memória por texto
        if "excluir" in u.lower() and "#" in u:
            parsed = parse_delete_memory_command(u)
            if parsed:
                excluir_memoria_por_texto(parsed)
            else:
                print("⚠️ Comando inválido para excluir memória.")
            continue
        
        # 5. buscar memórias relevantes
        memorias = search_memory("romeu", embedding)

        contexto = ""
        for m in memorias:
            contexto += f"- {m['content']}\n"

        # 6. montar prompt final
        prompt_final = montar_prompt(contexto, u)

        # 7. chamar o modelo principal
        print("Makesluke: ", end="", flush=True)
        for chunk in ollama.generate(
            model="Makesluke",
            prompt=prompt_final,
            stream=True
        ):    
            if "response" in chunk:
                print(chunk["response"], end="", flush=True)

        print()
