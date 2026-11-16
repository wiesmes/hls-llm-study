# llm_client.py
# Sends a prompt to the local Ollama server and returns the model's reply.

import json
from pathlib import Path

import requests

# Step 1: the address and the model name (the URL and "model" from the curl test)
OLLAMA_URL = "http://localhost:11434/api/generate"
#OLLAMA_MODEL = "fake-model"
OLLAMA_MODEL = "qwen2.5-coder:7b"
# Step 2: define ask(prompt) and build the data to send
def ask(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.8, "num_ctx": 4096}
    }

# Step 3: send it to the server and wait for the reply

    response = requests.post(OLLAMA_URL, json=payload, timeout=600)

# Step 4: read the JSON reply and return the "response" field
    if response.status_code == 200:
        data = response.json()
        ask.last_counts = {key: data.get(key) for key in ("prompt_eval_count", "eval_count")}
        return data["response"]
    else:
        raise Exception(f"Request failed with status code {response.status_code}: {response.text}")


def save_counts(path):
    """Save token counts for the most recent successful ask(), without changing its return type."""
    Path(path).write_text(json.dumps(ask.last_counts, indent=2) + "\n", encoding="utf-8")
