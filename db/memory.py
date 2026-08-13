from .connection import cursor, db
from ollama_assistant.core.utils import *
from datetime import datetime
import re
 
def editar_memoria_por_texto(parsed):
    # 1. Buscar memórias que contenham o texto antigo
    cursor.execute("""
        SELECT id, content, category, importance, confidence, expiration_date
        FROM memory
        WHERE content ILIKE %s
        ORDER BY importance DESC
        LIMIT 1
    """, (f"%{parsed['texto_antigo']}%",))

    row = cursor.fetchone()

    if not row:
        print("⚠️ Nenhuma memória encontrada com esse texto.")
        return

    mem_id = row["id"]

    campos = []
    valores = []

    # Atualizar somente o que foi enviado
    if parsed["texto_novo"]:
        campos.append("content = %s")
        valores.append(parsed["texto_novo"])

    if parsed["categoria"]:
        campos.append("category = %s")
        valores.append(parsed["categoria"])

    if parsed["importancia"] is not None:
        campos.append("importance = %s")
        valores.append(parsed["importancia"])

    if parsed["confidence"] is not None:
        campos.append("confidence = %s")
        valores.append(parsed["confidence"])

    if parsed["expiration"] is not None:
        campos.append("expiration_date = %s")
        valores.append(parsed["expiration"])

    if not campos:
        print("⚠️ Nada para atualizar.")
        return

    valores.append(mem_id)

    sql = f"""
        UPDATE memory
        SET {", ".join(campos)}
        WHERE id = %s
    """

    cursor.execute(sql, valores)
    db.commit()

    print(f"✅ Memória atualizada (ID {mem_id})!")

def save_vector_memory_command(user_id, command, embedding):
    parsed = parse_memory_command(command)
    if not parsed:
        print("⚠️ Nenhum dado válido para salvar na memória.")
        return
    
    cursor.execute(
        """
        INSERT INTO memory (user_id, content, category, importance, confidence, embedding, expiration_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            parsed["texto"],
            parsed["categoria"],
            parsed["importancia"],
            parsed["confidence"],
            embedding,
            parsed["expiration"]
        )
    )
    db.commit()
    print(f"✅ Memória salva: {parsed['texto']} ({parsed['categoria']})")

def search_memory(user_id, embedding, categorias=None):
    query = """
        SELECT content, category, importance, confidence, embedding <-> %s::vector AS distancia
        FROM memory
        WHERE user_id = %s
          AND (expiration_date IS NULL OR expiration_date > NOW())
    """

    params = [embedding, user_id]

    if categorias:
        query += " AND category = ANY(%s)"
        params.append(categorias)

    query += " ORDER BY importance DESC, distancia ASC LIMIT 10"

    cursor.execute(query, params)
    return cursor.fetchall()

def excluir_memoria_por_texto(parsed):
    # 1. Buscar memória que contenha o texto
    cursor.execute("""
        SELECT id, content, category, importance
        FROM memory
        WHERE content LIKE %s
        ORDER BY importance DESC
        LIMIT 1
    """, (f"%{parsed['texto_antigo']}%",))

    row = cursor.fetchone()

    if not row:
        print("⚠️ Nenhuma memória encontrada com esse texto.")
        return

    mem_id = row["id"]

    # 2. Excluir
    cursor.execute("DELETE FROM memory WHERE id = %s", (mem_id,))
    db.commit()

    print(f"🗑️ Memória excluída (ID {mem_id}): {row['content']}")    


