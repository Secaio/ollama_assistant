from .connection import cursor, db

def save_vector_memory(user_id, content, embedding, category="geral", importance=5, confidence=1.0, expiration_date=None):
    if embedding is None:
        print("Embedding falhou, memória não salva.")
        return

    cursor.execute("""
        INSERT INTO memory (user_id, content, category, importance, confidence, embedding, expiration_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, content, category, importance, confidence, embedding, expiration_date))

    db.commit()

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


