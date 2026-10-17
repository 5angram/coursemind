import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VECTOR_DIR = os.path.join(
    BASE_DIR,
    "data",
    "vector"
)

def save_vector(video_id , chunks , embeddings):
    os.makedirs(VECTOR_DIR , exist_ok=True)

    records = []

    for i , chunk in enumerate(chunks):
        records.append({
            "video_id": video_id,
            "chunk_id": i + 1,
            "text": chunk,
            "embedding": embeddings[i].tolist()
        })

    file_path = os.path.join(
        VECTOR_DIR,
        f"{video_id}.json"
    )

    with open(file_path,"w",encoding="utf-8")as file:
        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("vector saved at:",file_path)

def load_vector(video_id):
    file_path = os.path.join(
        VECTOR_DIR,
        f"{video_id}.json"
    )

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"vector file not found:{file_path}"
        )

    with open(file_path,"r",encoding="utf-8") as file:
        return json.load(file)