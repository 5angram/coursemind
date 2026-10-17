from video_pipeline import process_video

video_id = "LusTv0RlnSU"

success = process_video(
    video_id
)

if success:

    print(
        "\n✅ Video processed successfully!"
    )

else:

    print(
        "\n❌ Video processing failed."
    )