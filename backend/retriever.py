
import os
import json
import numpy as np

from backend.embedding import create_embedding


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

VECTOR_DIR = os.path.join(
    BASE_DIR,
    "data",
    "vector"
)


# =====================================================
# COSINE SIMILARITY
# =====================================================

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    denominator = (
        np.linalg.norm(a) * np.linalg.norm(b)
    )

    if denominator == 0:
        return 0

    return np.dot(a, b) / denominator


# =====================================================
# LOAD VECTOR FILE
# =====================================================

def load_vector(video_id):
    file_path = os.path.join(
        VECTOR_DIR,
        f"{video_id}.json"
    )

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"video file not found {file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def _select_diverse_results(results, top_k, max_per_video=3):
    """Select high-scoring chunks without letting one video dominate."""
    selected = []
    per_video_count = {}

    for item in results:
        video_id = item.get("video_id")
        if video_id is not None:
            count = per_video_count.get(video_id, 0)
            if count >= max_per_video:
                continue
            per_video_count[video_id] = count + 1

        selected.append(item)
        if len(selected) >= top_k:
            break

    return selected


# =====================================================
# LECTURE-LEVEL RETRIEVAL
# Existing behavior preserved
# =====================================================

def retrieve(
    question,
    video_id,
    top_k=5,
    min_similarity=0.48
):
    print("\n========== RETRIEVING ==========")
    print("Question:", question)
    print("Video ID:", video_id)

    # Create question embedding.
    question_embedding = create_embedding(
        [question]
    )[0]

    # Load vectors for this video only.
    vectors = load_vector(video_id)

    results = []

    # Calculate similarity for each chunk.
    for item in vectors:
        similarity = cosine_similarity(
            question_embedding,
            item["embedding"]
        )

        results.append({
            "chunk_id": item["chunk_id"],
            "text": item["text"],
            "similarity": float(similarity)
        })

    # Sort chunks by similarity.
    results.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    print("\n========== TOP SIMILARITIES ==========")

    for result in results[:top_k]:
        print(
            f"Chunk {result['chunk_id']} "
            f"| Similarity: {result['similarity']:.4f}"
        )

    # Apply minimum similarity threshold.
    filtered_results = [
        result
        for result in results[:top_k]
        if result["similarity"] >= min_similarity
    ]

    print("\nMinimum similarity:", min_similarity)
    print("Relevant chunks:", len(filtered_results))

    if not filtered_results:
        print("No sufficiently relevant chunks found.")
        return []

    return filtered_results


# =====================================================
# COURSE-LEVEL RETRIEVAL
# Searches all videos in the selected course
# =====================================================

def retrieve_course(
    question,
    video_ids,
    top_k=5,
    min_similarity=0.48,
    video_titles=None
):
    print("\n========== COURSE RETRIEVAL ==========")
    print("Question:", question)
    print("Videos in selected course:", len(video_ids))

    # Create the question embedding only once.
    question_embedding = create_embedding(
        [question]
    )[0]

    results = []

    # -------------------------------------------------
    # LOAD AND SCORE ALL VIDEOS
    # -------------------------------------------------

    for video_id in video_ids:

        vector_file = os.path.join(
            VECTOR_DIR,
            f"{video_id}.json"
        )

        # Skip videos without a vector file.
        if not os.path.isfile(vector_file):
            print("Skipping missing vector:", video_id)
            continue

        try:
            vectors = load_vector(video_id)

        except (OSError, json.JSONDecodeError) as error:
            print(
                f"Skipping unreadable vector "
                f"{video_id}: {error}"
            )
            continue

        title = (video_titles or {}).get(
            video_id,
            video_id
        )

        # Score every chunk from this video.
        for item in vectors:
            similarity = cosine_similarity(
                question_embedding,
                item["embedding"]
            )

            results.append({
                "video_id": video_id,
                "video_title": title,
                "chunk_id": item["chunk_id"],
                "text": item["text"],
                "similarity": float(similarity)
            })

    # -------------------------------------------------
    # IMPORTANT: SORT AFTER PROCESSING EVERY VIDEO
    # This block must remain OUTSIDE the video loop.
    # -------------------------------------------------

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    print("\nTop 10 course retrieval scores:")

    for item in results[:10]:
        print(
            f"Video: {item['video_title']} | "
            f"Video ID: {item['video_id']} | "
            f"Chunk: {item['chunk_id']} | "
            f"Similarity: {item['similarity']:.4f}"
        )

    print("Total chunks searched:", len(results))
    print("Minimum similarity threshold:", min_similarity)

    # -------------------------------------------------
    # FILTER AND SELECT TOP RESULTS
    # -------------------------------------------------

    # Apply the threshold first, then limit repeated chunks from one video.
    # This gives other relevant lectures a chance to contribute evidence.
    threshold_results = [
        item
        for item in results
        if item["similarity"] >= min_similarity
    ]

    filtered_results = _select_diverse_results(
        threshold_results,
        top_k=top_k,
        max_per_video=3
    )

    print("Chunks above threshold:", len(threshold_results))
    print("Relevant chunks after diversity selection:", len(filtered_results))

    if not filtered_results:
        print("No sufficiently relevant chunks found.")
        return []

    return filtered_results
