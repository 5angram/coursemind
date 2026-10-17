from transcript import get_transcript
from chunker import chunk_test
from cleaner import clean_transcript
from vector_store import save_vector
from sentence_transformers import SentenceTransformer


video_id = "N4gJDGdhpLw"

result = get_transcript(video_id)

cleaned_text = clean_transcript(result["text"])

chunks = chunk_test(
    cleaned_text,
    chunk_size=100,
    overlap=20
)

print("no. of chunks :" ,len(chunks))

model = SentenceTransformer("BAAI/bge-large-en-v1.5")

embeddings = model.encode(chunks)

print("embedding shape:",embeddings.shape)

save_vector(video_id , chunks , embeddings)