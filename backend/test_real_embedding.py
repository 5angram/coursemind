from chunker import chunk_test
from cleaner import clean_transcript
from transcript import get_transcript
from sentence_transformers import SentenceTransformer

video_id = "N4gJDGdhpLw"

result = get_transcript(video_id)


print("Language:", result["language"])
print("Language code:", result["language_code"])

clean_text = clean_transcript(result["text"])

chunks = chunk_test(
    clean_text,
    chunk_size=100,
    overlap=20
)

print("\nNumber of chunks:", len(chunks))


model = SentenceTransformer("BAAI/bge-large-en-v1.5")

embeddings = model.encode(chunks)

print("embedding shape:",embeddings.shape)

for i , embedding in enumerate(embeddings):
    print(f"chunk{i+1}")
    print(chunks[i])

    print("embedding size",len(embedding))

    print("first 5 values:",embedding[:5])