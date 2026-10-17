from video_pipeline import process_video


video_id = "RjxD6UXGlhc"

result = process_video(video_id)

if result:
    print("\n✅ Missing video processed successfully!")
else:
    print("\n❌ Failed to process missing video.")