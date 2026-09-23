import json

from prompts.memory_prompt import MEMORY_EXTRACTION_PROMPT
from schemas.memory_schema import MEMORY_EXTRACTION_FORMAT
from config import (
    OPENAI_MODEL,
    get_debug_memory
)
from database import (
    get_memories,
    add_memory_value,
    save_memory,
    delete_memory_value
)


def extract_memory(client, user_input):
    current_memories = get_memories()
    
    if current_memories:
        memory_text = "\n".join(
            f"- {memory['key']}: {memory['value']}"
            for memory in current_memories
        )
    else:
        memory_text = "저장된 장기 기억 없음"
        
    memory_input = f"""
    [현재 저장된 장기 기억]
    {memory_text}
    
    [새 사용자 메시지]
    {user_input}
    """
    
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=MEMORY_EXTRACTION_PROMPT,
        input=memory_input,
        text=MEMORY_EXTRACTION_FORMAT
    )
    
    try:
        data = json.loads(response.output_text)
        memories = data["memories"]
        
        for memory in memories:
            operation = memory["operation"]
            key = memory["key"]
            value = memory["value"]
            
            if operation == "add":
                add_memory_value(key, value)
                
            elif operation == "update":
                save_memory(key, value)
                
            elif operation == "delete":
                delete_memory_value(key, value)
                
            # 디버그 모드일 때만 기억 변경 내용 출력
            if get_debug_memory():
                print(
                    f"[Memory] "
                    f"{operation.upper()} "
                    f"{key} = {value}"
                )
            
    except (json.JSONDecodeError, KeyError, TypeError):
        print("기억 정보를 처리하는 중 오류가 발생했습니다.")
