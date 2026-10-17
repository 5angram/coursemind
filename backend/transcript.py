import os
import json

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    IpBlocked,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "transcripts"
)

os.makedirs(CACHE_DIR,exist_ok=True)

def get_transcript(video_id):


    cache_file = os.path.join(
        CACHE_DIR,
        f"{video_id}.json"
    )

    if os.path.exists(cache_file):
        print("loading transcript....")

        with open(cache_file , "r" , encoding="utf-8") as file:
            return json.load(file)

    print("not found in cache")
    print("fetching from youtube")


    try:

        api = YouTubeTranscriptApi()

        transcripts = api.list(video_id)

        selected_transcript = None

        # for transcript in transcripts:
        #     if transcript.language_code=="en":
        #         selected_transcript = transcript
        #         break

        if selected_transcript is None:
            for transcript in transcripts:
                if transcript.language_code=="hi":
                    selected_transcript = transcript
                    break

        if selected_transcript is None:

            selected_transcript = next(
                iter(transcripts)
            )


        # if selected_transcript is None:
        #     raise Exception("no transcript found!!!")

        print(
            "Selected:",selected_transcript.language,
            "|",selected_transcript.language_code,
            "| Generated:",selected_transcript.is_generated
        )

        fetched = selected_transcript.fetch()

        text = " ".join(
            item.text for item in fetched
        )


        result = {
            "video_id":video_id,
            "language":selected_transcript.language,
            "language_code":selected_transcript.language_code,
            "is_generated":selected_transcript.is_generated,
            "text":text
        }

        with open(cache_file , "w" , encoding="utf-8") as file:
            json.dump(result , file , ensure_ascii=False , indent=4)

        print("transcript saved")

        return result

    except IpBlocked:
        print("Youtube blocked transcript request....")

        return{
            "video_id":video_id,
            "status":"failed",
            "reason":"ip_blocked",
            "text":""
        }
    except TranscriptsDisabled:

        print("Transcripts are disabled for this video.")

        return {
            "video_id": video_id,
            "status": "failed",
            "reason": "transcripts_disabled",
            "text": ""
        }


    except NoTranscriptFound:

        print("No transcript was found.")

        return {
            "video_id": video_id,
            "status": "failed",
            "reason": "no_transcript",
            "text": ""
        }


    except VideoUnavailable:

        print("Video is unavailable.")

        return {
            "video_id": video_id,
            "status": "failed",
            "reason": "video_unavailable",
            "text": ""
        }


    except Exception as e:

        print(
            "Unexpected transcript error:",
            str(e)
        )

        return {
            "video_id": video_id,
            "status": "failed",
            "reason": "unknown_error",
            "error": str(e),
            "text": ""
        }
