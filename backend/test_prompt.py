from retriever import retrieve
from context_builder import build_context
from prompt_builder import build_prompt

video_id = "N4gJDGdhpLw"

question = "what is permutation?"

results = retrieve(
    video_id,
    question,
    top_k=3,
    threshold=0.3
)

context = build_context(results)

prompt = build_prompt(question,context)


print("\n========== PROMPT ==========\n")
print(prompt)