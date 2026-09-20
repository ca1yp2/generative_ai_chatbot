from dotenv import load_dotenv
from openai import OpenAI
from prompts.prompt import SYSTEM_PROMPT
from services.chat_service import generate_chat_response
from services.memory_service import extract_memory
from commands.command_handler import handle_command
from database import (
    init_db,
    migrate_memories,
    repair_memory_values_foreign_key,
    migrate_messages_to_sessions,
    migrate_chat_sessions_title
)

# .env 파일의 환경변수 불러오기
load_dotenv()

# OpenAI 클라이언트 생성
client = OpenAI()

# 데이터베이스 초기화
migrate_memories()
repair_memory_values_foreign_key()
init_db()
migrate_messages_to_sessions()
migrate_chat_sessions_title()

print("=" * 30)
print("Generative AI Chatbot")
print("=" * 30)
print("'도움말'          : 사용 가능한 명령어 확인")
print("'새대화'          : 새로운 대화 세션 시작")
print("'대화목록'        : 저장된 대화 세션 목록 확인")
print("'기억목록'        : 장기 기억 목록 확인")
print("'설정'            : 현재 챗봇 설정 확인")
print("'종료'            : 프로그램 종료")
print()

while True:
    user_input = input("나: ").strip()
    
    # 프로그램 종료
    if user_input == "종료":
        print("챗봇을 종료합니다.")
        break
    
    # 명령어 처리
    if handle_command(user_input):
        continue
    
    # AI 응답 생성
    ai_response = generate_chat_response(
        client,
        user_input
    )
    
    # AI 답변 출력
    print(f"AI: {ai_response}\n")
    
    # 사용자 메시지에서 장기 기억할 정보 추출
    extract_memory(
        client,
        user_input
    )