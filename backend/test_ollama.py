import requests


url = "http://localhost:11434/api/generate"

data = {
    "model": "llama3.2:latest",
    "prompt": "What is a flowchart? Answer in two sentences.",
    "stream": False
}


print("Sending request to Ollama...")

response = requests.post(
    url,
    json=data,
    timeout=120
)


print("Status:", response.status_code)

print("\nResponse:")

print(response.text)