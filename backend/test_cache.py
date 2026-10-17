import os
import json

from transcript import get_transcript

video_id = "test_video"

os.makedirs("data/transcript" , exist_ok=True)

test_data = {
    "video_id": video_id,

    "language": "Hindi (auto-generated)",

    "language_code": "hi",

    "is_generated": True,

    "text": "यह एक टेस्ट ट्रांसक्रिप्ट है।"
}

cache_file = f"data/transcript/{video_id}.json"

with open(cache_file , "w" , encoding="utf-8") as file:
    json.dump(test_data , file , ensure_ascii=False , indent=4)

print("cache created....")

result = get_transcript(video_id)



print("\n========== RESULT ==========")

print("Language:", result["language"])

print("Language code:", result["language_code"])

print("Transcript:", result["text"])