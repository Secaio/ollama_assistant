import ollama, json

def gerar_embedding(texto):
    resposta = ollama.generate(
        model="Makesluke",
        prompt=f"""
Transforme o texto abaixo em um embedding numérico JSON com 1536 dimensões.
Responda SOMENTE com o JSON.

Texto:
{texto}
"""
    )
    try:
        return json.loads(resposta["response"])
    except Exception:
        return [0.0] * 1536
