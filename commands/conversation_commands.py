from database import (
    create_chat_session,
    get_chat_sessions,
    get_chat_session_info,
    get_session_messages,
    update_message,
    search_chat_sessions,
    get_current_session_id,
    chat_session_exists,
    set_current_session_id,
    update_chat_session_title,
    get_chat_session_summary,
    update_chat_session_summary
)

from services.session_summary_service import summarize_session
from services.session_export_service import export_session_to_markdown

from commands.delete_confirmation import set_pending_delete


def handle_conversation_command(user_input, normalized_input):
    # 새로운 대화 세션 시작
    if normalized_input == "새대화":
        session_id = create_chat_session()

        print(f"새로운 대화를 시작합니다. (세션 {session_id})")

        return True

    # 대화 세션 목록 조회
    if normalized_input == "대화목록":
        sessions = get_chat_sessions()

        if not sessions:
            print("저장된 대화 세션이 없습니다.")
            return True

        current_session_id = get_current_session_id()

        print("\n[대화 세션 목록]\n")

        for session in sessions:
            title = session["title"]

            if not title:
                title = "제목 없음"

            current_marker = ""

            if session["id"] == current_session_id:
                current_marker = " [현재]"

            print(
                f"세션 {session['id']} - {title} - "
                f"{session['created_at']} - "
                f"메시지 {session['message_count']}개"
                f"{current_marker}"
            )

        return True

    # 특정 대화 세션 정보 확인
    if normalized_input.startswith("대화정보"):
        session_id_text = normalized_input[len("대화정보"):]

        if not session_id_text:
            print("사용법: 대화정보 <session_id>")
            return True

        try:
            session_id = int(session_id_text)

            if session_id <= 0:
                raise ValueError

        except ValueError:
            print("session_id는 1 이상의 숫자로 입력해주세요.")
            return True

        session = get_chat_session_info(session_id)

        if session is None:
            print(f"세션 {session_id}을(를) 찾을 수 없습니다.")
            return True

        current_session_id = get_current_session_id()

        if session_id == current_session_id:
            is_current = "예"
        else:
            is_current = "아니오"

        title = session["title"] or "제목 없음"

        print(f"\n[세션 {session_id} 정보]\n")
        print(f"제목: {title}")
        print(f"생성 시간: {session['created_at']}")
        print(f"메시지 수: {session['message_count']}개")
        print(f"현재 세션: {is_current}")

        if session["summary"]:
            print("\n[요약]\n")
            print(session["summary"])
        else:
            print("\n요약: 저장된 요약이 없습니다.")

        print()

        return True

    # 특정 대화 세션의 대화 기록 확인
    if normalized_input.startswith("대화보기"):
        session_id_text = normalized_input[len("대화보기"):]

        if not session_id_text:
            print("사용법: 대화보기 <session_id>")
            return True

        try:
            session_id = int(session_id_text)

            if session_id <= 0:
                raise ValueError

        except ValueError:
            print("session_id는 1 이상의 숫자로 입력해주세요.")
            return True

        messages = get_session_messages(session_id)

        if messages is None:
            print(f"세션 {session_id}을(를) 찾을 수 없습니다.")
            return True

        if not messages:
            print(f"세션 {session_id}에는 저장된 대화가 없습니다.")
            return True

        print(f"\n[세션 {session_id} 대화 기록]\n")

        for message in messages:
            if message["role"] == "user":
                speaker = "나"
            elif message["role"] == "assistant":
                speaker = "AI"
            else:
                speaker = message["role"]

            print(
                f"[메시지 {message['id']}] "
                f"{speaker}: {message['content']}"
            )

        return True

    # 특정 대화 메시지 수정
    if normalized_input.startswith("대화수정"):
        command_text = user_input.strip()

        parts = command_text.split(maxsplit=3)

        if len(parts) < 4:
            print(
                "사용법: 대화수정 "
                "<session_id> <message_id> <새내용>"
            )
            return True

        try:
            session_id = int(parts[1])
            message_id = int(parts[2])

            if session_id <= 0 or message_id <= 0:
                raise ValueError

        except ValueError:
            print(
                "session_id와 message_id는 "
                "1 이상의 숫자로 입력해주세요."
            )
            return True

        new_content = parts[3].strip()

        if not new_content:
            print("새로운 메시지 내용을 입력해주세요.")
            return True

        try:
            success = update_message(
                session_id,
                message_id,
                new_content
            )

        except Exception as error:
            print(
                "대화 메시지 수정 중 오류가 발생했습니다: "
                f"{error}"
            )
            return True

        if not success:
            print(
                f"세션 {session_id}에서 메시지 "
                f"{message_id}을(를) 찾을 수 없습니다."
            )
            return True

        print(
            f"세션 {session_id}의 메시지 "
            f"{message_id}을(를) 수정했습니다."
        )

        return True

    # 대화 세션 검색
    if normalized_input.startswith("대화검색"):
        command_text = user_input.strip()
        parts = command_text.split(maxsplit=1)

        if len(parts) < 2:
            print("사용법: 대화검색 <검색어>")
            return True

        query = parts[1].strip()

        if not query:
            print("검색어를 입력해주세요.")
            return True

        sessions = search_chat_sessions(query)

        if not sessions:
            print(f"'{query}'에 대한 검색 결과가 없습니다.")
            return True

        current_session_id = get_current_session_id()

        print(f"\n[대화 검색 결과: {query}]\n")

        for session in sessions:
            title = session["title"]

            if not title:
                title = "제목 없음"

            current_marker = ""

            if session["id"] == current_session_id:
                current_marker = " [현재]"

            print(
                f"세션 {session['id']} - {title} - "
                f"{session['created_at']} - "
                f"메시지 {session['message_count']}개"
                f"{current_marker}"
            )

            matched_content = session["matched_content"]
            matched_role = session["matched_role"]

            if matched_content:
                content = " ".join(matched_content.split())

                content_lower = content.lower()
                query_lower = query.lower()

                match_index = content_lower.find(query_lower)

                preview_length = 80
                context_length = 30

                if match_index != -1:
                    start = max(
                        0,
                        match_index - context_length
                    )

                    end = min(
                        len(content),
                        match_index
                        + len(query)
                        + context_length
                    )

                    preview = content[start:end]

                    if start > 0:
                        preview = "..." + preview

                    if end < len(content):
                        preview = preview + "..."

                else:
                    preview = content[:preview_length]

                    if len(content) > preview_length:
                        preview += "..."

                role_name = (
                    "나"
                    if matched_role == "user"
                    else "AI"
                )

                print(f"  └ {role_name}: {preview}")

            else:
                print("  └ 제목에서 검색어가 일치했습니다.")

        return True

    # 특정 대화 세션으로 이동
    if normalized_input.startswith("대화이동"):
        session_id_text = normalized_input[len("대화이동"):]

        if not session_id_text:
            print("사용법: 대화이동 <session_id>")
            return True

        try:
            session_id = int(session_id_text)

            if session_id <= 0:
                raise ValueError

        except ValueError:
            print("session_id는 1 이상의 숫자로 입력해주세요.")
            return True

        if not chat_session_exists(session_id):
            print(f"세션 {session_id}을(를) 찾을 수 없습니다.")
            return True

        set_current_session_id(session_id)

        print(f"세션 {session_id}로 이동했습니다.")

        return True

    # 특정 대화 세션 제목 변경
    if normalized_input.startswith("대화제목"):
        command_text = user_input.strip()

        parts = command_text.split(maxsplit=2)

        if len(parts) < 3:
            print("사용법: 대화제목 <session_id> <제목>")
            return True

        try:
            session_id = int(parts[1])

            if session_id <= 0:
                raise ValueError

        except ValueError:
            print("session_id는 1 이상의 숫자로 입력해주세요.")
            return True

        title = parts[2].strip()

        if not title:
            print("제목을 입력해주세요.")
            return True

        success = update_chat_session_title(
            session_id,
            title
        )

        if not success:
            print(f"세션 {session_id}을(를) 찾을 수 없습니다.")
            return True

        print(
            f"세션 {session_id}의 제목을 "
            f"'{title}'(으)로 변경했습니다."
        )

        return True

    # 특정 대화 세션 요약
    if normalized_input.startswith("대화요약"):
        session_id_text = normalized_input[len("대화요약"):]

        if not session_id_text:
            print("사용법: 대화요약 <session_id>")
            return True

        try:
            session_id = int(session_id_text)

            if session_id <= 0:
                raise ValueError

        except ValueError:
            print("session_id는 1 이상의 숫자로 입력해주세요.")
            return True

        saved_summary = get_chat_session_summary(session_id)

        if saved_summary is not None:
            print(f"\n[세션 {session_id} 요약]\n")
            print(saved_summary)
            print()

            return True

        messages = get_session_messages(session_id)

        if messages is None:
            print(f"세션 {session_id}을(를) 찾을 수 없습니다.")
            return True

        if not messages:
            print(
                f"세션 {session_id}에는 "
                "요약할 대화가 없습니다."
            )
            return True

        try:
            summary = summarize_session(messages)

        except Exception as error:
            print(f"대화 요약 중 오류가 발생했습니다: {error}")
            return True

        try:
            update_chat_session_summary(
                session_id,
                summary
            )

        except Exception as error:
            print(
                "대화 요약 저장 중 오류가 발생했습니다: "
                f"{error}"
            )
            return True

        print(f"\n[세션 {session_id} 요약]\n")
        print(summary)
        print()

        return True

    # 특정 대화 세션 Markdown 내보내기
    if normalized_input.startswith("대화내보내기"):
        session_id_text = normalized_input[
            len("대화내보내기"):
        ]

        if not session_id_text:
            print("사용법: 대화내보내기 <session_id>")
            return True

        try:
            session_id = int(session_id_text)

            if session_id <= 0:
                raise ValueError

        except ValueError:
            print("session_id는 1 이상의 숫자로 입력해주세요.")
            return True

        session = get_chat_session_info(session_id)

        if session is None:
            print(f"세션 {session_id}을(를) 찾을 수 없습니다.")
            return True

        messages = get_session_messages(session_id)

        if messages is None:
            print(f"세션 {session_id}을(를) 찾을 수 없습니다.")
            return True

        try:
            file_path = export_session_to_markdown(
                session,
                messages
            )

        except Exception as error:
            print(
                "대화 내보내기 중 오류가 발생했습니다: "
                f"{error}"
            )
            return True

        print(
            f"세션 {session_id}을(를) "
            "Markdown 파일로 내보냈습니다."
        )
        print(f"파일 위치: {file_path}")

        return True

    # 특정 대화 세션 삭제
    if (
        normalized_input.startswith("대화삭제")
        and normalized_input != "대화삭제"
    ):
        session_id_text = normalized_input[
            len("대화삭제"):
        ]

        if not session_id_text:
            print("사용법: 대화삭제 <session_id>")
            return True

        try:
            session_id = int(session_id_text)

            if session_id <= 0:
                raise ValueError

        except ValueError:
            print("session_id는 1 이상의 숫자로 입력해주세요.")
            return True

        if not chat_session_exists(session_id):
            print(f"세션 {session_id}을(를) 찾을 수 없습니다.")
            return True

        set_pending_delete(
            "대화삭제세션",
            session_id
        )

        print(
            f"정말 세션 {session_id}을(를) "
            "삭제하시겠습니까?"
        )
        print(
            "삭제하려면 '확인'을, "
            "취소하려면 '취소'를 입력해주세요."
        )

        return True

    # 모든 대화 세션과 대화 기록 삭제
    if normalized_input == "대화삭제":
        set_pending_delete("대화삭제")

        print(
            "정말 모든 대화 세션과 "
            "대화 기록을 삭제하시겠습니까?"
        )
        print(
            "삭제하려면 '확인'을, "
            "취소하려면 '취소'를 입력해주세요."
        )

        return True

    return False