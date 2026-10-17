import os
import json

import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VECTOR_DIR = os.path.join(
    BASE_DIR,
    "data",
    "vector"
)

model = SentenceTransformer("BAAI/bge-large-en-v1.5")

def cosine_similarity(a , b):
    return np.dot(a,b)/(np.linalg.norm(a) * np.linalg.norm(b))

def search(video_id , query , top_k=3):
    file_path = os.path.join(
        VECTOR_DIR,
        f"{video_id}.json"
    )

    with open(file_path , "r" , encoding="utf-8") as file:
        records = json.load(file)

    query_embeddings = model.encode(query)

    results = []

    for record in records:
        chunk_embedding = record["embedding"]

        score = cosine_similarity(
            query_embeddings,
            chunk_embedding
        )

        results.append({
            "chunk_id": record["chunk_id"],
            "text": record["text"],
            "score": float(score)
        })

    results.sort(
        key = lambda x : x["score"],
        reverse=True
    )

    return results[:top_k]