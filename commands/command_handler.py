from commands.settings_commands import handle_settings_command
from commands.help_commands import handle_help_command
from commands.delete_confirmation import handle_delete_confirmation
from commands.memory_commands import handle_memory_command
from commands.conversation_commands import handle_conversation_command

def handle_command(user_input):
    # 명령어 판별용으로 공백 제거
    normalized_input = "".join(user_input.split())

    # 삭제 확인 처리
    if handle_delete_confirmation(normalized_input):
        return True

    # 기본 명령어
    if handle_help_command(normalized_input):
        return True

    # 설정 명령어
    if handle_settings_command(normalized_input):
        return True
    
    # 대화 명령어
    if handle_conversation_command(user_input, normalized_input):
        return True

    # 장기 기억 명령어
    if handle_memory_command(normalized_input):
        return True
    
    return False
