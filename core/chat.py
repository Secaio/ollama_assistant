import requests, json
from collections import deque
from datetime import datetime
from config import API_URL, MODEL, MAX_TOKENS, REQUEST_TIMEOUT, LOG_FILE, GATILHOS, HISTORY_MAX_MESSAGES
from db.memory import save_vector_memory
from embeddings.generator import gerar_embedding

history = deque(maxlen=HISTORY_MAX_MESSAGES)

def log(msg):
    ts = datetime.now().astimezone().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} {msg}\n")

def ask(user_text):
    history.append({"role": "user", "content": user_text})
    payload = {"model": MODEL, "messages": list(history), "max_tokens": MAX_TOKENS, "temperature": 0.2, "stream": True}
    try:
        r = requests.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT, stream=True)
        r.raise_for_status()
        print("Maks Luke:", end=" ", flush=True)
        assistant_text = ""
        for line in r.iter_lines():
            if not line: continue
            try: data = json.loads(line.decode())
            except: continue
            if "message" in data and "content" in data["message"]:
                chunk = data["message"]["content"]
                assistant_text += chunk
                print(chunk, end="", flush=True)
            if data.get("done"):
                print(); break
        assistant_text = assistant_text.strip() or "[sem resposta]"
        history.append({"role": "assistant", "content": assistant_text})
        log(f"USER: {user_text}")
        log(f"ASSISTANT: {assistant_text[:1000].replace(chr(10),' ')}")
        return assistant_text
    except Exception as e:
        err = f"Erro ao contactar o serviço local: {e}"
        log(err); print(err)
        return err

def interactive():
    print("Maks Luke pronto aqui. Digite sua pergunta: (digite 'sair' para encerrar)")
    while True:
        try: u = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError): print("\nEncerrando."); break
        if not u: continue
        if u.lower() in ("sair", "exit", "quit"): break
        if any(g in u.lower() for g in GATILHOS):
            embedding = gerar_embedding(u)
            save_vector_memory("romeu", u, embedding)
            print("✅ Memória salva com embedding!")
        ask(u)
