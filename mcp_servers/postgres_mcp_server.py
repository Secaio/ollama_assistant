import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

from mcp.server.mcpserver import MCPServer
from ollama_assistant.db.connection import db
from ollama_assistant.embeddings.generator import gerar_embedding
import sys


mcp = MCPServer(
    name="Makesluke PostgreSQL",
    version="1.0.0"
)


def get_connection():
    if db.closed:
        raise RuntimeError("Conexão PostgreSQL fechada.")
    return db


@mcp.tool()
def listar_memorias(
    user_id: str = "romeu",
    limite: int = 20
) -> list[dict]:
    """
    Lista as memórias armazenadas no PostgreSQL.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            content,
            category,
            importance,
            confidence,
            created_at,
            expiration_date
        FROM memory
        WHERE user_id = %s
        ORDER BY importance DESC, created_at DESC
        LIMIT %s
        """,
        (user_id, limite)
    )

    rows = cursor.fetchall()

    columns = [
        "id",
        "user_id",
        "content",
        "category",
        "importance",
        "confidence",
        "created_at",
        "expiration_date"
    ]

    cursor.close()

    return [
        dict(zip(columns, row))
        for row in rows
    ]


@mcp.tool()
def buscar_memoria(
    texto: str,
    user_id: str = "romeu"
) -> list[dict]:
    """
    Busca memórias pelo conteúdo usando correspondência textual.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            content,
            category,
            importance,
            confidence,
            created_at,
            expiration_date
        FROM memory
        WHERE user_id = %s
          AND content ILIKE %s
        ORDER BY importance DESC
        LIMIT 20
        """,
        (user_id, f"%{texto}%")
    )

    rows = cursor.fetchall()

    columns = [
        "id",
        "content",
        "category",
        "importance",
        "confidence",
        "created_at",
        "expiration_date"
    ]

    cursor.close()

    return [
        dict(zip(columns, row))
        for row in rows
    ]


@mcp.tool()
def buscar_memoria_semantica(
    query: str,
    user_id: str = "romeu",
    limite: int = 10
) -> list[dict]:
    """
    Busca memórias semanticamente usando embeddings e pgvector.
    """

    embedding = gerar_embedding(query)

    if not embedding:
        return [{
            "success": False,
            "error": "Não foi possível gerar o embedding da consulta."
        }]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            content,
            category,
            importance,
            confidence,
            created_at,
            expiration_date,
            embedding <-> %s::vector AS distancia
        FROM memory
        WHERE user_id = %s
          AND embedding IS NOT NULL
          AND (
              expiration_date IS NULL
              OR expiration_date > NOW()
          )
        ORDER BY embedding <-> %s::vector
        LIMIT %s
        """,
        (
            embedding,
            user_id,
            embedding,
            limite
        )
    )

    rows = cursor.fetchall()

    columns = [
        "id",
        "user_id",
        "content",
        "category",
        "importance",
        "confidence",
        "created_at",
        "expiration_date",
        "distancia"
    ]

    cursor.close()

    return [
        dict(zip(columns, row))
        for row in rows
    ]


@mcp.tool()
def obter_memoria(
    memory_id: int
) -> dict | None:
    """
    Retorna uma memória pelo ID.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            content,
            category,
            importance,
            confidence,
            created_at,
            expiration_date
        FROM memory
        WHERE id = %s
        """,
        (memory_id,)
    )

    row = cursor.fetchone()

    columns = [
        "id",
        "user_id",
        "content",
        "category",
        "importance",
        "confidence",
        "created_at",
        "expiration_date"
    ]

    cursor.close()

    if not row:
        return None

    return dict(zip(columns, row))


@mcp.tool()
def salvar_memoria(
    content: str,
    user_id: str = "romeu",
    category: str | None = None,
    importance: int = 5,
    confidence: float = 1.0
) -> dict:
    """
    Salva uma nova memória e gera automaticamente seu embedding.
    """

    embedding = gerar_embedding(content)

    if not embedding:
        return {
            "success": False,
            "message": "Não foi possível gerar o embedding da memória."
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO memory
        (
            user_id,
            content,
            category,
            importance,
            confidence,
            embedding
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            user_id,
            content,
            category,
            importance,
            confidence,
            embedding
        )
    )

    memory_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()

    return {
        "success": True,
        "id": memory_id,
        "message": "Memória salva com sucesso e embedding gerado."
    }


@mcp.tool()
def editar_memoria(
    memory_id: int,
    content: str | None = None,
    category: str | None = None,
    importance: int | None = None,
    confidence: float | None = None
) -> dict:
    """
    Edita uma memória existente.

    Se o conteúdo for alterado, um novo embedding será gerado automaticamente.
    """

    campos = []
    valores = []

    if content is not None:

        embedding = gerar_embedding(content)

        if not embedding:
            return {
                "success": False,
                "message": "Não foi possível gerar o novo embedding."
            }

        campos.append("content = %s")
        valores.append(content)

        campos.append("embedding = %s")
        valores.append(embedding)

    if category is not None:
        campos.append("category = %s")
        valores.append(category)

    if importance is not None:
        campos.append("importance = %s")
        valores.append(importance)

    if confidence is not None:
        campos.append("confidence = %s")
        valores.append(confidence)

    if not campos:
        return {
            "success": False,
            "message": "Nenhum campo para atualizar."
        }

    conn = get_connection()
    cursor = conn.cursor()

    valores.append(memory_id)

    sql = f"""
        UPDATE memory
        SET {", ".join(campos)}
        WHERE id = %s
    """

    cursor.execute(sql, valores)

    if cursor.rowcount == 0:
        cursor.close()

        return {
            "success": False,
            "message": "Memória não encontrada."
        }

    conn.commit()
    cursor.close()

    return {
        "success": True,
        "id": memory_id,
        "message": "Memória atualizada com sucesso."
    }


@mcp.tool()
def excluir_memoria(
    memory_id: int
) -> dict:
    """
    Exclui uma memória pelo ID.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM memory
        WHERE id = %s
        """,
        (memory_id,)
    )

    if cursor.rowcount == 0:
        cursor.close()

        return {
            "success": False,
            "message": "Memória não encontrada."
        }

    conn.commit()
    cursor.close()

    return {
        "success": True,
        "id": memory_id,
        "message": "Memória excluída com sucesso."
    }


@mcp.tool()
def estatisticas_memoria(
    user_id: str = "romeu"
) -> dict:
    """
    Retorna estatísticas das memórias.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*),
            COUNT(*) FILTER (
                WHERE expiration_date IS NULL
                   OR expiration_date > NOW()
            ),
            COUNT(*) FILTER (
                WHERE expiration_date IS NOT NULL
                  AND expiration_date <= NOW()
            )
        FROM memory
        WHERE user_id = %s
        """,
        (user_id,)
    )

    total, ativas, expiradas = cursor.fetchone()

    cursor.close()

    return {
        "user_id": user_id,
        "total": total,
        "ativas": ativas,
        "expiradas": expiradas
    }

@mcp.tool()
def maior_id_memoria(user_id: str = "romeu") -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT MAX(id)
        FROM memory
        WHERE user_id = %s
        """,
        (user_id,)
    )

    maior_id = cursor.fetchone()[0]
    cursor.close()

    return {
        "user_id": user_id,
        "maior_id": maior_id
    }


@mcp.tool()
def contar_memorias(user_id: str = "romeu") -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM memory
        WHERE user_id = %s
        """,
        (user_id,)
    )

    total = cursor.fetchone()[0]
    cursor.close()

    return {
        "user_id": user_id,
        "total": total
    }    


if __name__ == "__main__":
    mcp.run()