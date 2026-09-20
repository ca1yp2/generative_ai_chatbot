from config import OPENAI_MODEL
from prompts.session_prompt import SESSION_TITLE_PROMPT

def generate_session_title(client, user_input):
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=SESSION_TITLE_PROMPT,
        input=user_input
    )
    
    title = response.output_text.strip()
    
    # 여러 줄이 반환되면 첫 번째 줄만 사용
    title = title.splitlines()[0].strip()
    
    # 혹시 따옴표가 붙어 있으면 제거
    title = title.strip('"').strip("'").strip()
    
    # 빈 제목 방지
    if not title:
        return "새 대화"
    
    # 너무 긴 제목 방지
    if len(title) > 30:
        title = title[:30].rstrip()
    
    return title