from transcript import get_transcript
from chunker import chunk_test

video_id = "N4gJDGdhpLw"

result = get_transcript(video_id)


print("\n========== RESULT ==========")

print("Language:", result["language"])
print("Language code:", result["language_code"])
print("Generated:", result["is_generated"])

print("\nTranscript:")
print(result["text"][:1000])

print("\n=>print first 3 snippets...")
for item in result["snippets"][:3]:
    print(item)

chunks = chunk_test(
    result["snippets"],
    chunk_size=500,
    overlap=100
)

print("\n========== CHUNKS ==========")

print("Number of chunks:", len(chunks))

print("\nFirst chunk:")

print("Start:", chunks[0]["start"])
print("End:", chunks[0]["end"])
print("Text:", chunks[0]["text"][:1000])