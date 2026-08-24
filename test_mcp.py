import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def chamar_tool(session, nome, argumentos):
    result = await session.call_tool(nome, argumentos)

    if result.is_error:
        print(f"❌ Erro ao executar {nome}")
        print(result)
        return None

    if not result.content:
        print(f"⚠️ {nome} não retornou conteúdo.")
        return None

    for item in result.content:
        if hasattr(item, "text"):
            try:
                return json.loads(item.text)
            except json.JSONDecodeError:
                return item.text

    return None


async def main():

    server_params = StdioServerParameters(
        command="/home/romeu/ollama_assistant/venv/bin/python",
        args=[
            "-m",
            "ollama_assistant.mcp_servers.postgres_mcp_server"
        ],
        cwd="/home/romeu"
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            print("\n")
            print("=" * 60)
            print("MCP CONECTADO")
            print("=" * 60)

            result = await session.list_tools()

            print("\nFerramentas disponíveis:\n")

            for tool in result.tools:
                print(f"  ✓ {tool.name}")
                print(f"    {tool.description}")
                print()

            # -------------------------------------------------
            # 1. LISTAR MEMÓRIAS
            # -------------------------------------------------

            print("=" * 60)
            print("1. LISTAR MEMÓRIAS")
            print("=" * 60)

            memorias = await chamar_tool(
                session,
                "listar_memorias",
                {
                    "user_id": "romeu",
                    "limite": 5
                }
            )

            print(json.dumps(
                memorias,
                indent=2,
                ensure_ascii=False
            ))

            # -------------------------------------------------
            # 2. SALVAR MEMÓRIA
            # -------------------------------------------------

            print("\n")
            print("=" * 60)
            print("2. SALVAR MEMÓRIA + GERAR EMBEDDING")
            print("=" * 60)

            nova_memoria = await chamar_tool(
                session,
                "salvar_memoria",
                {
                    "content": "Teste de memória criado através do cliente MCP",
                    "user_id": "romeu",
                    "category": "TESTE_MCP",
                    "importance": 5,
                    "confidence": 1.0
                }
            )

            print(json.dumps(
                nova_memoria,
                indent=2,
                ensure_ascii=False
            ))

            # -------------------------------------------------
            # 3. BUSCA TEXTUAL
            # -------------------------------------------------

            print("\n")
            print("=" * 60)
            print("3. BUSCA TEXTUAL")
            print("=" * 60)

            busca = await chamar_tool(
                session,
                "buscar_memoria",
                {
                    "texto": "Teste de memória",
                    "user_id": "romeu"
                }
            )

            print(json.dumps(
                busca,
                indent=2,
                ensure_ascii=False
            ))

            # -------------------------------------------------
            # 4. BUSCA SEMÂNTICA
            # -------------------------------------------------

            print("\n")
            print("=" * 60)
            print("4. BUSCA SEMÂNTICA")
            print("=" * 60)

            semantica = await chamar_tool(
                session,
                "buscar_memoria_semantica",
                {
                    "query": "informação criada para testar a memória",
                    "user_id": "romeu",
                    "limite": 5
                }
            )

            print(json.dumps(
                semantica,
                indent=2,
                ensure_ascii=False
            ))

            # -------------------------------------------------
            # 5. ESTATÍSTICAS
            # -------------------------------------------------

            print("\n")
            print("=" * 60)
            print("5. ESTATÍSTICAS")
            print("=" * 60)

            stats = await chamar_tool(
                session,
                "estatisticas_memoria",
                {
                    "user_id": "romeu"
                }
            )

            print(json.dumps(
                stats,
                indent=2,
                ensure_ascii=False
            ))

            print("\n")
            print("=" * 60)
            print("TESTE MCP FINALIZADO")
            print("=" * 60)
            print()


if __name__ == "__main__":
    asyncio.run(main())