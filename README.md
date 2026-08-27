Makesluke Assistant
📌 Sobre o projeto
Makesluke é um assistente técnico com memória semântica, desenvolvido para interagir via texto ou voz, armazenar informações relevantes do usuário, editar ou excluir memórias, e responder levando em conta o contexto salvo no banco de dados.

Ele utiliza:

Ollama para geração de respostas e embeddings

PostgreSQL + pgvector para memória vetorial

Whisper (opcional) para comandos por voz

Arquitetura modular e extensível

📁 Estrutura do Projeto
ollama_assistant/
│
├── run_assistant.py          # Entry point CLI
│
├── core/
│   ├── chat.py               # Loop principal de interação
│   ├── prompts.py            # Templates de prompt
│   └── utils.py              # Parsers e funções auxiliares
│
├── db/
│   ├── memory.py             # CRUD de memórias (save, edit, delete, search)
│   └── connection.py         # Conexão PostgreSQL
│
├── embeddings/
│   └── generator.py          # Função gerar_embedding()
│
├── config.py                 # Gatilhos e configurações gerais
│
├── requirements.txt          # Dependências
└── README.md                 # Este arquivo 

⚙️ Instalação

1. Instale dependências 
Código
pip install -r requirements.txt

2. Configure o banco PostgreSQL
Crie o banco e a tabela:
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE memory (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    importance INT DEFAULT 5,
    confidence FLOAT DEFAULT 1.0,
    embedding VECTOR(1536),
    expiration_date DATE
);

3. Configure o Ollama
Instale o Ollama e adicione o modelo Makesluke:

Código
ollama create Makesluke -f Modelfile

🚀 Como rodar
Código
makesluke

Ou:

Código
python3 run_assistant.py

Comandos de Memória
Makesluke entende comandos especiais usando #...#.

Salvar memória

Código
salve#texto/categoria/importancia/confidence/expiration#

Exemplos:

Código
salve#eu gosto de café/GOSTOS#
salve#minha cor favorita é azul/GOSTOS/10#
salve#eu gosto de basquete/GOSTOS/9/1/2026-09--01#

Se houver apenas texto → categoria = GERAL.

Se ## estiver vazio → nada é salvo.

Editar memória por texto

Código
editar#texto_antigo/texto_novo#

Exemplos:
Código
editar#eu gosto de futebo/eu gosto de futebol#
editar#Scuby é nosso gato/Scuby é o Gato de Romeu e Joseane#
Makesluke busca a memória que contém texto_antigo e atualiza.

Excluir memória por texto
Código
excluir#texto_antigo#

Exemplo:
Código
excluir#eu gosto de futebol#
Makesluke encontra a memória mais relevante e remove do banco.

🔍 Como funciona internamente

Fluxo do chat

Usuário envia texto

Gera embedding

Verifica gatilhos (salvar, editar, excluir)

Se houver comando → executa

Caso contrário → busca memórias relevantes

Monta prompt com contexto

Envia para o modelo Makesluke

Responde ao usuário

Gatilhos configurados em config.py
Código
GATILHOS = ["salve", "salvar", "guardar", "guarde", "memorize"]

Edição e exclusão usam gatilhos próprios:

Código
editar
excluir

🎤 Comandos por voz (opcional)
Se Whisper estiver habilitado, você pode falar:

“salve …”

“editar …”

“excluir …”

Makesluke converte áudio → texto → executa o comando.

📌 Objetivo do projeto

Criar um assistente técnico:

com memória vetorial real

capaz de evoluir com o usuário

modular e fácil de expandir

pronto para integrar com apps, automações e voz
