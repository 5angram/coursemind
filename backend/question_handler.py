"""Question-answering orchestration for CourseMind's course-level tutor."""

import json
import os
import re
import traceback
from typing import Any

from backend.llm import generate_answer

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


def resolve_course_retrieval_query(
    question: str,
    history: list | None,
) -> str:

    question = (
        question or ""
    ).strip()

    question = re.sub(
        r"^\s*\d+[.)]\s*",
        "",
        question,
    ).strip()

    if not history:
        return question

    recent_history = [
        turn
        for turn in history[-8:]
        if isinstance(turn, dict)
    ]

    previous_questions = [
        str(
            turn.get(
                "question",
                "",
            )
        ).strip()
        for turn in recent_history
        if str(
            turn.get(
                "question",
                "",
            )
        ).strip()
    ]

    if not previous_questions:
        return question

# ---------------------------------------------------------
# EXPLICIT TOPIC SAFETY CHECK
# ---------------------------------------------------------
#
# If the current question already explicitly names a known
# course topic, DO NOT send it through the LLM query resolver.
#
# Example:
#
#   "What is binary search?"
#
# must remain:
#
#   "What is binary search?"
#
# It must never be rewritten using previous conversation
# history.
#
# The LLM resolver is only needed for genuine follow-ups
# such as:
#
#   "What is its time complexity?"
#   "How does it work?"
#
# ---------------------------------------------------------

    explicit_topics = _find_named_topics(question)

    if explicit_topics:
        print(
            "Explicit topic detected; skipping LLM query resolver:",
            explicit_topics,
        )
        return question

# Resolve simple pronoun follow-ups deterministically before calling the LLM.

    if re.search(
        r"\b(it|its|this|that|these|those)\b",
        question,
        flags=re.IGNORECASE,
    ):

        prior_topic = None

        for previous_question in reversed(
            previous_questions
        ):

            found_topics = (
                _find_named_topics(
                    previous_question
                )
            )

            if found_topics:
                prior_topic = found_topics[0]
                break

        if prior_topic:

            resolved = re.sub(
                r"\b(its|it|this|that|these|those)\b",
                prior_topic,
                question,
                flags=re.IGNORECASE,
            )

            resolved = re.sub(
                r"^\s*\d+[.)]\s*",
                "",
                resolved,
            ).strip()

            print(
                "Resolved follow-up deterministically:",
                resolved,
            )

            return resolved

    history_text = "\n".join(
        f"Turn {index + 1}: {previous_question}"
        for index, previous_question
        in enumerate(
            previous_questions
        )
    )

    latest_user_question = (
        previous_questions[-1]
    )

    resolver_prompt = f"""
Rewrite the current user question into ONE standalone retrieval query.

Rules:

- Resolve pronouns using recent user questions.
- Preserve the exact topic.
- Preserve the exact requested task.
- Preserve comparison questions.
- Do not answer the question.
- Do not add information.
- Return only the rewritten query.

RECENT USER QUESTIONS:
{history_text}

LATEST PREVIOUS USER QUESTION:
{latest_user_question}

CURRENT USER QUESTION:
{question}

STANDALONE RETRIEVAL QUERY:
""".strip()

    try:

        resolved = str(
            generate_answer(
                resolver_prompt,
                max_tokens=200,
                temperature=0.0,
            )
        ).strip().strip('"').strip("'")

        if (
            not resolved
            or len(resolved) > 1000
            or "\n" in resolved
        ):
            return question

        resolved = re.sub(
            r"^\s*\d+[.)]\s*",
            "",
            resolved,
        ).strip()

        if re.search(
            r"\b(it|its|this|that|these|those)\b",
            resolved,
            flags=re.IGNORECASE,
        ):
            return question

        return resolved

    except Exception as error:

        print(
            "Question resolution failed:",
            str(error),
        )

        return question


_TOPIC_ALIASES = {
    "merge sort": ("merge sort",),
    "binary search": ("binary search",),
    "bubble sort": ("bubble sort",),
    "selection sort": ("selection sort",),
    "insertion sort": ("insertion sort",),
    "quick sort": (
        "quick sort",
        "quicksort",
    ),
    "quicksort": (
        "quick sort",
        "quicksort",
    ),
    "linear search": ("linear search",),
    "binary tree": (
        "binary tree",
        "binary trees",
    ),
    "linked list": (
        "linked list",
        "linked lists",
    ),
    "stack": (
        "stack",
        "stacks",
    ),
    "queue": (
        "queue",
        "queues",
    ),
    "recursion": ("recursion",),
    "dynamic programming": (
        "dynamic programming",
    ),
}


def _find_named_topics(
    query: str,
) -> list[str]:

    normalized = (
        " ".join(
            (query or "")
            .lower()
            .replace("-", " ")
            .split()
        )
    )

    matches = [
        topic
        for topic in _TOPIC_ALIASES
        if topic in normalized
    ]

    return list(
        dict.fromkeys(matches)
    )


def _videos_for_topic(
    topic: str,
    video_titles: dict[str, str],
) -> list[str]:

    aliases = _TOPIC_ALIASES.get(
        topic,
        (topic,),
    )

    return [
        video_id
        for video_id, title
        in video_titles.items()
        if any(
            alias in str(title).lower()
            for alias in aliases
        )
    ]


def _core_videos_for_topic(
    topic: str,
    video_titles: dict[str, str],
) -> list[str]:

    core_patterns = {
        "merge sort": (
            "merge sort algorithm",
        ),
        "binary search": (
            "binary search algorithm",
        ),
    }

    patterns = core_patterns.get(
        topic
    )

    if not patterns:
        return []

    return [
        video_id
        for video_id, title
        in video_titles.items()
        if any(
            pattern in str(title).lower()
            for pattern in patterns
        )
    ]


def _retrieve_topic_aware(
    query: str,
    video_ids: list[str],
    video_titles: dict[str, str],
    top_k: int,
) -> list[dict[str, Any]]:

    topics = _find_named_topics(query)

    print(
        "Detected topics:",
        topics,
    )

    topic_video_ids = {
        topic: _videos_for_topic(
            topic,
            video_titles,
        )
        for topic in topics
    }

    print(
        "Topic video IDs:",
        topic_video_ids,
    )

    if not topics:
        return retrieve_course(
            question=query,
            video_ids=video_ids,
            top_k=top_k,
            video_titles=video_titles,
        )

    available_topics = [
        topic
        for topic in topics
        if topic_video_ids.get(topic)
    ]

    if not available_topics:
        return retrieve_course(
            question=query,
            video_ids=video_ids,
            top_k=top_k,
            video_titles=video_titles,
        )

    # ---------------------------------------------------------
    # SINGLE-TOPIC QUESTION
    # ---------------------------------------------------------

    if len(available_topics) == 1:

        topic = available_topics[0]

        core_video_ids = _core_videos_for_topic(
            topic,
            video_titles,
        )

        scoped_video_ids = (
            core_video_ids
            if core_video_ids
            else topic_video_ids[topic]
        )

        topic_query = f"{topic}: {query}"

        print(
            "\nTopic-specific retrieval query:",
            topic_query,
        )

        print(
            f"Videos used for topic "
            f"'{topic}': {scoped_video_ids}"
        )

        results = retrieve_course(
            question=topic_query,
            video_ids=scoped_video_ids,
            top_k=top_k,
            video_titles=video_titles,
        )

        # If the exact question does not retrieve enough evidence,
        # fall back to a topic-focused query.
        if not results:

            fallback_query = (
                f"{topic}: Explain {topic}"
            )

            print(
                "\nNo results for exact topic query."
            )

            print(
                "Fallback retrieval query:",
                fallback_query,
            )

            results = retrieve_course(
                question=fallback_query,
                video_ids=scoped_video_ids,
                top_k=top_k,
                video_titles=video_titles,
            )

        return results

    # ---------------------------------------------------------
    # MULTI-TOPIC / COMPARISON QUESTION
    # ---------------------------------------------------------

    per_topic_k = max(
        3,
        (
            top_k
            + len(available_topics)
            - 1
        )
        // len(available_topics),
    )

    merged = []
    seen = set()

    for topic in available_topics:

        core_video_ids = _core_videos_for_topic(
            topic,
            video_titles,
        )

        scoped_video_ids = (
            core_video_ids
            if core_video_ids
            else topic_video_ids[topic]
        )

        # First try the ORIGINAL comparison question.
        comparison_query = (
            f"{topic}: {query}"
        )

        print(
            "\nTopic-specific retrieval query:",
            comparison_query,
        )

        print(
            f"Videos used for topic "
            f"'{topic}': {scoped_video_ids}"
        )

        topic_results = retrieve_course(
            question=comparison_query,
            video_ids=scoped_video_ids,
            top_k=per_topic_k,
            video_titles=video_titles,
        )

        # -----------------------------------------------------
        # IMPORTANT FALLBACK
        # -----------------------------------------------------
        #
        # The comparison wording can lower cosine similarity
        # even when the lecture contains excellent evidence.
        #
        # Example:
        #
        # "merge sort: How is merge sort different from
        #  binary search?"
        #
        # may score 0.4795 against a Merge Sort chunk,
        # while:
        #
        # "merge sort: Explain merge sort"
        #
        # scores > 0.48.
        #
        # Therefore, if the comparison retrieval finds nothing,
        # retrieve the topic itself rather than losing that topic.
        # -----------------------------------------------------

        if not topic_results:

            fallback_query = (
                f"{topic}: Explain {topic}"
            )

            print(
                "\nNo sufficiently relevant results "
                f"for comparison query of '{topic}'."
            )

            print(
                "Fallback topic retrieval query:",
                fallback_query,
            )

            topic_results = retrieve_course(
                question=fallback_query,
                video_ids=scoped_video_ids,
                top_k=per_topic_k,
                video_titles=video_titles,
            )

        for result in topic_results:

            key = (
                str(
                    result.get(
                        "video_id",
                        "",
                    )
                ),
                str(
                    result.get(
                        "chunk_id",
                        "",
                    )
                ),
            )

            if key in seen:
                continue

            seen.add(key)
            merged.append(result)

    if not merged:

        return retrieve_course(
            question=query,
            video_ids=video_ids,
            top_k=top_k,
            video_titles=video_titles,
        )

    merged.sort(
        key=lambda item: item.get(
            "similarity",
            0.0,
        ),
        reverse=True,
    )

    # Keep enough evidence for every requested topic.
    return merged[
        :max(
            top_k,
            len(available_topics) * 3,
        )
    ]

def _format_retrieved_evidence(
    results: list[dict],
) -> str:
    """Convert Python-selected retrieval results into evidence for the LLM."""

    blocks = []

    for index, result in enumerate(results, start=1):
        text = str(
            result.get("text", "")
        ).strip()

        if not text:
            continue

        source = str(
            result.get(
                "video_title",
                "Unknown lecture",
            )
        ).strip()

        video_id = str(
            result.get(
                "video_id",
                "unknown",
            )
        ).strip()

        chunk_id = str(
            result.get(
                "chunk_id",
                "unknown",
            )
        ).strip()

        similarity = float(
            result.get(
                "similarity",
                0.0,
            )
        )

        blocks.append(
            f"[EVIDENCE {index}]\n"
            f"Source: {source}\n"
            f"Video ID: {video_id}\n"
            f"Chunk ID: {chunk_id}\n"
            f"Similarity: {similarity:.4f}\n"
            f"Exact course passage:\n"
            f"{text}"
        )

    return "\n\n".join(blocks)





def _is_comparison_question(query: str) -> bool:
    """Return True when the user explicitly asks for a comparison."""
    comparison_patterns = (
        r"\bdifferent\b",
        r"\bdifference\b",
        r"\bcompare\b",
        r"\bcomparison\b",
        r"\bvs\b",
        r"\bversus\b",
        r"\bcontrast\b",
    )

    query_lower = (query or "").lower()

    return any(
        re.search(pattern, query_lower)
        for pattern in comparison_patterns
    )


def _build_evidence_synthesis_prompt(
    question: str,
    evidence_context: str,
    comparison: bool = False,
) -> str:
    """Build the single evidence-grounded answer prompt."""

    if comparison:
        return f"""
You are CourseMind.

Compare the two topics in the user's question using ONLY the supplied course evidence.

QUESTION:
{question}

EVIDENCE:
{evidence_context}

Give a short comparison.
State only differences supported by the evidence.
Every factual sentence must end with its evidence citation: [1], [2], [3], or [4].

Return only the final answer.
""".strip()

    return f"""
You are CourseMind's answer-generation model.

Answer the user's question using the COURSE EVIDENCE below.

USER QUESTION:
{question}

COURSE EVIDENCE:
{evidence_context}

HOW TO ANSWER:

1. Build the answer directly from the supplied course evidence.
2. Use the course evidence as the factual source for every statement.
3. Write a short, clear answer that directly addresses the question.
4. Prefer simple explanations using wording supported by the evidence.
5. Combine related evidence when it clearly describes the same idea.
6. Preserve the meaning of the course evidence.
7. When the evidence gives only part of an answer, give only that supported part.
8. When a requested detail is not present in the evidence, leave that detail out.

CITATIONS:

- Every factual sentence MUST end with one or more evidence citations.
- Use only the evidence numbers supplied in the COURSE EVIDENCE.
- Format citations exactly like [1], [2], or [1][2].
- Place the citation immediately at the end of the sentence it supports.
- Do not place citations only at the end of a paragraph.
- Use the smallest number of citations needed to support each sentence.

GROUNDING:


- State facts that are explicitly present in the course evidence.
- Prefer direct statements from the evidence over inferred explanations.
- Use the evidence's terminology when possible.
- Keep the answer concise.
- DO NOT add textbook knowledge that is absent from the evidence.
- DO NOT add explanations that are only logically implied.
- DO NOT add unsupported examples, classifications, complexity values, advantages,
  disadvantages, use cases, or conclusions.
- DO NOT invent details to make the answer more complete.

OUTPUT:

Return only the final user-facing answer.
""".strip()

def _validate_answer_citations(
    answer: str,
    evidence_count: int,
) -> str:
    """
    Validate citation structure and evidence IDs.

    Python checks:
    - answer is not empty
    - at least one citation exists
    - every citation refers to an existing evidence block

    Semantic grounding is handled by the evidence-only generation prompt.
    """

    answer = (answer or "").strip()

    if not answer:
        return ""

    valid_ids = set(
        range(
            1,
            evidence_count + 1,
        )
    )

    citation_pattern = re.compile(
        r"\[(\d+)\]"
    )

    citations = citation_pattern.findall(
        answer
    )

    # ---------------------------------------------------------
    # Every answer must contain at least one citation.
    # ---------------------------------------------------------

    if not citations:
        print(
            "Citation validation failed: "
            "answer contains no evidence citations."
        )
        return ""

    # ---------------------------------------------------------
    # Every citation must reference real evidence.
    # ---------------------------------------------------------

    citation_numbers = [
        int(citation)
        for citation in citations
    ]

    invalid_citations = [
        citation
        for citation in citation_numbers
        if citation not in valid_ids
    ]

    if invalid_citations:
        print(
            "Citation validation failed: "
            f"invalid evidence citation(s): "
            f"{invalid_citations}"
        )
        return ""

    # ---------------------------------------------------------
    # Citation validation passed.
    # ---------------------------------------------------------

    print(
        "Citation validation passed:",
        sorted(set(citation_numbers)),
    )

    return answer

def _generate_grounded_answer(
    question: str,
    evidence_context: str,
    evidence_count: int,
    comparison: bool = False,
) -> str:
    """Generate one evidence-cited answer from course evidence."""

    prompt = _build_evidence_synthesis_prompt(
        question=question,
        evidence_context=evidence_context,
        comparison=comparison,
    )

    print(
        "\n========== EVIDENCE-GROUNDED ANSWER =========="
    )

    draft_answer = generate_answer(
        prompt,
        max_tokens=120 if comparison else 500,
        temperature=0.1,
    ).strip()

    print("\n========== RAW LLM ANSWER ==========")
    print(draft_answer)

    if not draft_answer:
        return NO_CONTEXT_ANSWER

    print(
        "\n========== PYTHON CITATION VALIDATION =========="
    )

    validated_answer = _validate_answer_citations(
        answer=draft_answer,
        evidence_count=evidence_count,
    )

    if not validated_answer:
        print(
            "Answer rejected because its evidence citations "
            "were invalid or missing."
        )

        return (
            "I couldn't produce a reliably "
            "evidence-cited answer from the selected "
            "course content."
        )

    return validated_answer

def _limit_comparison_evidence(
    evidence: list[dict],
    max_per_topic: int = 2,
) -> list[dict]:
    """
    Keep comparison evidence balanced across the requested topics.

    For a two-topic comparison:
    - up to 2 evidence blocks from topic 1
    - up to 2 evidence blocks from topic 2
    """

    selected = []
    counts = {}

    for item in evidence:
        topic_key = (
            str(item.get("video_id", "")).strip()
            or str(item.get("source", "")).strip()
        )

        if not topic_key:
            continue

        current_count = counts.get(topic_key, 0)

        if current_count >= max_per_topic:
            continue

        selected.append(item)
        counts[topic_key] = current_count + 1

    return selected

def handle_course_question(
    playlist_id: str,
    question: str,
    history: list | None = None,
    top_k: int = 5,
) -> dict[str, Any]:

    try:

        playlist_id = (
            playlist_id or ""
        ).strip()

        question = (
            question or ""
        ).strip()

        if (
            not playlist_id
            or "/" in playlist_id
            or "\\" in playlist_id
        ):
            return {
                "message":
                "invalid playlist ID"
            }

        if not question:

            return {
                "message":
                "Please enter a question.",
                "answer":
                NO_CONTEXT_ANSWER,
                "sources": [],
            }

        manifest_file = os.path.join(
            COURSE_MANIFEST_DIR,
            f"{playlist_id}.json",
        )

        if not os.path.isfile(
            manifest_file
        ):

            return {
                "message":
                "Course manifest not found. "
                "Please index this course first.",
                "playlist_id":
                playlist_id,
            }

        with open(
            manifest_file,
            "r",
            encoding="utf-8",
        ) as file:

            manifest = json.load(file)

        videos = manifest.get(
            "videos",
            [],
        )

        if not videos:

            return {
                "message":
                "No videos found in this course manifest.",
                "answer":
                "This course does not contain any indexed lectures.",
                "sources": [],
            }

        video_ids = [
            video["video_id"]
            for video in videos
            if video.get("video_id")
        ]

        video_titles = {
            video["video_id"]:
            video.get(
                "title",
                video["video_id"],
            )
            for video in videos
            if video.get("video_id")
        }

        retrieval_question = (
            resolve_course_retrieval_query(
                question,
                history or [],
            )
        )

        print(
            "\n========== COURSE RETRIEVAL QUERY =========="
        )

        print(
            "Original question:",
            question,
        )

        print(
            "Resolved retrieval query:",
            retrieval_question,
        )

        requested_top_k = max(
            1,
            min(
                int(top_k),
                20,
            ),
        )

        results = _retrieve_topic_aware(
            query=retrieval_question,
            video_ids=video_ids,
            video_titles=video_titles,
            top_k=requested_top_k,
        )

        if not results:

            return {
                "playlist_id":
                playlist_id,
                "answer":
                NO_CONTEXT_ANSWER,
                "sources": [],
            }
        
        is_comparison = (
            _is_comparison_question(retrieval_question)
            and len(_find_named_topics(retrieval_question)) >= 2
        )

        if is_comparison:
            results = _limit_comparison_evidence(
                results,
                max_per_topic=2,
            )

            print(
                "\nComparison evidence limited to:",
                len(results),
                "blocks",
            )

# ---------------------------------------------------------
# PYTHON EVIDENCE SELECTION
# ---------------------------------------------------------

        # ---------------------------------------------------------
        # PYTHON EVIDENCE SELECTION
        # ---------------------------------------------------------
        # Retrieval has already ranked the transcript chunks.
        # Use those exact chunks as evidence.
        # No LLM evidence-selection call is needed.
        # ---------------------------------------------------------

        evidence_context = _format_retrieved_evidence(
            results
        )

        if not evidence_context:
            return {
                "playlist_id": playlist_id,
                "answer": (
                    "I couldn't find sufficiently relevant "
                    "evidence in the selected course content "
                    "to answer this question."
                ),
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

        print(
            "\n========== PYTHON-SELECTED EVIDENCE =========="
        )

        print(evidence_context)

        print(
            "\nRetrieved context sources:"
        )

        for result in results:
            print(
                f"  - "
                f"{result.get('video_title', 'Unknown lecture')} "
                f"(video_id="
                f"{result.get('video_id', 'unknown')}, "
                f"chunk_id="
                f"{result.get('chunk_id', 'unknown')}, "
                f"similarity="
                f"{result.get('similarity', 0.0):.4f})"
            )

        

    
        # ---------------------------------------------------------
        # FINAL ANSWER GENERATION
        # ---------------------------------------------------------
        # First pass receives ONLY validated evidence.
        # Second pass verifies the generated answer against
        # the exact same evidence.
        # Raw retrieval context never reaches answer synthesis.
        # ---------------------------------------------------------

        

        answer = _generate_grounded_answer(
            question=retrieval_question,
            evidence_context=evidence_context,
            evidence_count=len(results),
            comparison=is_comparison,
        )

        

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

        print(
            "Course question error:",
            str(error),
        )

        traceback.print_exc()

        return {
            "message":
            "Failed to generate course answer.",
            "error":
            str(error),
        }