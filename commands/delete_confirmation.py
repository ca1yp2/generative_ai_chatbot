from database import (
    clear_messages,
    clear_memories,
    delete_memory,
    delete_chat_session,
    get_current_session_id,
    get_latest_chat_session_id,
    set_current_session_id
)


pending_delete_command = None
pending_delete_target = None


def set_pending_delete(command, target=None):
    global pending_delete_command, pending_delete_target

    pending_delete_command = command
    pending_delete_target = target


def handle_delete_confirmation(normalized_input):
    global pending_delete_command, pending_delete_target

    # 삭제 대기 상태가 아니면 처리하지 않음
    if pending_delete_command is None:
        return False

    # 삭제 확인
    if normalized_input == "확인":
        if pending_delete_command == "대화삭제":
            clear_messages()
            print("AI: 저장된 모든 대화 세션과 대화 기록을 삭제했습니다.\n")

        elif pending_delete_command == "기억전체삭제":
            clear_memories()
            print("AI: 모든 장기 기억을 삭제했습니다.\n")

        elif pending_delete_command == "대화삭제세션":
            session_id = pending_delete_target

            current_session_id = get_current_session_id()
            success = delete_chat_session(session_id)

            if not success:
                print(f"세션 {session_id}을(를) 찾을 수 없습니다.")

            elif current_session_id == session_id:
                latest_session_id = get_latest_chat_session_id()

                if latest_session_id is not None:
                    set_current_session_id(latest_session_id)

                    print(
                        f"세션 {session_id}을(를) 삭제했습니다. "
                        f"세션 {latest_session_id}로 이동했습니다."
                    )

                else:
                    print(
                        f"세션 {session_id}을(를) 삭제했습니다. "
                        "남아 있는 대화 세션이 없습니다."
                    )

            else:
                print(f"세션 {session_id}을(를) 삭제했습니다.")

        elif pending_delete_command == "기억삭제":
            key = pending_delete_target

            deleted_count = delete_memory(key)

            if deleted_count > 0:
                print(f"AI: '{key}' 기억을 삭제했습니다.\n")

            else:
                print(f"AI: '{key}'에 해당하는 기억을 찾지 못했습니다.\n")

        pending_delete_command = None
        pending_delete_target = None

        return True

    # 삭제 취소
    if normalized_input == "취소":
        pending_delete_command = None
        pending_delete_target = None

        print("삭제를 취소했습니다.")

        return True

    # 삭제 확인 대기 중 다른 입력이 들어온 경우
    print("삭제하려면 '확인'을, 취소하려면 '취소'를 입력해주세요.")

    return True