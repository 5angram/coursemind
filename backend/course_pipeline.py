import os
import json
from playlist import get_playlist_video
from cleaner import clean_transcript
from chunker import chunk_test
from transcript import get_transcript
from embedding import create_embedding

COURSE_DIR = "data/course"
VECTOR_DIR = "data/vector"

def process_playlist(playlist_url):

    os.makedirs(COURSE_DIR , exist_ok=True)
    os.makedirs(VECTOR_DIR , exist_ok=True)

    videos = get_playlist_video(playlist_url)

    course_data = []

    for video in videos:
        print("\n--------------------------------")

        print(
            f"processing{video['video_number']}"
            f"{video['title']}"
        )
        video_id = video["video_id"]

        try:
            #get transcript
            result = get_transcript(video_id)
            #clean the transcript
            cleaned_text = clean_transcript(result["text"])

            #create chunks
            chunks =  chunk_test(
                cleaned_text,
                chunk_size=100,
                overlap=20
            )

            print("Chunks:",len(chunks))

            #embedding
            print("creating embedding...")
            texts = [
                chunks["text"]
                for chunk in chunks
            ]

            embeddings = create_embedding(texts)
            print("embedding shape:",embeddings.shape)


            # video_data = {
            #     "video_number": video["video_number"],
            #     "video_id": video_id,
            #     "title": video["title"],
            #     "language": result["language"],
            #     "language_code": result["language_code"],
            #     "is_generated": result["is_generated"],
            #     "transcript": cleaned_text,
            #     "chunks": chunks
            # }

            # course_data.append(video_data)

            # print("✓ Done")
            # print("Language:", result["language_code"])
            # print("Chunks:", len(chunks))


            # progress_file = os.path.join(
            #     COURSE_DIR,
            #     "course_progress.json"
            # )

            # with open(progress_file,"w",encoding="utf-8") as file:
            #     json.dump(course_data , file , ensure_ascii=False , indent=4)

            # print("progress save")

        except Exception as e:
            print(f"✗ Failed: {e}")
            continue

    return course_data
