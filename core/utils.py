import re
from datetime import datetime

def extract_hash_content(command):
    match = re.search(r"#(.+?)#", command)
    if not match:
        return None
    raw = match.group(1).strip()
    return raw if raw else None

def parse_memory_command(command: str):
    # Extrai conteúdo entre #
    match = re.search(r"#(.+?)#", command)
    if not match:
        return None
    
    raw = match.group(1).strip()
    if not raw:  # nada entre ##
        return None
    
    parts = raw.split("/")
    
    texto = parts[0].strip()
    categoria = "GERAL" if len(parts) == 1 else parts[1].strip()
    
    # Defaults
    importancia = 5
    confidence = 1.0
    expiration = None
    
    if len(parts) >= 3:
        importancia = int(parts[2].strip())
    if len(parts) >= 4:
        confidence = float(parts[3].strip())
    if len(parts) >= 5 and parts[4].strip():
        expiration = datetime.strptime(parts[4].strip(), "%Y-%m-%d")
    
    return {
        "texto": texto,
        "categoria": categoria,
        "importancia": importancia,
        "confidence": confidence,
        "expiration": expiration
    }

def parse_edit_memory_command(command: str):
    match = re.search(r"#(.+?)#", command)
    if not match:
        return None
    
    raw = match.group(1).strip()
    if not raw:
        return None
    
    parts = raw.split("/")
    if len(parts) < 2:
        return None
    
    texto_antigo = parts[0].strip()
    texto_novo = parts[1].strip()
    nova_categoria = parts[2].strip() if len(parts) >= 3 else None
    nova_importancia = int(parts[3].strip()) if len(parts) >= 4 else None
    nova_confidence = float(parts[4].strip()) if len(parts) >= 5 else None
    
    nova_expiration = None
    if len(parts) >= 6 and parts[5].strip():
        nova_expiration = datetime.strptime(parts[5].strip(), "%Y-%m-%d")
    
    return {
        "texto_antigo": texto_antigo,
        "texto_novo": texto_novo,
        "categoria": nova_categoria,
        "importancia": nova_importancia,
        "confidence": nova_confidence,
        "expiration": nova_expiration
    }

def parse_delete_memory_command(command: str):
    match = re.search(r"#(.+?)#", command)
    if not match:
        return None
    
    texto_antigo = match.group(1).strip()
    if not texto_antigo:
        return None
    
    return {"texto_antigo": texto_antigo}
