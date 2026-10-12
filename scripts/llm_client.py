# llm_client.py
# Sends a prompt to the local Ollama server and returns the model's reply.

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
        "stream": False
    }
#         (the same three keys you sent with curl's -d)

# Step 3: send it to the server and wait for the reply

    response = requests.post(OLLAMA_URL, json=payload, timeout=600)

# Step 4: read the JSON reply and return the "response" field
    if response.status_code == 200:
        return response.json()["response"]
    else:
        raise Exception(f"Request failed with status code {response.status_code}: {response.text}")