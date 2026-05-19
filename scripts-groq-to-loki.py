import requests
import time
import json
from datetime import datetime, timezone

import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")  # Use .env instead
LOKI_URL = "http://localhost:3100/loki/api/v1/push"
INTERVAL_SECONDS = 300

def get_groq_models():
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    try:
        response = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception as e:
        print(f"Erreur: {e}")
    return []

def push_to_loki(log_message, stream_labels):
    ts = str(int(time.time() * 1_000_000_000))
    payload = {"streams": [{"stream": stream_labels, "values": [[ts, log_message]]}]}
    try:
        r = requests.post(LOKI_URL, json=payload, timeout=10)
        if r.status_code == 204:
            print(f"OK: {log_message[:60]}")
    except Exception as e:
        print(f"Erreur Loki: {e}")

def collect_and_send():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Collecte Groq...")
    models = get_groq_models()
    if not models:
        return
    for model in models:
        model_id = model.get("id", "unknown")
        model_type = "audio" if "whisper" in model_id.lower() else "llm"
        log_entry = json.dumps({"event": "groq_model_info", "model": model_id, "type": model_type, "timestamp": datetime.now(timezone.utc).isoformat()})
        push_to_loki(log_entry, {"app": "groq", "type": model_type, "model": model_id})
    print(f"{len(models)} modeles envoyes a Loki")

collect_and_send()
while True:
    time.sleep(INTERVAL_SECONDS)
    collect_and_send()
