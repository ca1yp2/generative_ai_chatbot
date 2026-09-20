from openai import OpenAI

from config import OPENAI_MODEL
from prompts.session_summary_prompt import SESSION_SUMMARY_PROMPT

client = OpenAI()

def summarize_session(messages):
    conversation = []
    
    for message in messages:
        if message["role"] == "user":
            speaker = "사용자"
        elif message["role"] == "assistant":
            speaker = "AI"
        else:
            speaker = message["role"]
            
        conversation.append(
            f"{speaker}: {message['content']}"
        )
        
    conversation_text = "\n".join(conversation)
    
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=SESSION_SUMMARY_PROMPT,
        input=conversation_text
    )
    
    return response.output_text.strip()