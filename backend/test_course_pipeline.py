from course_pipeline import process_playlist

playlist_url = input("enter url:")

course = process_playlist(playlist_url)

print("\n========== COURSE COMPLETE ==========")

print("no. of video:",len(course))

for video in course[:3]:
    print("\n------------------------------")

    print("Video:", video["video_number"])
    print("Title:", video["title"])
    print("Language:", video["language"])
    print("Language code:", video["language_code"])
    print("Generated:", video["is_generated"])
    print("Chunks:", len(video["chunks"]))

    if video["chunks"]:

        print("\nFirst chunk:")
        print(video["chunks"][0])