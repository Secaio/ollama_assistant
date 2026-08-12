import ollama

def gerar_embedding(texto: str):
    try:
        resposta = ollama.embeddings(
            model="nomic-embed-text",
            prompt=texto
        )

        emb = resposta.get("embedding")

        if not emb or not isinstance(emb, list):
            raise ValueError("Embedding inválido")

        return emb

    except Exception as e:
        print("ERRO AO GERAR EMBEDDING:", e)
        return None

