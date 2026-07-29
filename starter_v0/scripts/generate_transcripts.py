import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Enforce UTF-8 encoding for Windows terminal stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version
from chat import run_model_tool_loop, write_transcript

load_lab_env(ROOT)
transcripts_dir = ROOT / 'transcripts'
transcripts_dir.mkdir(parents=True, exist_ok=True)

sys_prompt_path = ROOT / 'artifacts' / 'system_prompt.md'
tools_path = ROOT / 'artifacts' / 'tools.yaml'

system_prompt = sys_prompt_path.read_text(encoding='utf-8')
tool_declarations = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(tool_declarations)
provider = make_provider('openai')
artifact_version = build_artifact_version('v3', sys_prompt_path, tools_path)

def create_transcript_session(transcript_id: str, scenarios: list[str]) -> Path:
    messages = [{"role": "system", "content": system_prompt}]
    turns_history = []
    
    for user_input in scenarios:
        messages.append({"role": "user", "content": user_input})
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=getattr(provider, 'default_model', 'gpt-4o-mini'),
            max_tool_rounds=4
        )
        assistant_text = result.get("assistant_text", "")
        messages.append({"role": "assistant", "content": assistant_text})
        
        turns_history.append({
            "user": user_input,
            "assistant": assistant_text,
            "status": result.get("status"),
            "rounds": result.get("rounds", []),
            "tool_events": result.get("tool_events", []),
        })
    
    file_path = transcripts_dir / f"{transcript_id}.transcript.json"
    transcript_data = {
        "transcript_id": transcript_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "provider": "openai",
        "model": getattr(provider, "default_model", "gpt-4o-mini"),
        "version": artifact_version.version,
        "artifact_version": artifact_version.artifact_version,
        "prompt_hash": artifact_version.prompt_hash,
        "tools_hash": artifact_version.tools_hash,
        "turns": turns_history,
        "status": turns_history[-1]["status"] if turns_history else "empty",
    }
    write_transcript(file_path, transcript_data)
    print(f"Saved transcript: {file_path}")
    return file_path

if __name__ == "__main__":
    print("Generating scenario 1...")
    create_transcript_session("scenario1_normal_research", ["Tìm tin tức mới nhất về AI agent evaluation trong tuần này."])
    
    print("Generating scenario 2...")
    create_transcript_session("scenario2_clarify_missing_handle", [
        "Lấy các bài đăng gần đây của người này trên mạng xã hội giúp tôi.",
        "Tài khoản là sama."
    ])
    
    print("Generating scenario 3...")
    create_transcript_session("scenario3_sensitive_confirmation", [
        "Gửi bản tổng hợp nghiên cứu AI này lên Telegram giúp tôi.",
        "Yes, tôi đồng ý gửi."
    ])
    
    print("Generating scenario 4...")
    create_transcript_session("scenario4_multitool_research", [
        "Tìm kiếm các bài viết mới nhất bàn về Gemini 2.0 Flash trên Twitter."
    ])
    
    print("All transcripts generated successfully!")
