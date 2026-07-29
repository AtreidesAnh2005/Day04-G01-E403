from typing import Any, List, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    version: str = "v3"
    provider: str = "openai"
    model: Optional[str] = None
    max_tool_rounds: int = 4

class ToolCallSchema(BaseModel):
    name: str
    args: dict[str, Any]

class ToolEventSchema(BaseModel):
    tool: str
    args: dict[str, Any]
    result: dict[str, Any]

class RoundSchema(BaseModel):
    round: int
    assistant_text: Optional[str] = None
    tool_calls: List[ToolCallSchema]
    tool_results: List[ToolEventSchema]

class ChatResponse(BaseModel):
    status: str
    assistant_text: str
    artifact_version: str
    prompt_hash: str
    tools_hash: str
    rounds: List[RoundSchema]
    tool_events: List[ToolEventSchema]
    transcript_id: str
