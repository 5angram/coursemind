from retriever import retrieve
from context_builder import build_context

video_id = "N4gJDGdhpLw"

query = "what is permutations?"

results = retrieve(
    video_id,
    query,
    top_k=3,
    threshold=0.3
)

context = build_context(results)

print(context)