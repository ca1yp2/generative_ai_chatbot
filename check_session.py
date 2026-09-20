import sqlite3

from database import get_current_session_id

conn = sqlite3.connect("chatbot.db")
cursor = conn.cursor()

print("[messages 테이블 구조]")

cursor.execute("PRAGMA table_info(messages)")

for column in cursor.fetchall():
    print(column)
    
print("\n[chat_sessions]")

cursor.execute("""
    SELECT *
    FROM chat_sessions
    ORDER BY id
""")

sessions = cursor.fetchall()

for session in sessions:
    print(session)
    
print("\n[messages 일부]")

cursor.execute("""
    SELECT id, session_id, role, content, created_at
    FROM messages
    ORDER BY id DESC
    LIMIT 10
""")

messages = cursor.fetchall()

for message in messages:
    print(message)
    
print("\n[외래 키]")

cursor.execute("PRAGMA foreign_key_list(messages)")

for foreign_key in cursor.fetchall():
    print(foreign_key)
    
conn.close()

print("\n[현재 세션]")
print(get_current_session_id())