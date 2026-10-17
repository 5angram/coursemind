import requests
import numpy as np

OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "bge-m3"

def create_embedding(chunks):
    print("\n==============creating embeddings===============")
    print("no. of chunks:",len(chunks))

    response = requests.post(
        OLLAMA_URL,
        json={
            "model":MODEL,
            "input":chunks
        }
    )

    if response.status_code != 200:
        raise Exception(
            f"embedding failed :"
            f"{response.status_code}-{response.text}"
        )

    data = response.json()

    embeddings = np.array(
        data["embeddings"],
        dtype=np.float32
    )

    print("embedding shape:",embeddings.shape)
    return embeddings