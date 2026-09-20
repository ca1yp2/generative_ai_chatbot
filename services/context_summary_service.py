from config import OPENAI_MODEL
from prompts.context_summary_prompt import CONTEXT_SUMMARY_PROMPT

def summarize_context(client, previous_summary, messages):
    conversation = []
    
    for message in messages:
        if message["role"] == "user":
            speaker = "사용자"
        elif message["role"] == "assistant":
            speaker = "AI"
        else:
            speaker = message["role"]
            
        conversation.append(f"{speaker}: {message['content']}")
    
    conversation_text = "\n".join(conversation)
    
    if previous_summary:
        input_text = f"""
[기존 대화 요약]
{previous_summary}

[새로 추가할 대화]
{conversation_text}
        """
    else:
        input_text = f"""
[새로 추가할 대화]
{conversation_text}
        """
        
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=CONTEXT_SUMMARY_PROMPT,
        input=input_text
    )
    
    return response.output_text.strip()