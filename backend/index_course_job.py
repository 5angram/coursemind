import os
import sys
import json
import traceback

from playlist import get_playlist_video
from video_pipeline import process_video

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VECTOR_DIR = os.path.join(BASE_DIR , "data" , "vector")
JOB_DIR = os.path.join(BASE_DIR ,"data","index_jobs")
COURSE_MANIFEST_DIR = os.path.join(BASE_DIR , "data" , "course_manifests")


def save_status(playlist_id , status):
    os.makedirs(JOB_DIR , exist_ok=True)

    status_file = os.path.join(JOB_DIR , f"{playlist_id}.json")

    temp_file = status_file + ".tmp"

    with open(temp_file , "w" , encoding="utf-8") as file:
        json.dump(status , file , indent=2 , ensure_ascii=False)

    os.replace(temp_file,status_file)


def save_course_manifest(playlist_id , videos):
    os.makedirs(COURSE_MANIFEST_DIR , exist_ok=True)

    manifest = {
        "playlist_id":playlist_id,
        "total_videos":len(videos),
        "videos":[
            {
                "video_number":video.get("video_number",index),
                "video_id":video["video_id"],
                "title":video.get("title") or video["video_id"]
            }
            for index , video in enumerate(videos , start=1)
        ]
    }

    manifest_file = os.path.join(
        COURSE_MANIFEST_DIR,
        f"{playlist_id}.json"
    )

    temp_file = manifest_file + ".tmp"

    with open(temp_file , "w" , encoding="utf-8") as file:
        json.dump(manifest,file,indent=2,ensure_ascii=False)

    os.replace(temp_file,manifest_file)

    print("course manifest saved:",manifest_file)


def has_valid_vector(video_id):
    vector_file = os.path.join(VECTOR_DIR,f"{video_id}.json")

    if not os.path.exists(VECTOR_DIR):
        return False

    try:
        with open(vector_file,"r",encoding="utf-8") as file:
            records = json.load(file)

        return isinstance(records,list) and len(records)>0

    except(OSError , json.JSONDecodeError):
        return False

def run_indexing(playlist_url , playlist_id):
    status = {
        "playlist_id": playlist_id,
        "status": "running",
        "total": 0,
        "processed": 0,
        "successful": 0,
        "skipped": 0,
        "failed": 0,
        "current_video": "",
        "failed_videos": [],
        "error": None
    }

    try:
        os.makedirs(VECTOR_DIR,exist_ok=True)

        save_status(playlist_id , status)
        print(f"\nIndex playlist:{playlist_id}")

        videos = get_playlist_video(playlist_url)
        status["total"] = len(videos)
        save_status(playlist_id , status)

        save_course_manifest(playlist_id, videos)

        for video in videos:
            video_id = video["video_id"]
            title = video.get("title") or video_id

            status["current_video"] = title
            save_status(playlist_id , status)

            print(
                f"\n[{status.get('processed',0)+1}/{status['total']}]"
                f"{title}({video_id})"
            )

            try:
                if has_valid_vector(video_id):
                    status["skipped"] = status.get("skipped" ,0)+1
                    print("exisiting vector found;skipping")
                else:
                    result = process_video(video_id)

                    if result:
                        status["successful"] = status.get("successful",0)+1
                        print("Video processed successfully.")
                    else:
                        status["failed"] = status.get("failed" , 0)+1
                        status["failed_videos"].append({
                            "video_id":video_id,
                            "title":title
                        })
            except Exception as error:
                status["failed"] = status.get("failed",0)+1
                status["failed_videos"].append({
                    "video_id":video_id,
                    "title":title,
                    "error":str(error),
                    "traceback": traceback.format_exc()
                })
                print(f"failed to process {video_id}:{error}")
                traceback.print_exc()

            finally:
                status["processed"] = status.get("processed",0)+1
                save_status(playlist_id , status)

        status["status"] ="completed"
        status["current_video"] = ""

        print("\nPlaylist indexing finished.")
        print(
            f"Total :{status['total']} | "
            f"Newly Indexed:{status['successful']} | "
            f"Skipped:{status['skipped']} | "
            f"Failed:{status["failed"]}"
        )
    except Exception as error:
        status["status"] = "failed"
        status["error"] = str(error)
        status["traceback"] = traceback.format_exc()

        print("playlist indexing failed",error)
        traceback.print_exc()

    finally:
        save_status(playlist_id , status)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage:python index_course_job.py Playlist_url Playlist_id"
        )

    run_indexing(sys.argv[1],sys.argv[2])
