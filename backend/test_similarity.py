from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

model = SentenceTransformer("BAAI/bge-m3")

chunks = [
    "Machine learning is a field of artificial intelligence.",
    "Supervised learning uses labelled data.",
    "Unsupervised learning works with unlabelled data.",
    "Regression is used for predicting continuous values.",
    "Classification is used for predicting categories."
]

question = "What is supervised learning?"

chunks_embedding = model.encode(chunks)
question_embedding = model.encode(question)

similarity = cos_sim(
    question_embedding,
    chunks_embedding
)[0]

for i , score in enumerate(similarity):
    print(f"Chunks{i+1}")
    print(chunks[i])

    print("similarity:",float(score))
    print()
