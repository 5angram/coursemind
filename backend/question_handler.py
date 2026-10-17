"""Question-answering orchestration for CourseMind's course-level tutor.

This module coordinates follow-up resolution, course retrieval, context building,
and answer generation. API routing remains in app.py.
"""

import json
import os
import re
import traceback
from typing import Any

from backend.context_builder import build_context
from backend.llm import generate_answer
from backend.prompt_builder import build_prompt
from backend.retriever import retrieve_course

COURSE_MANIFEST_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "course_manifests",
)

NO_CONTEXT_ANSWER = (
    "I couldn't find sufficiently relevant information "
    "in the selected course content."
)


def resolve_course_retrieval_query(question: str, history: list | None) -> str:
    """Rewrite a follow-up as a standalone query using prior user questions.

    Assistant answers are intentionally excluded from topic resolution because
    they may contain errors or drift to an unrelated topic.
    """
    question = (question or "").strip()
    # Chat UIs sometimes prefix questions with list numbering; it is not intent.
    question = re.sub(r"^\s*\d+[.)]\s*", "", question).strip()
    if not history:
        return question

    recent_history = [turn for turn in history[-8:] if isinstance(turn, dict)]
    previous_questions = [
        str(turn.get("question", "")).strip()
        for turn in recent_history
        if str(turn.get("question", "")).strip()
    ]
    if not previous_questions:
        return question

    # Resolve simple pronoun follow-ups deterministically before calling the LLM.
    # This prevents a malformed LLM rewrite (e.g. "Compare its with binary search")
    # from losing the previous topic and retrieving the wrong lecture.
    if re.search(r"\b(it|its|this|that|these|those)\b", question, flags=re.IGNORECASE):
        prior_topic = None
        # Scan newest-to-oldest user questions; the latest explicit topic wins.
        for previous_question in reversed(previous_questions):
            found_topics = _find_named_topics(previous_question)
            if found_topics:
                prior_topic = found_topics[0]
                break
        if prior_topic:
            resolved = re.sub(
                r"\b(its|it|this|that|these|those)\b",
                lambda match: prior_topic if match.group(0).lower() in {"it", "this", "that"} else prior_topic,
                question,
                flags=re.IGNORECASE,
            )
            resolved = re.sub(r"^\s*\d+[.)]\s*", "", resolved).strip()
            print("Resolved follow-up deterministically:", resolved)
            return resolved

    history_text = "\n".join(
        f"Turn {index + 1}: {previous_question}"
        for index, previous_question in enumerate(previous_questions)
    )
    latest_user_question = previous_questions[-1]

    resolver_prompt = f"""Task: rewrite the current user question into ONE standalone search query for retrieving relevant passages from a course transcript.

Rules:
1. Decide whether the current question continues the existing topic or explicitly starts a new topic.
2. Resolve pronouns and short follow-ups using the most recent user-established topic.
3. Use user questions, not assistant answers, to establish topic continuity.
4. A new explicit topic replaces the previous topic. Later follow-ups refer to the newest explicit topic.
5. Preserve the user's requested task, including requests for examples, code, comparisons, or step-by-step explanations.
6. Do not answer the question or add unrelated requirements. Return only one standalone query, with no label or explanation.
7. If history does not establish the topic, do not invent one; return the current question unchanged.

RECENT USER QUESTIONS (oldest first):
{history_text}

LATEST PREVIOUS USER QUESTION:
{latest_user_question}

CURRENT USER QUESTION:
{question}

STANDALONE RETRIEVAL QUERY:"""

    try:
        resolved = str(generate_answer(resolver_prompt)).strip().strip('"').strip("'")
        if not resolved or len(resolved) > 1000 or "\n" in resolved:
            return question
        # Reject numbering and unresolved pronouns in model-generated rewrites.
        resolved = re.sub(r"^\s*\d+[.)]\s*", "", resolved).strip()
        if re.search(r"\b(it|its|this|that|these|those)\b", resolved, flags=re.IGNORECASE):
            print("Resolver left an unresolved pronoun; using original question.")
            return question
        print("Retrieval query resolver history turns:", len(previous_questions))
        print("Resolved retrieval query:", resolved)
        return resolved
    except Exception as error:
        print("Question-context resolution failed; using original question:", str(error))
        return question



# Common named topics that can be grounded against lecture titles. Keep this
# deliberately small and explicit; unknown topics continue through global search.
_TOPIC_ALIASES = {
    "merge sort": ("merge sort",),
    "binary search": ("binary search",),
    "bubble sort": ("bubble sort",),
    "selection sort": ("selection sort",),
    "insertion sort": ("insertion sort",),
    "quick sort": ("quick sort", "quicksort"),
    "quicksort": ("quick sort", "quicksort"),
    "linear search": ("linear search",),
    "binary tree": ("binary tree", "binary trees"),
    "linked list": ("linked list", "linked lists"),
    "stack": ("stack", "stacks"),
    "queue": ("queue", "queues"),
    "recursion": ("recursion",),
    "dynamic programming": ("dynamic programming",),
}


def _find_named_topics(query: str) -> list[str]:
    """Return recognized topic names explicitly present in the query."""
    normalized = " ".join((query or "").lower().replace("-", " ").split())
    matches = [topic for topic in _TOPIC_ALIASES if topic in normalized]
    # Avoid counting quick sort and quicksort as two different topics.
    return list(dict.fromkeys(matches))


def _videos_for_topic(topic: str, video_titles: dict[str, str]) -> list[str]:
    aliases = _TOPIC_ALIASES.get(topic, (topic,))
    return [
        video_id
        for video_id, title in video_titles.items()
        if any(alias in str(title).lower() for alias in aliases)
    ]

def _retrieve_topic_aware(
    query: str,
    video_ids: list[str],
    video_titles: dict[str, str],
    top_k: int,
) -> list[dict[str, Any]]:
    """Prefer named lecture videos; for comparisons, reserve evidence for each side.

    If a named topic has no matching lecture title, global semantic retrieval remains
    the fallback so title matching does not silently discard potentially useful evidence.
    """
    topics = _find_named_topics(query)
    if not topics:
        return retrieve_course(
            question=query, video_ids=video_ids, top_k=top_k, video_titles=video_titles
        )

    topic_video_ids = {topic: _videos_for_topic(topic, video_titles) for topic in topics}
    available_topics = [topic for topic in topics if topic_video_ids[topic]]

    if not available_topics:
        return retrieve_course(
            question=query, video_ids=video_ids, top_k=top_k, video_titles=video_titles
        )

    # For a comparison, search each recognized topic independently, then merge results.
    # For a single topic, constrain retrieval to its lecture(s) when available.
    if len(available_topics) == 1 and len(topics) == 1:
        topic = available_topics[0]
        scoped = retrieve_course(
            question=query,
            video_ids=topic_video_ids[topic],
            top_k=top_k,
            video_titles=video_titles,
        )
        if scoped:
            return scoped

    per_topic_k = max(1, (top_k + len(available_topics) - 1) // len(available_topics))
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for topic in available_topics:
        topic_query = f"{topic}: {query}"
        topic_results = retrieve_course(
            question=topic_query,
            video_ids=topic_video_ids[topic],
            top_k=per_topic_k,
            video_titles=video_titles,
        )
        for result in topic_results:
            key = (str(result.get("video_id", "")), str(result.get("chunk_id", "")))
            if key not in seen:
                seen.add(key)
                merged.append(result)

    # If title-scoped retrieval produced no chunks, fall back to the global search.
    if not merged:
        return retrieve_course(
            question=query, video_ids=video_ids, top_k=top_k, video_titles=video_titles
        )

    merged.sort(key=lambda item: item.get("similarity", 0.0), reverse=True)
    return merged[:max(top_k, len(available_topics))]

def handle_course_question(
    playlist_id: str,
    question: str,
    history: list | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """Run the full course question-answering pipeline and return API data."""
    try:
        playlist_id = (playlist_id or "").strip()
        question = (question or "").strip()

        if not playlist_id or "/" in playlist_id or "\\" in playlist_id:
            return {"message": "invalid playlist ID"}
        if not question:
            return {"message": "Please enter a question.", "answer": NO_CONTEXT_ANSWER, "sources": []}

        manifest_file = os.path.join(COURSE_MANIFEST_DIR, f"{playlist_id}.json")
        if not os.path.isfile(manifest_file):
            return {
                "message": "Course manifest not found. Please index this course first.",
                "playlist_id": playlist_id,
            }

        with open(manifest_file, "r", encoding="utf-8") as file:
            manifest = json.load(file)

        videos = manifest.get("videos", [])
        if not videos:
            return {
                "message": "No videos found in this course manifest.",
                "answer": "This course does not contain any indexed lectures.",
                "sources": [],
            }

        video_ids = [video["video_id"] for video in videos if video.get("video_id")]
        video_titles = {
            video["video_id"]: video.get("title", video["video_id"])
            for video in videos
            if video.get("video_id")
        }

        retrieval_question = resolve_course_retrieval_query(question, history or [])
        print("\n========== COURSE RETRIEVAL QUERY ==========")
        print("Original question:", question)
        print("Resolved retrieval query:", retrieval_question)

        requested_top_k = max(1, min(int(top_k), 20))
        results = _retrieve_topic_aware(
            query=retrieval_question,
            video_ids=video_ids,
            video_titles=video_titles,
            top_k=requested_top_k,
        )

        if not results:
            return {"playlist_id": playlist_id, "answer": NO_CONTEXT_ANSWER, "sources": []}

        context = build_context(results)
        # Log source attribution only by default; full transcript text can be enabled
        # locally when debugging retrieval with COURSEMIND_DEBUG_CONTEXT=1.
        print("Retrieved context sources:")
        for result in results:
            print(
                f"  - {result.get('video_title', 'Unknown lecture')} "
                f"(video_id={result.get('video_id', 'unknown')}, "
                f"chunk_id={result.get('chunk_id', 'unknown')}, "
                f"similarity={result.get('similarity', 0.0):.4f})"
            )
        if os.getenv("COURSEMIND_DEBUG_CONTEXT") == "1":
            print("========== FULL COURSE CONTEXT ==========")
            print(context)
        # Use the resolved standalone query, not raw history, so earlier incorrect
        # assistant answers cannot pull generation toward a different topic.
        prompt = build_prompt(retrieval_question, context, [])
        prompt += """

ADDITIONAL ACCURACY CHECKS:
- Answer only what the supplied course context supports.
- For a comparison, explain each named concept separately and compare them only where the context supports it.
- Do not state that a searching algorithm sorts data unless the supplied context explicitly says so.
- For worked examples, check each intermediate step and the final result for consistency before responding.
- For merge sort, do not present merging two already-sorted arrays as a complete merge-sort example. If context supports it, show divide -> recursively sort halves -> merge; otherwise clearly say the context only demonstrates the merge step.
- Never switch to a different comparison (for example, binary search vs. linear search) when the user asked to compare another pair of topics.
- Preserve the exact topics and task requested by the user. Do not add examples or time-complexity requirements unless asked or needed to answer the question.
- If the retrieved context does not contain enough evidence for a requested part, state that limitation instead of guessing.
"""
        answer = generate_answer(prompt)

        return {
            "playlist_id": playlist_id,
            "answer": answer,
            "sources": [
                {
                    "video_id": result["video_id"],
                    "video_title": result["video_title"],
                    "chunk_id": result["chunk_id"],
                    "similarity": result["similarity"],
                }
                for result in results
            ],
        }
    except Exception as error:
        print("Course question error:", str(error))
        traceback.print_exc()
        return {"message": "Failed to generate course answer.", "error": str(error)}
