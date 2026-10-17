from cleaner import clean_transcript
from chunker import chunk_test


text = """
[Music]

Hello guys, welcome back!

Today we are going to learn
machine learning.

[Laughter]

Machine learning allows computers
to learn from data.

Supervised learning uses labelled data.

[Applause]

Unsupervised learning works with
unlabelled data.

Classification is used for predicting categories.
"""


#clean transcript
cleaned_text = clean_transcript(text)


#chunk the clean transcript
chunks = chunk_test(
    cleaned_text,
    chunk_size=10,
    overlap=2
)



print("\n========== CHUNKS ==========")

for i , chunk in enumerate(chunks):
    print(f"\n------chunks{i+1}-----")
    print(chunk)