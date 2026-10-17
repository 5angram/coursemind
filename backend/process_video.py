from transcript import get_transcript
from chunker import chunk_test
from cleaner import clean_transcript

def process_video(video_id , title=""):
    print("\n================processing video===============")
    print("video_id:",video_id)
    print("title   :",title)


    #transcript

    transcript = get_transcript(video_id)

    if not transcript:
        print("transcript not found!!")
        return None

    print("transcript fetched successfully!!")

    #clean transcript

    text = clean_transcript(transcript["text"])

    print("transcript Length:",len(text))

    #chunking

    chunks = chunk_test(
        text ,
        chunk_size=500,
        overlap=100
    )

    print("no. of chunks:",len(chunks))

    #return processed data
    result = {
        "video_id":video_id,
        "title":title,
        "transcript":text,
        "chunks":chunks
    }

    print("\n==============video processed==============")
    return result


if __name__ == "__main__":
    video_id = input("enter video id:").strip()
    title = input("enter title:").strip()

    result = process_video(video_id,title)

    if result:
        print("\nFirst chunk")
        print(result["chunks"][0])
