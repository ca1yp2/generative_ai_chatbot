from config import (
    OPENAI_MODEL,
    get_chat_history_limit,
    set_chat_history_limit,
    get_debug_memory,
    set_debug_memory
)


def handle_settings_command(normalized_input):
    # 현재 설정 확인
    if normalized_input == "설정":
        debug_status = "ON" if get_debug_memory() else "OFF"

        print("\n[현재 설정]")
        print(f"\nAI 모델: {OPENAI_MODEL}")
        print(f"최근 대화 기록: {get_chat_history_limit()}개")
        print(f"기억 디버그: {debug_status}")

        return True

    # 최근 대화 기록 개수 변경
    if normalized_input.startswith("설정대화기록"):
        value_text = normalized_input[
            len("설정대화기록"):
        ]

        if not value_text:
            print("사용법: 설정 대화기록 <개수>")
            return True

        try:
            value = int(value_text)

        except ValueError:
            print("대화 기록 개수는 숫자로 입력해주세요.")
            return True

        if value <= 0:
            print("대화 기록 개수는 1 이상이어야 합니다.")
            return True

        set_chat_history_limit(value)

        print(f"최근 대화 기록을 {value}개로 변경했습니다.")

        return True

    # 디버그 설정 ON
    if normalized_input == "설정디버그on":
        set_debug_memory(True)

        print("기억 디버그를 ON으로 변경했습니다.")
        return True

    # 디버그 설정 OFF
    if normalized_input == "설정디버그off":
        set_debug_memory(False)

        print("기억 디버그를 OFF로 변경했습니다.")
        return True

    return False