
import os
import json

from playlist import get_playlist_video

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MANIFEST_DIR = os.path.join(
    BASE_DIR,
    "backend",
    "data",
    "course_manifests"
)

COURSES = {
    "PLfqMhTWNBTe137I_EPQd34TsgV6IO55pt": "DSA",
    "PLKnIA16_Rmvbr7zKYQuBfsVkjoLcJgxHH": "Machine Learning"
}

os.makedirs(MANIFEST_DIR, exist_ok=True)

for playlist_id, course_name in COURSES.items():
    print(f"\nFetching {course_name} playlist...")

    playlist_url = (
        f"https://www.youtube.com/playlist?list={playlist_id}"
    )

    videos = get_playlist_video(playlist_url)

    manifest = {
        "playlist_id": playlist_id,
        "course_name": course_name,
        "total_videos": len(videos),
        "videos": videos
    }

    manifest_file = os.path.join(
        MANIFEST_DIR,
        f"{playlist_id}.json"
    )

    with open(manifest_file, "w", encoding="utf-8") as file:
        json.dump(
            manifest,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved {len(videos)} videos to {manifest_file}")

print("\nManifest generation finished.")
