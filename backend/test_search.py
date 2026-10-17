from search import search

video_id = "N4gJDGdhpLw"

query = "What are permutations?"

results = search(video_id , query , top_k=3)

for result in results:
    print(
        f"\nChunk {result['chunk_id']}"
    )

    print(
        "Similarity:",
        result["score"]
    )

    print(
        "Text:",
        result["text"]
    )
