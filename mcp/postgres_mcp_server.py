import logging
from typing import Optional

from mcp.server.mcpserver import MCPServer

from db.connection import db


# ============================================================
# CONFIGURAÇÃO
# ============================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = MCPServer(
    name="Makesluke PostgreSQL",
    version="1.0.0"
)


# ============================================================
# CONEXÃO
# ============================================================

def verificar_conexao():
    """
    Verifica se a conexão PostgreSQL ainda está aberta.
    """
    if db.closed:
        raise RuntimeError("A conexão com PostgreSQL está fechada.")

    return db


# ============================================================
# LISTAR MEMÓRIAS
# ============================================================

@mcp.tool()
def listar_memorias(
    user_id: str = "romeu",
    limite: int = 20
) -> list[dict]:
    """
    Lista as memórias do usuário.

    Use esta ferramenta quando precisar consultar
    as memórias armazenadas no Makesluke.
    """

    conn = verificar_conexao()

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

    cursor.close()

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

    return [
        dict(zip(columns, row))
        for row in rows
    ]


# ============================================================
# BUSCAR MEMÓRIA POR TEXTO
# ============================================================

@mcp.tool()
def buscar_memoria(
    texto: str,
    user_id: str = "romeu"
) -> list[dict]:
    """
    Busca memórias pelo conteúdo textual.

    Use esta ferramenta quando precisar encontrar
    uma memória específica pelo texto.
    """

    conn = verificar_conexao()

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
        ORDER BY importance DESC, created_at DESC
        LIMIT 20
        """,
        (
            user_id,
            f"%{texto}%"
        )
    )

    rows = cursor.fetchall()

    cursor.close()

    columns = [
        "id",
        "content",
        "category",
        "importance",
        "confidence",
        "created_at",
        "expiration_date"
    ]

    return [
        dict(zip(columns, row))
        for row in rows
    ]


# ============================================================
# OBTER UMA MEMÓRIA
# ============================================================

@mcp.tool()
def obter_memoria(
    memory_id: int
) -> Optional[dict]:
    """
    Obtém uma memória específica pelo ID.
    """

    conn = verificar_conexao()

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

    cursor.close()

    if not row:
        return None

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

    return dict(zip(columns, row))


# ============================================================
# SALVAR MEMÓRIA
# ============================================================

@mcp.tool()
def salvar_memoria(
    content: str,
    user_id: str = "romeu",
    category: Optional[str] = None,
    importance: int = 5,
    confidence: float = 1.0
) -> dict:
    """
    Salva uma nova memória no PostgreSQL.

    IMPORTANTE:
    Esta ferramenta não gera embedding.
    O embedding continuará sendo responsabilidade
    do Makesluke.
    """

    conn = verificar_conexao()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO memory
        (
            user_id,
            content,
            category,
            importance,
            confidence
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            user_id,
            content,
            category,
            importance,
            confidence
        )
    )

    memory_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()

    logger.info(
        "Memória salva. ID=%s",
        memory_id
    )

    return {
        "success": True,
        "id": memory_id,
        "message": "Memória salva com sucesso."
    }


# ============================================================
# EDITAR MEMÓRIA
# ============================================================

@mcp.tool()
def editar_memoria(
    memory_id: int,
    content: Optional[str] = None,
    category: Optional[str] = None,
    importance: Optional[int] = None,
    confidence: Optional[float] = None
) -> dict:
    """
    Edita uma memória existente.

    Somente os campos enviados serão alterados.
    """

    conn = verificar_conexao()

    campos = []
    valores = []

    if content is not None:
        campos.append("content = %s")
        valores.append(content)

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
            "message": "Nenhum campo foi informado para alteração."
        }

    valores.append(memory_id)

    sql = f"""
        UPDATE memory
        SET {", ".join(campos)}
        WHERE id = %s
    """

    cursor = conn.cursor()

    cursor.execute(sql, valores)

    if cursor.rowcount == 0:
        cursor.close()

        return {
            "success": False,
            "message": f"Memória {memory_id} não encontrada."
        }

    conn.commit()

    cursor.close()

    logger.info(
        "Memória %s atualizada.",
        memory_id
    )

    return {
        "success": True,
        "id": memory_id,
        "message": "Memória atualizada com sucesso."
    }


# ============================================================
# EXCLUIR MEMÓRIA
# ============================================================

@mcp.tool()
def excluir_memoria(
    memory_id: int
) -> dict:
    """
    Exclui uma memória pelo ID.
    """

    conn = verificar_conexao()

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
            "message": f"Memória {memory_id} não encontrada."
        }

    conn.commit()

    cursor.close()

    logger.info(
        "Memória %s excluída.",
        memory_id
    )

    return {
        "success": True,
        "id": memory_id,
        "message": "Memória excluída com sucesso."
    }


# ============================================================
# ESTATÍSTICAS
# ============================================================

@mcp.tool()
def estatisticas_memoria(
    user_id: str = "romeu"
) -> dict:
    """
    Retorna estatísticas das memórias do usuário.
    """

    conn = verificar_conexao()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (
                WHERE expiration_date IS NULL
                   OR expiration_date > NOW()
            ) AS ativas,
            COUNT(*) FILTER (
                WHERE expiration_date IS NOT NULL
                  AND expiration_date <= NOW()
            ) AS expiradas
        FROM memory
        WHERE user_id = %s
        """,
        (user_id,)
    )

    row = cursor.fetchone()

    cursor.close()

    return {
        "user_id": user_id,
        "total": row[0],
        "ativas": row[1],
        "expiradas": row[2]
    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    logger.info("Makesluke PostgreSQL MCP Server iniciando...")

    mcp.run()