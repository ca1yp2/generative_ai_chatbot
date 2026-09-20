from prompts.prompt import SYSTEM_PROMPT
from config import (
    OPENAI_MODEL,
    CONTEXT_SUMMARY_BATCH_SIZE,
    get_chat_history_limit
)
from database import (
    save_message,
    get_recent_messages,
    get_memories,
    get_current_session_id,
    get_chat_session_title,
    get_user_message_count,
    update_chat_session_title,
    get_chat_context_summary,
    update_chat_context_summary,
    get_messages_for_context_summary
)

from services.session_service import generate_session_title
from services.context_summary_service import summarize_context

def generate_chat_response(client, user_input):
    # 최근 대화 기록 불러오기
    session_id = get_current_session_id()
    history_limit = get_chat_history_limit()
    
    context_summary = None
    pending_messages = []
    messages = []
    
    if session_id is not None:
        context_data = get_chat_context_summary(session_id)
        
        if context_data:
            context_summary = context_data["summary"]
            context_summary_message_id = context_data["message_id"]
        
        else:
            context_summary_message_id = None
            
        pending_messages = get_messages_for_context_summary(
            session_id=session_id,
            recent_limit=history_limit,
            after_message_id=context_summary_message_id
        )
        
        if len(pending_messages) >= CONTEXT_SUMMARY_BATCH_SIZE:
            context_summary = summarize_context(
                client=client,
                previous_summary=context_summary,
                messages=pending_messages
            )
            
            last_message_id = pending_messages[-1]["id"]
            
            update_chat_context_summary(
                session_id=session_id,
                summary=context_summary,
                message_id=last_message_id
            )
            
            pending_messages = []
            
        recent_messages = get_recent_messages(limit=history_limit)
        
        messages = [
            {
                "role": message["role"],
                "content": message["content"]
            }
            for message in pending_messages
        ]
        
        messages.extend(recent_messages)
    
    # 장기 기억 불러오기
    memories = get_memories()
    
    # 장기 기억을 AI에게 전달할 문자열로 변환
    if memories:
        memory_text = "\n".join(
            f"- {memory['key']}: {memory['value']}"
            for memory in memories
        )
    else:
        memory_text = "저장된 장기 기억 없음"
    
    # 현재 사용자 메시지 추가
    messages.append({
        "role": "user",
        "content": user_input
    })
    
    # OpenAI API 호출
    if context_summary:
        context_summary_text = context_summary
        
    else:
        context_summary_text = "저장된 이전 대화 맥락 없음"
    
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=f"""
        {SYSTEM_PROMPT}
        
        [사용자에 대한 장기 기억]
        {memory_text}
        
        [이전 대화의 압축된 맥락]
        {context_summary_text}
        """,
        input=messages
    )
    
    # AI 답변 가져오기
    ai_response = response.output_text
    
    # 현재 대화를 데이터베이스에 저장
    save_message("user", user_input)
    
    session_id = get_current_session_id()
    
    if session_id is not None:
        title = get_chat_session_title(session_id)
        user_message_count = get_user_message_count(session_id)
        
        if not title and user_message_count == 1:
            try:
                generated_title = generate_session_title(client, user_input)
                
                update_chat_session_title(session_id, generated_title)
            
            except Exception as e:
                print(f"[Session] 자동 제목 생성 실패: {e}")
    
    save_message("assistant", ai_response)
    
    return ai_response