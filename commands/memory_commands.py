from database import (
    get_memories,
    get_memory_values,
    search_memories
)

from commands.delete_confirmation import set_pending_delete


def handle_memory_command(normalized_input):
    # 장기 기억 목록 확인
    if normalized_input == "기억목록":
        memories = get_memories()

        if not memories:
            print("AI: 저장된 장기 기억이 없습니다.\n")

        else:
            print("AI: 저장된 장기 기억입니다.")

            for memory in memories:
                print(f"- {memory['key']}: {memory['value']}")

            print()

        return True

    # 특정 장기 기억 상세 조회
    if normalized_input.startswith("기억상세"):
        key = normalized_input[
            len("기억상세"):
        ]

        if not key:
            print("사용법: 기억상세 <key>")
            return True

        values = get_memory_values(key)

        if not values:
            print(f"'{key}'에 저장된 장기 기억이 없습니다.")
            return True

        print("\n[장기 기억 상세]")
        print(f"\nkey: {key}")
        print("\n저장된 값:")

        for index, value in enumerate(values, start=1):
            print(f"{index}. {value}")

        print()

        return True

    # 장기 기억 검색
    if normalized_input.startswith("기억검색"):
        query = normalized_input[
            len("기억검색"):
        ]

        if not query:
            print("사용법: 기억검색 <검색어>")
            return True

        results = search_memories(query)

        if not results:
            print(f"'{query}'와 일치하는 장기 기억이 없습니다.")
            return True

        print("\n[장기 기억 검색 결과]\n")

        for result in results:
            print(f"{result['key']}: {result['value']}")

        print()

        return True

    # 특정 장기 기억 삭제
    if normalized_input.startswith("기억삭제"):
        key = normalized_input[
            len("기억삭제"):
        ]

        if not key:
            print("사용법: 기억삭제 <key>")
            return True

        values = get_memory_values(key)

        if not values:
            print(f"'{key}'에 해당하는 기억을 찾지 못했습니다.")
            return True

        set_pending_delete(
            "기억삭제",
            key
        )

        print(f"정말 '{key}' 기억을 삭제하시겠습니까?")
        print("삭제하려면 '확인'을, 취소하려면 '취소'를 입력해주세요.")

        return True

    # 모든 장기 기억 삭제
    if normalized_input == "기억전체삭제":
        set_pending_delete("기억전체삭제")

        print("정말 모든 장기 기억을 삭제하시겠습니까?")
        print("삭제하려면 '확인'을, 취소하려면 '취소'를 입력해주세요.")

        return True

    return False