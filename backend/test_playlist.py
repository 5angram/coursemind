from playlist import get_playlist_video

playlist_url = input("enter your url:")

videos = get_playlist_video(playlist_url)


print("\n========== PLAYLIST ==========")

for video in videos:
    print(
        f"{video['video_number']}. "
        f"{video['title']} "
        f"{video['video_id']}"
    )