from cleaner import clean_transcript
from chunker import chunk_test
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")

text = """
[Music]

Machine learning is a field of artificial intelligence.

It allows computers to learn from data.

Supervised learning uses labelled data.

[Laughter]

Unsupervised learning works with unlabelled data.

Regression is used for predicting continuous values.

Classification is used for predicting categories.

[Applause]
"""


#cleaning
cleaned_text = clean_transcript(text)

#chunking
chunks = chunk_test(
    cleaned_text,
    chunk_size=10,
    overlap=2
)

#embedding
embedding = model.encode(chunks)

print("no. of chunks:",len(chunks))
print("shape of embedding:",embedding.shape)


for i , chunk in enumerate(chunks):
    print(f"\n--- Chunk {i + 1} ---")
    print(chunk)

    print("embedding size:",len(embedding[i]))
    print("first 5 value:",embedding[i][:5])
