from .connection import cursor, db

def load_memory(user_id, limit=50):
    cursor.execute("""
        SELECT content, category, importance, confidence, created_at
        FROM memory
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (user_id, limit))
    rows = cursor.fetchall()
    return "\n".join(
        f"[{r['created_at']}] ({r['category']}; imp={r['importance']}; conf={r['confidence']}) {r['content']}"
        for r in rows
    ) if rows else ""

def save_kv_memory(user_id, key, value, category="geral", importance=5, confidence=1.0):
    content = f"{key}: {value}"
    cursor.execute("""
        INSERT INTO memory (user_id, content, category, importance, confidence)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, content, category, importance, confidence))
    db.commit()

def save_vector_memory(user_id, content, embedding, category="geral", importance=5, confidence=1.0):
    emb_str = "[" + ",".join(map(str, embedding)) + "]"
    cursor.execute("""
        INSERT INTO memory (user_id, content, category, importance, confidence, embedding)
        VALUES (%s, %s, %s, %s, %s, %s::vector)
    """, (user_id, content, category, importance, confidence, emb_str))
    db.commit()

def search_memory_by_embedding(embedding, user_id=None, limit=5):
    emb_str = "[" + ",".join(map(str, embedding)) + "]"
    if user_id:
        cursor.execute("""
            SELECT content, category, importance, confidence
            FROM memory
            WHERE user_id = %s
            ORDER BY embedding <-> %s::vector
            LIMIT %s
        """, (user_id, emb_str, limit))
    else:
        cursor.execute("""
            SELECT content, category, importance, confidence
            FROM memory
            ORDER BY embedding <-> %s::vector
            LIMIT %s
        """, (emb_str, limit))
    return cursor.fetchall()
