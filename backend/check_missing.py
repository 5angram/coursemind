import os

from playlist import get_playlist_video


# Your playlist URL
PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLfqMhTWNBTe137I_EPQd34TsgV6IO55pt"

# Vector folder
VECTOR_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "vector"
)


print("========== CHECKING VECTORS ==========")

videos = get_playlist_video(PLAYLIST_URL)

print("Playlist videos:", len(videos))


missing = []


for video in videos:

    video_id = video["video_id"]

    vector_file = os.path.join(
        VECTOR_DIR,
        f"{video_id}.json"
    )

    if not os.path.exists(vector_file):

        missing.append(video)


print("\n========== MISSING VIDEOS ==========")


if not missing:

    print("All videos have vector files!")

else:

    for video in missing:

        print(
            f"\n[{video['video_number']}/{len(videos)}] "
            f"{video['title']}"
        )

        print(
            "Video ID:",
            video["video_id"]
        )


print("\n====================================")
print("Missing:", len(missing))
print("====================================")