from chunker import chunk_test

text = """
Machine learning is a field of artificial intelligence.
It allows computers to learn from data.
Supervised learning uses labelled data.
Unsupervised learning works with unlabelled data.
Regression is used for predicting continuous values.
Classification is used for predicting categories.
"""


chunks = chunk_test(text , chunk_size=10 , overlap=2)

for i , chunk in enumerate(chunks):
    print(f"\n---Chunk{i+1}---")
    print(chunk)