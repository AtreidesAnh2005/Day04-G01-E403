import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import ChatRequest, ChatResponse
from backend.services.agent_service import process_chat, ARTIFACTS_DIR, TRANSCRIPTS_DIR

app = FastAPI(title="Research Agent Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/artifacts")
def get_artifacts():
    versions = ["v0"] # Base version
    versions_dir = ARTIFACTS_DIR / "versions"
    if versions_dir.exists():
        for d in versions_dir.iterdir():
            if d.is_dir():
                versions.append(d.name)
    return {"versions": list(set(versions))}

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        response_data = process_chat(request.model_dump())
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transcripts/{transcript_id}")
def get_transcript(transcript_id: str):
    file_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
