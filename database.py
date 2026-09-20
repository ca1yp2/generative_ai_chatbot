import sqlite3

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


DB_PATH = "chatbot.db"

# =========================================================
# 공통 데이터베이스 기능
# =========================================================

# 데이터베이스 연결
def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# UTC 시간을 한국 시간으로 변환
def utc_to_kst(datetime_text):
    if datetime_text is None:
        return None
    
    utc_datetime = datetime.strptime(
        datetime_text,
        "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc)
    
    kst_datetime = utc_datetime.astimezone(
        ZoneInfo("Asia/Seoul")
    )
    
    return kst_datetime.strftime("%Y-%m-%d %H:%M:%S")

# =========================================================
# 데이터베이스 초기화 및 마이그레이션
# =========================================================

# 데이터베이스 초기화
def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 대화 세션 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                summary TEXT,
                context_summary TEXT,
                context_summary_message_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("PRAGMA table_info(chat_sessions)")
        columns = [
            row[1]
            for row in cursor.fetchall()
        ]
        
        if "summary" not in columns:
            cursor.execute("""
                ALTER TABLE chat_sessions
                ADD COLUMN summary TEXT
            """)
        
        if "context_summary" not in columns:
            cursor.execute("""
                ALTER TABLE chat_sessions
                ADD COLUMN context_summary TEXT
            """)
            
        if "context_summary_message_id" not in columns:
            cursor.execute("""
                ALTER TABLE chat_sessions
                ADD COLUMN context_summary_message_id INTEGER
            """)
        
        # 현재 대화 세션 상태 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_state (
                id INTEGER PRIMARY KEY,
                current_session_id INTEGER,
                FOREIGN KEY (current_session_id)
                    REFERENCES chat_sessions(id)
                    ON DELETE SET NULL
            )
        """)
        
        cursor.execute("""
            INSERT OR IGNORE INTO chat_state (
                id, current_session_id
            )
            VALUES (1, NULL)
        """)
        
        # 현재 세션이 지정되어 있지 않다면 기존의 가장 최근 세션을 현재 세션으로 설정
        cursor.execute("""
            SELECT current_session_id
            FROM chat_state
            WHERE id = 1
        """)
        
        row = cursor.fetchone()
        
        if row is not None and row[0] is None:
            cursor.execute("""
                SELECT id
                FROM chat_sessions
                ORDER BY id DESC
                LIMIT 1
            """)
            
            latest_session = cursor.fetchone()
            
            if latest_session is not None:
                cursor.execute("""
                    UPDATE chat_state
                    SET current_session_id = ?
                    WHERE id = 1
                """, (latest_session[0],))
        
        # 대화 기록 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 장기 기억 종류 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 장기 기억 값 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_values(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                value TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (memory_id)
                    REFERENCES memories(id)
                    ON DELETE CASCADE,
                    
                UNIQUE(memory_id, value)
            )
        """)
        
        conn.commit()
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 기존 장기 기억 데이터를 새 구조로 변환
def migrate_memories():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # memories 테이블이 존재하는지 확인
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
                AND name = 'memories'
        """)
        
        if cursor.fetchone() is None:
            return
    
        # 기존 memories 테이블의 컬럼 확인
        cursor.execute("PRAGMA table_info(memories)")
        columns = cursor.fetchall()
        
        column_names = [
            column[1]
            for column in columns
        ]
    
        # value 컬럼이 없다면 이미 새 구조이므로 변환하지 않음
        if "value" not in column_names:
            return
        
        print("장기 기억 데이터 구조를 변환합니다...")
        
        # 기존 데이터 먼저 읽어두기
        cursor.execute("""
            SELECT id, key, value, created_at, updated_at
            FROM memories
            ORDER BY id ASC
        """)
        
        old_rows = cursor.fetchall()
        
        # 혹시 memory_values가 이미 존재하는지 확인
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
                AND name = 'memory_values'
        """)
        
        memory_values_exists = cursor.fetchone() is not None
        
        if memory_values_exists:
            cursor.execute("""
                SELECT COUNT(*)
                FROM memory_values
            """)
            
            value_count = cursor.fetchone()[0]
            
            # 기존 데이터가 들어 있는 memory_values를 임의로 삭제하면 안 되므로 삭제하면 마이그레이션 중단
            if value_count > 0:
                raise RuntimeError(
                    "기존 memory_values 테이블에 데이터가 있어 자동 마이그레이션을 중단했습니다."
                )
        
        # 테이블 구조 변경 중에는 외래 키 검사 비활성화
        conn.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("BEGIN")
        
        # 비어 있는 memory_values가 이미 있다면 제거
        if memory_values_exists:
            cursor.execute("DROP TABLE memory_values")
            
        # 기존 memories 테이블 제거
        cursor.execute("DROP TABLE memories")
    
        # 새 memories 테이블 생성
        cursor.execute("""
            CREATE TABLE memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 새 memory_values 테이블 생성
        cursor.execute("""
            CREATE TABLE memory_values(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                value TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id)
                    REFERENCES memories(id)
                    ON DELETE CASCADE,
                UNIQUE(memory_id, value)
            )
        """)
    
        # 기존 데이터를 새 구조로 변환
        for memory_id, key, old_value, created_at, updated_at in old_rows:
            
            # 기존 id와 시간 정보도 그대로 보존
            cursor.execute(
                """
                INSERT INTO memories (id, key, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (memory_id, key, created_at, updated_at)
            )
            
            # 기존 "Python, Java" 형태의 값을 각각 분리
            values = [
                value.strip()
                for value in old_value.split(",")
                if value.strip()
            ]
            
            for value in values:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO memory_values (
                        memory_id,
                        value
                    )
                    VALUES (?, ?)
                    """,
                    (memory_id, value)
                )
        # 외래 키 구조 검증
        problems = cursor.execute("PRAGMA foreign_key_check").fetchall()
        
        if problems:
            raise RuntimeError(
                f"외래 키 검사 실패: {problems}"
            )
        
        conn.commit()
        
        print("장기 기억 데이터 구조 변환이 완료되었습니다.")
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# memory_values 외래 키 복구
def repair_memory_values_foreign_key():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 현재 외래 키 확인
        cursor.execute("PRAGMA foreign_key_list(memory_values)")
        foreign_keys = cursor.fetchall()
        
        # memory_values 테이블이 없거나 이미 memories를 정상 참조하고 있다면 종료
        if not foreign_keys:
            return
        
        referenced_table = foreign_keys[0][2]
        
        if referenced_table == "memories":
            return
        
        print("memory_values 외래 키를 복구합니다...")
        
        # 테이블 재구성 중 외래 키 검사 비활성화
        conn.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("BEGIN")
        cursor.execute("DROP TABLE IF EXISTS memory_values_new")
        cursor.execute("""
            CREATE TABLE memory_values_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                value TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id)
                    REFERENCES memories(id)
                    ON DELETE CASCADE,
                UNIQUE(memory_id, value)
            )
        """)
        
        cursor.execute("""
            INSERT INTO memory_values_new (id, memory_id, value, created_at)
            SELECT id, memory_id, value, created_at
            FROM memory_values
        """)
        
        cursor.execute("DROP TABLE memory_values")
        
        cursor.execute("""
            ALTER TABLE memory_values_new
            RENAME TO memory_values
        """)
        
        conn.commit()
        
        print("memory_values 외래 키 복구가 완료되었습니다.")
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 기존 대화 기록을 세션 구조로 변환
def migrate_messages_to_sessions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # messages 테이블 존재 여부 확인
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
                AND name = 'messages'
        """)
        
        if cursor.fetchone() is None:
            return
        
        # 현재 messages 테이블 컬럼 확인
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        
        column_names = [
            column[1]
            for column in columns
        ]
        
        # 이미 session_id가 있다면 마이그레이션하지 않음
        if "session_id" in column_names:
            return
        
        print("대화 기록 구조를 세션 방식으로 변환합니다...")
        
        # 기존 메시지 미리 읽어두기
        cursor.execute("""
            SELECT id, role, content, created_at
            FROM messages
            ORDER BY id ASC
        """)
        
        old_messages = cursor.fetchall()
        
        conn.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("BEGIN")
        
        # 기존 메시지가 있다면 기존 대화를 담을 첫 세션 생성
        if old_messages:
            cursor.execute("INSERT INTO chat_sessions DEFAULT VALUES")
            
            session_id = cursor.lastrowid
            
        else:
            session_id = None
            
        # 새 messages 테이블 생성
        cursor.execute("""
            CREATE TABLE messages_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                Foreign KEY (session_id)
                    REFERENCES chat_sessions(id)
                    ON DELETE CASCADE
            )
        """)
        
        # 기존 메시지를 첫 번째 세션에 복사
        for message_id, role, content, created_at in old_messages:
            cursor.execute("""
                INSERT INTO messages_new (id, session_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (message_id, session_id, role, content, created_at))
        
        # 기존 messages 삭제
        cursor.execute("DROP TABLE messages")
        
        # 새 테이블을 messages로 변경
        cursor.execute("""
            ALTER TABLE messages_new
            RENAME TO messages
        """)
        
        conn.commit()
        
        print("대화 기록 구조 변환이 완료되었습니다.")
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 대화 세션 제목 컬럼 추가
def migrate_chat_sessions_title():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(chat_sessions)")
        
        columns = cursor.fetchall()
        
        column_names = [
            column[1]
            for column in columns
        ]
        
        if "title" in column_names:
            return
        
        print("대화 세션에 제목 기능을 추가합니다...")
        
        cursor.execute("""
            ALTER TABLE chat_sessions
            ADD COLUMN title TEXT
        """)
        
        conn.commit()
        
        print("대화 세션 제목 기능 추가가 완료되었습니다.")
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# =========================================================
# 일반 대화 처리
# =========================================================

# 대화 메시지 저장
def save_message(role, content):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        session_id = get_current_session_id()
        
        if session_id is None:
            session_id = create_chat_session()
            
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        
        cursor.execute("""
        UPDATE chat_sessions
        SET summary = NULL
        WHERE id = ?
        """, (session_id,))
        
        conn.commit()
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 현재 세션의 최근 대화 기록 불러오기
def get_recent_messages(limit=20):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        session_id = get_current_session_id()
        
        if session_id is None:
            return []
        
        cursor.execute("""
            SELECT role, content
            FROM messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (session_id, limit))
        
        rows = cursor.fetchall()
        
        # 최신 순서로 조회했으므로 다시 시간순으로 정렬
        rows.reverse()
        
        return [
            {
                "role": role,
                "content": content
            }
            for role, content in rows
        ]
    
    finally:
        conn.close()
        
# 컨텍스트 요약에 새로 포함할 메시지 가져오기
def get_messages_for_context_summary(session_id, recent_limit, after_message_id=None):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        #최근 대화로 유지할 메시지의 시작 ID 확인
        cursor.execute("""
            SELECT id
            FROM messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1 OFFSET ?
        """, (session_id, recent_limit - 1))
        
        row = cursor.fetchone()
        
        # 최근 대화 기록 개수보다 메시지가 적으면 아직 컨텍스트 요약 대상이 없음
        if row is None:
            return []
        
        recent_start_message_id = row[0]
        
        # 아직 한 번도 컨텍스트 요약을 만들지 않은 경우
        if after_message_id is None:
            cursor.execute("""
                SELECT id, role, content
                FROM messages
                WHERE session_id = ?
                    AND id < ?
                ORDER BY id ASC
            """, (session_id, recent_start_message_id))
            
        # 기존 컨텍스트 요약이 있는 경우
        else:
            cursor.execute("""
                SELECT id, role, content
                FROM messages
                WHERE session_id = ?
                    AND id > ?
                    AND id < ?
                ORDER BY id ASC
            """, (session_id, after_message_id, recent_start_message_id))
            
        rows = cursor.fetchall()
        
        return [
            {
                "id": message_id,
                "role": role,
                "content": content
            }
            for message_id, role, content in rows
        ]
            
    finally:
        conn.close()

# 현재 대화 세션 ID 가져오기
def get_current_session_id():
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT current_session_id
            FROM chat_state
            WHERE id = 1
        """)
        
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return row[0]
    
    finally:
        conn.close()

# 가장 최근 대화 세션 ID 가져오기
def get_latest_chat_session_id():
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id
            FROM chat_sessions
            ORDER BY id DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return row[0]
    
    finally:
        conn.close()

# 대화 세션 존재 여부 확인
def chat_session_exists(session_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 1
            FROM chat_sessions
            WHERE id = ?
        """, (session_id,))
        
        return cursor.fetchone() is not None
    
    finally:
        conn.close()

# 특정 세션의 사용자 메시지 개수 가져오기
def get_user_message_count(session_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM messages
            WHERE session_id = ?
                AND role = 'user'
        """, (session_id,))
        
        row = cursor.fetchone()
        
        return row[0]
    
    finally:
        conn.close()

# 대화 세션 제목 가져오기
def get_chat_session_title(session_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT title
            FROM chat_sessions
            WHERE id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return row[0]
    
    finally:
        conn.close()

# =========================================================
# 대화 명령어 관련 기능
# =========================================================

# 새로운 대화 세션 생성
def create_chat_session():
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO chat_sessions DEFAULT VALUES")
        
        session_id = cursor.lastrowid
        
        cursor.execute("""
            UPDATE chat_state
            SET current_session_id = ?
            WHERE id = 1
        """, (session_id,))
        
        conn.commit()
        
        return session_id
    
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 대화 세션 목록 가져오기
def get_chat_sessions():
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT chat_sessions.id, chat_sessions.title, chat_sessions.created_at, COUNT(messages.id)
            FROM chat_sessions
            LEFT JOIN messages
                ON chat_sessions.id = messages.session_id
            GROUP BY chat_sessions.id, chat_sessions.title, chat_sessions.created_at
            ORDER BY chat_sessions.id DESC
        """)
        
        rows = cursor.fetchall()
        
        return [
            {
                "id": session_id,
                "title": title,
                "created_at": utc_to_kst(created_at),
                "message_count": message_count
            }
            for session_id, title, created_at, message_count in rows
        ]
        
    finally:
        conn.close()

# 특정 대화 세션 정보 가져오기
def get_chat_session_info(session_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT cs.id, cs.title, cs.created_at, cs.summary, COUNT(m.id)
            FROM chat_sessions AS cs
            LEFT JOIN messages AS m
                ON m.session_id = cs.id
            WHERE cs.id = ?
            GROUP BY cs.id, cs.title, cs.created_at, cs.summary
        """, (session_id,))
        
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return {
            "id": row[0],
            "title": row[1],
            "created_at": utc_to_kst(row[2]),
            "summary": row[3],
            "message_count": row[4]
        }
        
    finally:
        conn.close()

# 특정 대화 세션의 메시지 가져오기
def get_session_messages(session_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 세션 존재 여부 확인
        cursor.execute("""
            SELECT id
            FROM chat_sessions
            WHERE id = ?
        """, (session_id,))
        
        if cursor.fetchone() is None:
            return None
        
        # 해당 세션의 메시지 조회
        cursor.execute("""
            SELECT id, role, content, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
        """, (session_id,))
        
        rows = cursor.fetchall()
        
        return [
            {
                "id": message_id,
                "role": role,
                "content": content,
                "created_at": created_at
            }
            for message_id, role, content, created_at in rows
        ]
    
    finally:
        conn.close()
        
# 특정 대화 메시지 수정
def update_message(session_id, message_id, content):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE messages
            SET content = ?
            WHERE id = ?
                AND session_id = ?
        """, (content, message_id, session_id))
        
        if cursor.rowcount == 0:
            return False
        
        # 메시지가 수정되면 기존 세션 요약 무효화
        cursor.execute("""
            UPDATE chat_sessions
            SET summary = NULL
            WHERE id = ?
        """, (session_id,))
        
        # 수정된 메시지가 이미 컨텍스트 요약에 포함되어 있다면 기존 컨텍스트 요약을 무효화
        cursor.execute("""
            SELECT context_summary_message_id
            FROM chat_sessions
            WHERE id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        
        if (
            row is not None
            and row[0] is not None
            and message_id <= row[0]
        ):
            cursor.execute("""
                UPDATE chat_sessions
                SET context_summary = NULL,
                    context_summary_message_id = NULL
                WHERE id = ?
            """, (session_id,))
        
        conn.commit()
        
        return True
    
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 대화 세션 검색
def search_chat_sessions(query):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        search_pattern = f"%{query.lower()}%"
        
        cursor.execute("""
            SELECT
                chat_sessions.id,
                chat_sessions.title,
                chat_sessions.created_at,
                (
                    SELECT COUNT(*)
                    FROM messages
                    WHERE messages.session_id = chat_sessions.id
                ) AS message_count,
                (
                    SELECT role
                    FROM messages
                    WHERE messages.session_id = chat_sessions.id
                        AND LOWER(COALESCE(messages.content, '')) LIKE ?
                    ORDER BY messages.id ASC
                    LIMIT 1
                ) AS matched_role,
                (
                    SELECT content
                    FROM messages
                    WHERE messages.session_id = chat_sessions.id
                        AND LOWER(COALESCE(messages.content, '')) LIKE ?
                    ORDER BY messages.id ASC
                    LIMIT 1
                ) AS matched_content
            FROM chat_sessions
            WHERE LOWER(COALESCE(chat_sessions.title, '')) LIKE ?
                OR EXISTS(
                    SELECT 1
                    FROM messages
                    WHERE messages.session_id = chat_sessions.id
                        AND LOWER(COALESCE(messages.content, '')) LIKE ?
                )
            ORDER BY chat_sessions.id DESC
        """, (search_pattern, search_pattern, search_pattern, search_pattern))
        
        rows = cursor.fetchall()
        
        return [
            {
                "id": session_id,
                "title": title,
                "created_at": utc_to_kst(created_at),
                "message_count": message_count,
                "matched_role": matched_role,
                "matched_content": matched_content
            }
            for (session_id, title, created_at, message_count, matched_role, matched_content) in rows
        ]
        
    finally:
        conn.close()

# 현재 대화 세션 변경
def set_current_session_id(session_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE chat_state
            SET current_session_id = ?
            WHERE id = 1
        """, (session_id,))
        
        conn.commit()
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 대화 세션 제목 변경
def update_chat_session_title(session_id, title):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE chat_sessions
            SET title = ?
            WHERE id = ?
        """, (title, session_id))
        
        if cursor.rowcount == 0:
            return False
        
        conn.commit()
        return True
    
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 저장된 대화 요약 가져오기
def get_chat_session_summary(session_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT summary
            FROM chat_sessions
            WHERE id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return row[0]
    
    finally:
        conn.close()

# 대화 세션 요약 저장
def update_chat_session_summary(session_id, summary):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE chat_sessions
            SET summary = ?
            WHERE id = ?
        """, (summary, session_id))
        
        conn.commit()
        
        return cursor.rowcount > 0
    
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()
        
# 대화 컨텍스트 요약 가져오기
def get_chat_context_summary(session_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT context_summary, context_summary_message_id
            FROM chat_sessions
            WHERE id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return {
            "summary": row[0],
            "message_id": row[1]
        }
        
    finally:
        conn.close()
        
# 대화 컨텍스트 요약 저장
def update_chat_context_summary(session_id, summary, message_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE chat_sessions
            SET context_summary = ?,
                context_summary_message_id = ?
            WHERE id = ?
        """, (summary, message_id, session_id))
    
        conn.commit()
        return cursor.rowcount > 0
    
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 특정 대화 세션 삭제
def delete_chat_session(session_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM chat_sessions
            WHERE id = ?
        """, (session_id,))
        
        if cursor.rowcount == 0:
            return False
        
        conn.commit()
        return True
    
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 모든 대화 세션과 대화 기록 삭제
def clear_messages():
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM chat_sessions")

        conn.commit()
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# =========================================================
# 장기 기억 명령어 관련 기능
# =========================================================

# 장기 기억 목록 불러오기
def get_memories():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT memories.key, memory_values.value
        FROM memories
        JOIN memory_values
            ON memories.id = memory_values.memory_id
        ORDER BY memories.id ASC, memory_values.id ASC
    """)
    
    rows = cursor.fetchall()
    
    conn.close()
    
    memories = {}
    
    # 같은 key의 여러 값을 하나로 묶기
    for key, value in rows:
        if key not in memories:
            memories[key] = []
            
        memories[key].append(value)
    
    # 기존 코드와 호환되는 형태로 반환
    return [
        {
            "key": key,
            "value": ", ".join(values)
        }
        for key, values in memories.items()
    ]

# 특정 장기 기억 상세 조회
def get_memory_values(key):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT memory_values.value
            FROM memories
            JOIN memory_values
                ON memories.id = memory_values.memory_id
            WHERE memories.key = ?
            ORDER BY memory_values.id ASC
            """,
            (key,)
        )
        
        rows = cursor.fetchall()
        
        return [
            row[0]
            for row in rows
        ]
        
    finally:
        conn.close()

# 장기 기억 검색
def search_memories(query):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        search_pattern = f"%{query}%"
        
        cursor.execute(
            """
            SELECT memories.key, memory_values.value
            FROM memories
            JOIN memory_values
                ON memories.id = memory_values.memory_id
            WHERE LOWER(memories.key) LIKE LOWER(?)
                OR LOWER(memory_values.value) LIKE LOWER(?)
            ORDER BY memories.id ASC, memory_values.id ASC
            """,
            (search_pattern, search_pattern)
        )
        
        rows = cursor.fetchall()
        
        return [
            {
                "key": key,
                "value": value
            }
            for key, value in rows
        ]
        
    finally:
        conn.close()

# 특정 장기 기억 전체 삭제
def delete_memory(key):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 해당 key가 존재하는지 확인
        cursor.execute(
            "SELECT id FROM memories WHERE key = ?",
            (key,)
        )
        
        row = cursor.fetchone()
        
        if row is None:
            return False
        
        # key 삭제
        cursor.execute(
            "DELETE FROM memories WHERE id = ?",
            (row[0],)
        )
        
        conn.commit()
        return True
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 모든 장기 기억 삭제
def clear_memories():
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM memories")
        conn.commit()
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# =========================================================
# 장기 기억 저장 및 수정 기능
# =========================================================

# 장기 기억 값 추가
def add_memory_value(key, new_value):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 해당 key가 존재하는지 확인
        cursor.execute(
            "SELECT id FROM memories WHERE key = ?",
            (key,)
        )
        
        row = cursor.fetchone()
        
        # key가 없다면 새로 생성
        if row is None:
            cursor.execute(
                "INSERT INTO memories (key) VALUES (?)",
                (key,)
            )
            
            memory_id = cursor.lastrowid
        
        else:
            memory_id = row[0]
        
        # 같은 값이 이미 있는지 대소문자를 무시하고 확인
        cursor.execute(
            """
            SELECT id
            FROM memory_values
            WHERE memory_id = ?
                AND LOWER(value) = LOWER(?)
            """,
            (memory_id, new_value)
        )
        
        existing_value = cursor.fetchone()
        
        # 같은 값이 없을 때만 추가
        if existing_value is None:
            cursor.execute(
                """
                INSERT INTO memory_values (
                    memory_id,
                    value
                )
                VALUES (?, ?)
                """,
                (memory_id, new_value)
            )
        
        # 수정 시간 갱신
        cursor.execute(
            """
            UPDATE memories
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (memory_id,)
        )
            
        conn.commit()
    
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 장기 기억 저장 또는 기존 값 교체
def save_memory(key, value):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 해당 key가 존재하는지 확인
        cursor.execute(
            "SELECT id FROM memories WHERE key = ?",
            (key,)
        )
        
        row = cursor.fetchone()
        
        # key가 없다면 새로 생성
        if row is None:
            cursor.execute(
                "INSERT INTO memories (key) VALUES (?)",
                (key,)
            )
            
            memory_id = cursor.lastrowid
        
        # 기존 key라면 기존 값 전체 삭제
        else:
            memory_id = row[0]
            
            cursor.execute(
                "DELETE FROM memory_values WHERE memory_id = ?",
                (memory_id,)
            )
        
        # 새로운 값 저장
        cursor.execute("""
            INSERT INTO memory_values (
                memory_id,
                value
            )
            VALUES (?, ?)
            """,
            (memory_id, value)
        )
        
        # 수정 시간 갱신
        cursor.execute(
            """
            UPDATE memories
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (memory_id,)
        )
        
        conn.commit()
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()

# 특정 장기 기억 값 삭제
def delete_memory_value(key, delete_value):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 해당 key가 존재하는지 확인
        cursor.execute(
            "SELECT id FROM memories WHERE key = ?",
            (key,)
        )
        
        row = cursor.fetchone()
        
        if row is None:
            return
        
        memory_id = row[0]
        
        # 특정 값 삭제
        cursor.execute(
            """
            DELETE FROM memory_values
            WHERE memory_id = ?
                AND LOWER(value) = LOWER(?)
            """,
            (memory_id, delete_value)
        )
        
        # 남아 있는 값 개수 확인
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM memory_values
            WHERE memory_id = ?
            """,
            (memory_id,)
        )
        
        remaining_count = cursor.fetchone()[0]
        
        # 값이 하나도 남지 않았다면 key도 삭제
        if remaining_count == 0:
            cursor.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,)
            )
        
        else:
            cursor.execute(
                """
                UPDATE memories
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (memory_id,)
            )
        
        conn.commit()
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        conn.close()
