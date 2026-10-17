import yt_dlp

def get_playlist_video(playlist_url):

    options = {
        "extract_flat":True,
        "quiet":True
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(
            playlist_url,
            download=False
        )

    videos = []

    for index , video in enumerate(info["entries"] , start=1):
        videos.append({
            "video_number":index,
            "video_id" :video["id"],
            "title":video["title"]
        })

    return videos