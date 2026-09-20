from pathlib import Path

EXPORT_DIR = Path("exports")

def export_session_to_markdown(session, messages):
    EXPORT_DIR.mkdir(exist_ok=True)
    
    session_id = session["id"]
    title = session["title"] or "제목 없음"
    created_at = session["created_at"]
    summary = session["summary"]
    message_count = session["message_count"]
    
    file_path = EXPORT_DIR / f"session_{session_id}.md"
    
    lines = [
        f"# {title}",
        "",
        f"- 세션 ID: {session_id}",
        f"- 생성 시간: {created_at}",
        f"- 메시지 수: {message_count}개",
        "",
        "## 대화 요약",
        ""
    ]
    
    if summary:
        lines.append(summary)
    else:
        lines.append("저장된 요약이 없습니다.")
        
    lines.extend([
        "",
        "## 전체 대화",
        ""
    ])
    
    for message in messages:
        if message["role"] == "user":
            speaker = "사용자"
        elif message["role"] == "assistant":
            speaker = "AI"
        else:
            speaker = message["role"]
            
        lines.extend([
            f"### {speaker}",
            "",
            message["content"],
            ""
        ])
    
    file_path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )
    
    return str(file_path)