from playlist import get_playlist_video
from video_pipeline import process_video

def process_playlist(playlist_url):
    print("==========course processing============")

    videos = get_playlist_video(playlist_url)

    total = len(videos)

    print("total videos :",total)
    successful = 0
    failed = 0
    failed_videos = []

    for video in videos:
        number = video["video_number"]
        title = video["title"]
        video_id = video["video_id"]

        print("\n----------------------------------------")
        print(f"[{number}/{total}] {title}")
        print(f"Video ID: {video_id}")
        print("----------------------------------------")

        try:
            result = process_video(video_id)

            if result:
                successful += 1
                print("processed successfully!!")
            else:
                failed += 1
                print("processing failed!!")
                failed_videos.append({
                    "video_number": number,
                    "title": title,
                    "video_id": video_id
                })

        except Exception as e:
            failed +=1

            print("error:",e)
            continue

    print("\n========== COURSE COMPLETE ==========")

    print("Total videos:", total)
    print("Successful:", successful)
    print("Failed:", failed)

    print("\n========== FAILED VIDEOS ==========")

    if failed_videos:

        for video in failed_videos:

            print(
                f"[{video['video_number']}] "
                f"{video['title']}"
            )

            print(
                f"Video ID: {video['video_id']}"
            )

            if "error" in video:

                print(
                    f"Error: {video['error']}"
                )

    else:

        print("No failed videos.")


    return failed_videos
