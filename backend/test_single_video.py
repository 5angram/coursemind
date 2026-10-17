from transcript import get_transcript



video_id = "LusTv0RlnSU"


print("========== TRANSCRIPT ==========")

result = get_transcript(video_id)


if result.get("status") == "failed":
    print("\n❌ Transcript unavailable")

    print(
        "Reason:",
        result["reason"]
    )

else:

    print(
        "Language:",
        result["language"]
    )

    print(
        "Language code:",
        result["language_code"]
    )

    print(
        "\nTranscript:"
    )

    print(
        result["text"][:1000]
    )