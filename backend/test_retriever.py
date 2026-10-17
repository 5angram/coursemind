from retriever import retrieve

video_id = "VTLCoHnyACE"

question = input(
    "Enter your question: "
).strip()


results = retrieve(
    question,
    video_id,
    top_k=5
)



print("\n========== RESULTS ==========")


for result in results:

    print("\n----------------------------")
    print(
        "Chunk:",
        result["chunk_id"]
    )

    print(
        "Similarity:",
        result["similarity"]
    )

    print(
        "Text:",
        result["text"]
    )