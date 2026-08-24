import asyncio
import json
import re
import ollama

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ollama_assistant.core.prompts import montar_prompt
from ollama_assistant.core.utils import *
from ollama_assistant.config import GATILHOS


MCP_SERVER = "/home/romeu/ollama_assistant/mcp_servers/postgres_mcp_server.py"
PYTHON_VENV = "/home/romeu/ollama_assistant/venv/bin/python"

# MCP
def extrair_resultado(result):
    """
    Extrai o resultado retornado pelo MCP.
    """
    if hasattr(result, "structured_content") and result.structured_content:

        data = result.structured_content.get("result")

        if data is not None:
            return data

    if hasattr(result, "content") and result.content:

        textos = []

        for item in result.content:

            if hasattr(item, "text"):
                textos.append(item.text)

        if len(textos) == 1:

            try:
                return json.loads(textos[0])

            except Exception:
                return textos[0]

        return textos

    return None


async def chamar_mcp(session, ferramenta, argumentos=None):

    if argumentos is None:
        argumentos = {}
    try:
        result = await session.call_tool(
            ferramenta,
            argumentos
        )
        if getattr(result, "is_error", False):

            print(
                f"⚠️ Erro MCP em {ferramenta}:"
            )

            print(
                extrair_resultado(result)
            )

            return None

        return extrair_resultado(result)

    except Exception as e:

        print(
            f"⚠️ Erro ao chamar MCP "
            f"({ferramenta}): {e}"
        )

        return None


# ============================================================
# INPUT
# ============================================================

def ler_input():

    """
    Lê a entrada do terminal fora do event loop.

    Isso evita conflitos entre input()
    e MCP/AnyIO.
    """

    try:

        return input("Você: ").strip()

    except UnicodeDecodeError:

        print(
            "⚠️ Erro de codificação na entrada."
        )

        return ""

    except (KeyboardInterrupt, EOFError):

        raise


# ============================================================
# EXTRAIR ID DE MEMÓRIA
# ============================================================

def extrair_id_memoria(texto):
    """
    Detecta consultas explícitas de memória por ID.

    Exemplos:

    memória com id 15
    memória id: 15
    memória ID 15
    mostre a memória com id: 15
    mostrar memória 15
    """

    padroes = [
        r"\bmem[oó]ria\b.*?\bid\s*[:=]?\s*(\d+)",
        r"\bid\s*[:=]\s*(\d+).*?\bmem[oó]ria\b",
        r"\bmem[oó]ria\s+(\d+)\b",
    ]

    texto_lower = texto.lower()

    for padrao in padroes:

        match = re.search(
            padrao,
            texto_lower
        )

        if match:

            return int(match.group(1))

    return None


# ============================================================
# INTERACTIVE
# ============================================================

async def interactive():

    print(
        "Makesluke pronto. Digite sua pergunta:"
    )

    server_params = StdioServerParameters(

        command=PYTHON_VENV,

        args=[
            "-m",
            "ollama_assistant.mcp_servers.postgres_mcp_server"
        ],

        cwd="/home/romeu"
    )

    async with stdio_client(
        server_params
    ) as (read, write):

        async with ClientSession(
            read,
            write
        ) as session:

            await session.initialize()

            while True:

                # ====================================================
                # INPUT
                # ====================================================

                try:

                    u = await asyncio.to_thread(
                        ler_input
                    )

                except (
                    KeyboardInterrupt,
                    EOFError
                ):

                    print()
                    break

                if not u:
                    continue

                if u.lower() == "sair":
                    break

                # ====================================================
                # 1. CONSULTA DIRETA POR ID
                # ====================================================

                memory_id = extrair_id_memoria(u)

                if memory_id is not None:

                    memoria = await chamar_mcp(

                        session,

                        "obter_memoria",

                        {
                            "memory_id": memory_id
                        }
                    )

                    print()

                    if memoria:

                        print(
                            f"Memória {memory_id}:"
                        )

                        print(
                            json.dumps(
                                memoria,
                                ensure_ascii=False,
                                indent=2,
                                default=str
                            )
                        )

                    else:

                        print(
                            f"⚠️ A memória com ID "
                            f"{memory_id} não existe."
                        )

                    continue

                # ====================================================
                # 2. SALVAR MEMÓRIA
                # ====================================================

                if (
                    any(
                        g in u.lower()
                        for g in GATILHOS
                    )
                    and "#" in u
                ):

                    parsed = parse_memory_command(u)

                    if not parsed:

                        print(
                            "⚠️ Nenhum dado válido "
                            "para salvar na memória."
                        )

                        continue

                    resultado = await chamar_mcp(

                        session,

                        "salvar_memoria",

                        {
                            "content": parsed["texto"],
                            "user_id": "romeu",
                            "category": parsed["categoria"],
                            "importance": parsed["importancia"],
                            "confidence": parsed["confidence"]
                        }
                    )

                    if resultado:

                        print(
                            f"✅ Memória salva: "
                            f"{resultado.get('id')}"
                        )

                    continue

                # ====================================================
                # 3. EDITAR MEMÓRIA
                # ====================================================

                if (
                    "editar" in u.lower()
                    and "#" in u
                ):

                    parsed = parse_edit_memory_command(u)

                    if not parsed:

                        print(
                            "⚠️ Comando inválido "
                            "para editar memória."
                        )

                        continue

                    memorias = await chamar_mcp(

                        session,

                        "buscar_memoria",

                        {
                            "texto": parsed["texto_antigo"],
                            "user_id": "romeu"
                        }
                    )

                    if not memorias:

                        print(
                            "⚠️ Nenhuma memória encontrada."
                        )

                        continue

                    if isinstance(
                        memorias,
                        dict
                    ):

                        memorias = [memorias]

                    memoria = memorias[0]

                    argumentos = {
                        "memory_id": memoria["id"]
                    }

                    if parsed.get("texto_novo"):

                        argumentos["content"] = (
                            parsed["texto_novo"]
                        )

                    if parsed.get("categoria"):

                        argumentos["category"] = (
                            parsed["categoria"]
                        )

                    if parsed.get("importancia") is not None:

                        argumentos["importance"] = (
                            parsed["importancia"]
                        )

                    if parsed.get("confidence") is not None:

                        argumentos["confidence"] = (
                            parsed["confidence"]
                        )

                    resultado = await chamar_mcp(

                        session,

                        "editar_memoria",

                        argumentos
                    )

                    if resultado:

                        print(
                            f"✅ Memória "
                            f"{memoria['id']} atualizada."
                        )

                    continue

                # ====================================================
                # 4. EXCLUIR MEMÓRIA
                # ====================================================

                if (
                    "excluir" in u.lower()
                    and "#" in u
                ):

                    parsed = parse_delete_memory_command(u)

                    if not parsed:

                        print(
                            "⚠️ Comando inválido "
                            "para excluir memória."
                        )

                        continue

                    memorias = await chamar_mcp(

                        session,

                        "buscar_memoria",

                        {
                            "texto": parsed["texto_antigo"],
                            "user_id": "romeu"
                        }
                    )

                    if not memorias:

                        print(
                            "⚠️ Nenhuma memória encontrada."
                        )

                        continue

                    if isinstance(
                        memorias,
                        dict
                    ):

                        memorias = [memorias]

                    memoria = memorias[0]

                    resultado = await chamar_mcp(

                        session,

                        "excluir_memoria",

                        {
                            "memory_id": memoria["id"]
                        }
                    )

                    if resultado:

                        print(
                            f"🗑️ Memória "
                            f"{memoria['id']} excluída."
                        )

                    continue

                # ====================================================
                # 5. BUSCA SEMÂNTICA
                # ====================================================

                memorias = await chamar_mcp(

                    session,

                    "buscar_memoria_semantica",

                    {
                        "query": u,
                        "user_id": "romeu",
                        "limite": 10
                    }
                )

                # ====================================================
                # 6. MONTAR CONTEXTO
                # ====================================================

                contexto = ""

                if memorias:

                    if isinstance(
                        memorias,
                        dict
                    ):

                        memorias = [memorias]

                    for memoria in memorias:

                        if isinstance(
                            memoria,
                            dict
                        ):

                            contexto += (

                                f"- "
                                f"{memoria.get('content', '')}"
                                f"\n"

                            )

                # ====================================================
                # 7. MONTAR PROMPT
                # ====================================================

                prompt_final = montar_prompt(
                    contexto,
                    u
                )

                # ====================================================
                # 8. MAKESLUKE
                # ====================================================

                print(
                    "Makesluke: ",
                    end="",
                    flush=True
                )

                try:

                    for chunk in ollama.generate(

                        model="Makesluke",

                        prompt=prompt_final,

                        stream=True

                    ):

                        if "response" in chunk:

                            print(

                                chunk["response"],

                                end="",

                                flush=True

                            )

                except Exception as e:

                    print(

                        f"\n⚠️ Erro ao executar "
                        f"Makesluke: {e}"

                    )

                print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        interactive()
    )