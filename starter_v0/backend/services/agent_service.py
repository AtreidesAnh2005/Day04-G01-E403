import sys
from pathlib import Path
from typing import Any
from datetime import datetime

# To import from starter_v0
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version
from chat import run_model_tool_loop, write_transcript

ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

def get_artifact_paths(version: str) -> tuple[Path, Path]:
    version_dir = ARTIFACTS_DIR / "versions" / version
    sys_prompt = version_dir / "system_prompt.md"
    tools_yaml = version_dir / "tools.yaml"
    
    if not sys_prompt.exists():
        sys_prompt = ARTIFACTS_DIR / "system_prompt.md"
    if not tools_yaml.exists():
        tools_yaml = ARTIFACTS_DIR / "tools.yaml"
        
    return sys_prompt, tools_yaml

def process_chat(request_data: dict[str, Any]) -> dict[str, Any]:
    sys_prompt_path, tools_path = get_artifact_paths(request_data["version"])
    
    system_prompt = sys_prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    
    provider = make_provider(request_data["provider"])
    selected_model = request_data["model"] or getattr(provider, "default_model", None)
    
    artifact_version = build_artifact_version(request_data["version"], sys_prompt_path, tools_path)
    
    working_messages = [{"role": "system", "content": system_prompt}] + request_data["messages"]
    
    result = run_model_tool_loop(
        provider=provider,
        messages=working_messages,
        tools=openai_tools,
        model=selected_model,
        max_tool_rounds=request_data["max_tool_rounds"]
    )
    
    transcript_id = f"chat_{request_data['provider']}_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}"
    transcript_data = {
        "transcript_id": transcript_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "provider": request_data["provider"],
        "model": selected_model,
        "version": artifact_version.version,
        "artifact_version": artifact_version.artifact_version,
        "prompt_hash": artifact_version.prompt_hash,
        "tools_hash": artifact_version.tools_hash,
        "turns": [{
            "user": request_data["messages"][-1]["content"] if request_data["messages"] else "",
            "assistant": result.get("assistant_text", ""),
            "status": result.get("status"),
            "rounds": result.get("rounds", []),
            "tool_events": result.get("tool_events", []),
        }],
        "status": result.get("status")
    }
    
    write_transcript(TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json", transcript_data)
    
    return {
        "status": result.get("status"),
        "assistant_text": result.get("assistant_text", ""),
        "artifact_version": artifact_version.artifact_version,
        "prompt_hash": artifact_version.prompt_hash,
        "tools_hash": artifact_version.tools_hash,
        "rounds": result.get("rounds", []),
        "tool_events": result.get("tool_events", []),
        "transcript_id": transcript_id
    }
