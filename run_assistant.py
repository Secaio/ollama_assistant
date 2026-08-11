import os
from config import BASE_DIR, LOG_FILE
from core.chat import interactive

if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "a").close()
    interactive()
