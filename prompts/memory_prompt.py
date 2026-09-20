MEMORY_EXTRACTION_PROMPT = """
        사용자의 메시지에서 장기간 기억할 가치가 있는 정보를 추출하세요.
        
        입력에는 다음 두 정보가 포함됩니다.
        
        1. 현재 저장된 장기 기억
        2. 새 사용자 메시지
        
        반드시 현재 저장된 장기 기억과 새 사용자 메시지를 함께 비교하여
        add, update, delete 중 어떤 작업이 필요한지 판단하세요.
        
        작업 종류:
        
        - add: 기존 기억을 유지하면서 새로운 값을 추가할 때 사용합니다.
        
        - update: 기존 값을 새로운 값으로 교체할 때 사용합니다.
        
        - delete: 기존 기억의 특정 값을 제거할 때 사용합니다.
        
        규칙:
        
        - 사용자의 이름, 선호, 관심사, 장기 목표처럼 장기간 유지될 가능성이 높은 정보만 기억합니다.
        
        - 단순 질문, 인사, 일시적인 내용은 기억으로 처리하지 않습니다.
        
        - 한 메시지에 여러 기억이 있다면 모두 추출합니다.
        
        - key는 짧고 일관된 영문 snake_case를 사용합니다.
       
        - 여러 값을 가질 수 있는 항목은 복수형 key를 사용합니다.
        
        - 이미 동일한 값이 저장되어 있다면 다시 add 하지 않습니다.
        
        - 사용자가 "도", "추가로", 그리고" 등의 표현을 사용하면 기존의 값을 유지하고 add를 우선 고려합니다.
        
        - 사용자가 "이제", "앞으로는", "바꿨어", 변경했어"처럼 기존 상태를 새로운 값으로 대체하려는 의미라면 update를 고려합니다.
        
        - 사용자가 특정 값을 더 이상 좋아하지 않는다거나 제외해 달라고 하면 delete를 사용합니다.
        
        key 예시:
        
        - 이름 → name
        - 좋아하는 프로그래밍 언어 → favorite_languages
        - 관심 분야 → interests
        - 취미 → hobbies
        - 장기 목표 → goals
        
        예시:
        
        현재 기억:
        - favorite_languages: Python
        
        새 사용자 메시지:
        나는 Java도 좋아해
        
        결과:
        - operation: add
        - key: favorite_languages
        - value: Java
        
        
        현재 기억:
        - name: atlas
        
        새 사용자 메시지:
        이제 내 이름은 calyps야
        
        결과:
        - operation: update
        - key: name
        - value: calyps
        
        
        현재 기억:
        - favorite_language: Python, Java
        
        새 사용자 메시지:
        이제 Java는 좋아하지 않아
        
        결과:
        - operation: delete
        - key: favorite_language
        - value: Java
        
        
        현재 기억:
        - favorite_language: Python
        
        새 사용자 메시지:
        나는 Python을 좋아해
        
        결과:
        기억 변경 없음
        
        
        새 사용자 메시지:
        안녕
        
        결과:
        기억 변경 없음
        """