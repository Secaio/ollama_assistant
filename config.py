import os

BASE_DIR = os.path.expanduser("~/ollama_assistant")
API_URL = "http://localhost:11434/api/chat"
MODEL = "Makesluke"
SYSTEM_FILE = os.path.join(BASE_DIR, "assistant_system.txt")
LOG_FILE = os.path.join(BASE_DIR, "assistant.log")

HISTORY_MAX_MESSAGES = 40
MAX_TOKENS = 512
REQUEST_TIMEOUT = 120
GATILHOS = ["salve","salvar","guarde", "guardar", "lembre","lembrar", "memorize", "memorizar"]
