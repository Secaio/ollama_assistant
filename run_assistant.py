#!/usr/bin/env python3
import requests
import json
import time
import os
import ollama
from datetime import datetime
from collections import deque
import psycopg2
from psycopg2.extras import RealDictCursor

# ============================
# CONFIGURAÇÕES
# ============================
API_URL = "http://localhost:11434/api/chat"
MODEL = "Makesluke"
BASE_DIR = os.path.expanduser("~/ollama_assistant")
SYSTEM_FILE = os.path.join(BASE_DIR, "assistant_system.txt")
LOG_FILE = os.path.join(BASE_DIR, "assistant.log")
HISTORY_MAX_MESSAGES = 40
MAX_TOKENS = 512
REQUEST_TIMEOUT = 120
gatilhos = ["salve", "guardar", "lembre", "memorize"]
history = deque(maxlen=HISTORY_MAX_MESSAGES)

# ============================
# Conexão com o banco
# ============================
def connect_db():
    conn = psycopg2.connect(
        host="localhost",
        database="makesluke_memory",
        user="makesluke",
        password="bibi",
        port=5432
    )
    return conn

db = connect_db()
cursor = db.cursor(cursor_factory=RealDictCursor)

# -----------------------------
# Carregar memória (texto)
# -----------------------------
def load_memory(user_id, limit=50):
    cursor.execute(
        """
        SELECT content, category, importance, confidence, created_at
        FROM memory
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (user_id, limit)
    )
    rows = cursor.fetchall()
    if not rows:
        return ""

    texto = []
    for r in rows:
        texto.append(
            f"[{r['created_at']}] ({r['category']}; imp={r['importance']}; conf={r['confidence']}) {r['content']}"
        )
    return "\n".join(texto)

# -----------------------------
# Salvar memória simples (KV)
# -----------------------------
def save_kv_memory(user_id, key, value, category="geral", importance=5, confidence=1.0):
    content = f"{key}: {value}"
    cursor.execute(
        """
        INSERT INTO memory (user_id, content, category, importance, confidence)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, content, category, importance, confidence)
    )
    db.commit()

# -----------------------------
# Salvar memória vetorial (embedding)
# -----------------------------
def save_vector_memory(user_id, content, embedding, category="geral", importance=5, confidence=1.0):
    # Converte lista Python → literal pgvector "[0.1,0.2,...]"
    emb_str = "[" + ",".join(map(str, embedding)) + "]"

    cursor.execute(
        """
        INSERT INTO memory (user_id, content, category, importance, confidence, embedding)
        VALUES (%s, %s, %s, %s, %s, %s::vector)
        """,
        (user_id, content, category, importance, confidence, emb_str)
    )
    db.commit()

# -----------------------------
# Busca semântica (similaridade)
# -----------------------------
def search_memory_by_embedding(embedding, user_id=None, limit=5):
    emb_str = "[" + ",".join(map(str, embedding)) + "]"

    if user_id:
        cursor.execute(
            """
            SELECT content, category, importance, confidence
            FROM memory
            WHERE user_id = %s
            ORDER BY embedding <-> %s::vector
            LIMIT %s
            """,
            (user_id, emb_str, limit)
        )
    else:
        cursor.execute(
            """
            SELECT content, category, importance, confidence
            FROM memory
            ORDER BY embedding <-> %s::vector
            LIMIT %s
            """,
            (emb_str, limit)
        )

    return cursor.fetchall()



# ============================
# CARREGA PROMPT DE SISTEMA
# ============================
with open(SYSTEM_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

memory_text = load_memory("romeu")

system_prompt = f"""
Você é Makesluke, um assistente técnico.
Criado por Romeu Cornelius Junior.

MEMÓRIA DO USUÁRIO:
{memory_text}
"""



# ============================
# LOG
# ============================
def log(msg):
    ts = datetime.now().astimezone().isoformat()
    line = f"{ts} {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def gerar_embedding(texto):
    """
    Gera embedding usando o modelo Makesluke no Ollama.
    Retorna uma lista de floats (1536 dimensões).
    """
    resposta = ollama.generate(
        model="Makesluke",
        prompt=f"""
Transforme o texto abaixo em um embedding numérico JSON com 1536 dimensões.
Responda SOMENTE com o JSON.

Texto:
{texto}
"""
    )

    # O Ollama retorna o texto bruto em resposta["response"]
    try:
        embedding = json.loads(resposta["response"])
        return embedding
    except Exception as e:
        print("Erro ao converter embedding:", e)
        return [0.0] * 1536  # fallback seguro



# ============================
# ENVIA PERGUNTA AO OLLAMA
# ============================
def ask(user_text):
    history.append({"role": "user", "content": user_text})

    payload = {
        "model": MODEL,
        "messages": list(history),
        "max_tokens": MAX_TOKENS,
        "temperature": 0.2,
        "stream": True
    }

    try:
        r = requests.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT, stream=True)
        r.raise_for_status()

        print("Maks Luke:", end=" ", flush=True)
        assistant_text = ""

        for line in r.iter_lines():
            if not line:
                continue

            try:
                data = json.loads(line.decode())
            except:
                continue

            # Conteúdo parcial
            if "message" in data and "content" in data["message"]:
                chunk = data["message"]["content"]
                assistant_text += chunk
                print(chunk, end="", flush=True)

            # Finalização
            if data.get("done"):
                print()
                break

        assistant_text = assistant_text.strip()
        if not assistant_text:
            assistant_text = "[sem resposta]"

        history.append({"role": "assistant", "content": assistant_text})

        log(f"USER: {user_text}")
        log(f"ASSISTANT: {assistant_text[:1000].replace(chr(10),' ')}")

        return assistant_text

    except Exception as e:
        err = f"Erro ao contactar o serviço local: {e}"
        log(err)
        print(err)
        return err




# ============================
# MODO INTERATIVO
# ============================
def interactive():
    print("Maks Luke pronto aqui. Digite sua pergunta: (digite 'sair' para encerrar)")
    while True:
        try:
            u = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando.")
            break

        if not u:
            continue
        if u.lower() in ("sair", "exit", "quit"):
            break
        if any(g in u.lower() for g in gatilhos):
            embedding = gerar_embedding(u)  # sua função de embeddings
            save_vector_memory("romeu", u, embedding)
            print("✅ Memória salva com embedding!")
       
        ask(u)

# ============================
# MAIN
# ============================
if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "a").close()
    interactive()
