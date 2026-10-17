from transcript import get_transcript
from cleaner import clean_transcript
from chunker import chunk_test
from embedding import create_embedding
from vector_store import save_vector

def process_video(video_id):
    print("\n===========proceesing video=============")
    print(f"video id:{video_id}")

    #transcript
    transcript = get_transcript(video_id)


    if transcript.get("status") == "failed":
        print(
            "❌ Transcript failed:",
            transcript.get("reason")
        )

        return False

    raw_text = transcript["text"]
    print(
        "transcript fetched successfully!!"
    )

    #cleaning
    cleaned_text = clean_transcript(raw_text)
    print("transcript Length:",len(cleaned_text))

    #chunking
    chunks = chunk_test(
        cleaned_text,
        chunk_size=100,
        overlap=20
    )
    print("no. of chunks:",len(chunks))

    #embedding
    embeddings = create_embedding(chunks)

    print("embedding shape:",embeddings.shape)

    #vector records
    save_vector(
        video_id,
        chunks,
        embeddings
    )
    print("=============video complete============")

    return True