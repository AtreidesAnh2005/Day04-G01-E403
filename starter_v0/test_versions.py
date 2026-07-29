from fastapi.testclient import TestClient
from backend.main import app
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

client = TestClient(app)

print("--- TESTING ARTIFACTS ENDPOINT ---")
response = client.get("/api/artifacts")
print(response.json())

for version in ["v0", "v1", "v2"]:
    print(f"\n--- TESTING CHAT ENDPOINT ({version}) ---")
    payload = {
        "messages": [{"role": "user", "content": "hello"}],
        "version": version,
        "provider": "openai",
        "max_tool_rounds": 1
    }
    response = client.post("/api/chat", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"[{version}] Status:", data.get("status"))
        print(f"[{version}] Artifact Hash:", data.get("artifact_version"))
    else:
        print(f"[{version}] ERROR:", response.status_code, response.text)
