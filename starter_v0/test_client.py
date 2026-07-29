from fastapi.testclient import TestClient
from backend.main import app
import json
import sys
import codecs

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

client = TestClient(app)

print("--- TESTING HEALTH ENDPOINT ---")
response = client.get("/api/health")
print(f"Status: {response.status_code}")
print(response.json())

print("\n--- TESTING ARTIFACTS ENDPOINT ---")
response = client.get("/api/artifacts")
print(f"Status: {response.status_code}")
print(response.json())

print("\n--- TESTING CHAT ENDPOINT (Calling 'lookup' tool) ---")
payload = {
    "messages": [{"role": "user", "content": "Hãy dùng công cụ lookup để tìm bài viết Wikipedia về AI (chỉ lấy 1 bài thôi) và cho tôi biết tiêu đề của nó."}],
    "version": "v0",
    "provider": "openai",
    "max_tool_rounds": 4
}
response = client.post("/api/chat", json=payload)
print(f"Status: {response.status_code}")
data = response.json()
print("Status:", data.get("status"))
print("Assistant Text:", data.get("assistant_text"))
print("Tools Called:", [t["tool"] for t in data.get("tool_events", [])])

print("\n--- TESTING TRANSCRIPT ENDPOINT ---")
transcript_id = data.get("transcript_id")
if transcript_id:
    response = client.get(f"/api/transcripts/{transcript_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Transcript fetched successfully!")
        t_data = response.json()
        print(f"Transcript Version: {t_data.get('version')}")
