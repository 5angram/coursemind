"""Build a clearly attributed context block from retrieved course chunks."""


def build_context(results):
    """Format retrieved chunks with their lecture identity and chunk ID.

    Metadata is included so the LLM can distinguish evidence from different
    videos and avoid treating a partial operation as a complete explanation.
    """
    context_parts = []

    for result in results:
        title = str(result.get("video_title") or "Unknown lecture").strip()
        video_id = str(result.get("video_id") or "unknown-video").strip()
        chunk_id = result.get("chunk_id", "unknown")
        text = str(result.get("text") or "").strip()

        if not text:
            continue

        context_parts.append(
            f"[SOURCE: {title} | video_id={video_id} | chunk_id={chunk_id}]\n{text}"
        )

    return "\n\n---\n\n".join(context_parts)
