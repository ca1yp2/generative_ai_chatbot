import json
import os

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
SETTINGS_FILE = Path("settings.json")

def load_settings():
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8")as file:
            data = json.load(file)
            
        if not isinstance(data, dict):
            return {}
        
        return data
    
    except FileNotFoundError:
        return {}
    
    except json.JSONDecodeError:
        print("settings.json 파일 형식이 올바르지 않아 기본 설정을 사용합니다.")
        return {}
    
    except OSError as error:
        print(f"설정 파일을 읽는 중 오류가 발생했습니다: {error}")
        return {}
    
def save_settings():
    settings = {
        "chat_history_limit": CHAT_HISTORY_LIMIT,
        "debug_memory": DEBUG_MEMORY
    }
    
    try:
        with SETTINGS_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                settings,
                file,
                ensure_ascii=False,
                indent=2
            )
            
    except OSError as error:
        print(f"설정 파일을 저장하는 중 오류가 발생했습니다: {error}")

def get_positive_int_env(name, default):
    try:
        value = int(
            os.getenv(name, str(default))
        )
        
        if value <= 0:
            return default
        
        return value
    
    except ValueError:
        return default
    
DEFAULT_CHAT_HISTORY_LIMIT = get_positive_int_env(
    "CHAT_HISTORY_LIMIT",
    20
)

DEFAULT_DEBUG_MEMORY = (
    os.getenv("DEBUG_MEMORY", "false").lower() == "true"
)

# OpenAI 설정
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6"
)

# 내부 대화 컨텍스트 설정
CONTEXT_SUMMARY_BATCH_SIZE = 10

settings = load_settings()

CHAT_HISTORY_LIMIT = settings.get(
    "chat_history_limit",
    DEFAULT_CHAT_HISTORY_LIMIT
)

DEBUG_MEMORY = settings.get(
    "debug_memory",
    DEFAULT_DEBUG_MEMORY
)

def get_chat_history_limit():
    return CHAT_HISTORY_LIMIT

def set_chat_history_limit(value):
    global CHAT_HISTORY_LIMIT
    CHAT_HISTORY_LIMIT = value
    save_settings()

def get_debug_memory():
    return DEBUG_MEMORY

def set_debug_memory(value):
    global DEBUG_MEMORY
    DEBUG_MEMORY = value
    save_settings()