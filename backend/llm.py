import requests
import json


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:latest"


def generate_answer(
    prompt,
    max_tokens=450,
    temperature=0.1
):

    print("\n========== GENERATING ANSWER ==========")
    print("Sending prompt to Ollama...")

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        },
        stream=True,
        timeout=(10, 180)
    )

    print(
        "Ollama status:",
        response.status_code
    )

    if response.status_code != 200:
        raise Exception(
            f"Ollama request failed: "
            f"{response.status_code} - {response.text}"
        )

    answer_parts = []

    try:
        for line in response.iter_lines():

            if not line:
                continue

            data = json.loads(
                line.decode("utf-8")
            )

            text = data.get(
                "response",
                ""
            )

            if text:
                answer_parts.append(text)

            if data.get("done"):
                break
    finally:
        response.close()

    answer = "".join(answer_parts).strip()

    if not answer:
        raise Exception(
            "Ollama returned an empty response."
        )

    print(
        "Answer generated successfully."
    )

    return answer