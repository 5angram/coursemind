from retriever import retrieve
from context_builder import build_context
from prompt_builder import build_prompt
from llm import generate_answer


video_id = "VTLCoHnyACE"

question = input(
    "Enter your question: "
).strip()


# 1. Retrieve relevant chunks
results = retrieve(
    video_id=video_id,
    question=question,
    top_k=5
)


# 2. Build context
context = build_context(results)


# 3. Build prompt
prompt = build_prompt(
    question,
    context
)


# 4. Generate answer
answer = generate_answer(prompt)


# 5. Display answer
print("\n========== ANSWER ==========")
print(answer)


# 6. Display sources
print("\n========== SOURCES ==========")

for result in results:

    print(
        f"Chunk {result['chunk_id']} "
        f"| Similarity: "
        f"{result['similarity']:.4f}"
    )