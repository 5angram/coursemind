import json
import re

from backend.llm import generate_answer


def _parse_source_blocks(context: str) -> list[dict]:
    """
    Parse retrieved context into source blocks.

    Each block keeps its original SOURCE header and transcript text.
    """

    blocks = []

    raw_blocks = re.split(
        r"\n\s*---\s*\n",
        context,
    )

    for raw_block in raw_blocks:
        raw_block = raw_block.strip()

        if not raw_block:
            continue

        lines = raw_block.splitlines()

        if len(lines) < 2:
            continue

        source = lines[0].strip()
        text = "\n".join(lines[1:]).strip()

        if not text:
            continue

        blocks.append(
            {
                "source": source,
                "text": text,
            }
        )

    return blocks


def _build_passages(
    context: str,
    window_size: int = 100,
    overlap: int = 55,
) -> list[dict]:
    """
    Create evidence units from retrieved chunks.

    Each retrieved chunk is preserved as a complete passage first.
    Smaller overlapping windows are also created for long chunks so the
    selector can focus on a specific part when necessary.

    The text of every passage comes directly from the retrieved context.
    No LLM-generated text is used here.
    """
    passages = []

    if overlap >= window_size:
        overlap = window_size // 2

    step = window_size - overlap

    for block in _parse_source_blocks(context):
        words = block["text"].split()

        if not words:
            continue

        # Keep the complete retrieved chunk as the primary evidence unit.
        full_text = " ".join(words).strip()

        passages.append(
            {
                "passage_id": len(passages),
                "source": block["source"],
                "text": full_text,
                "passage_type": "complete_chunk",
            }
        )

        # For long chunks, also provide focused overlapping windows.
        if len(words) <= window_size:
            continue

        start = 0

        while start < len(words):
            end = min(start + window_size, len(words))
            window_text = " ".join(words[start:end]).strip()

            if window_text:
                passages.append(
                    {
                        "passage_id": len(passages),
                        "source": block["source"],
                        "text": window_text,
                        "passage_type": "window",
                    }
                )

            if end >= len(words):
                break

            start += step

    return passages


def _extract_json_array(raw: str) -> list:
    """
    Safely extract a JSON array from the model response.
    """

    raw = (raw or "").strip()

    raw = re.sub(
        r"^```(?:json)?\s*",
        "",
        raw,
        flags=re.IGNORECASE,
    )

    raw = re.sub(
        r"\s*```$",
        "",
        raw,
    ).strip()

    try:
        data = json.loads(raw)

        if isinstance(data, list):
            return data

    except json.JSONDecodeError:
        pass

    match = re.search(
        r"\[[\s\S]*\]",
        raw,
    )

    if not match:
        return []

    try:
        data = json.loads(
            match.group(0)
        )

        return data if isinstance(data, list) else []

    except json.JSONDecodeError:
        return []


def extract_evidence(
    question: str,
    context: str,
) -> list[dict]:
    """
    Select exact passages that support the question.

    IMPORTANT:
    The LLM is allowed to select passage IDs only.
    It is NOT allowed to generate evidence text.

    Python retrieves the actual passage text afterward.
    """

    passages = _build_passages(
        context
    )

    if not passages:
        return []

    formatted_passages = "\n\n".join(
        (
            f"[PASSAGE_ID={item['passage_id']}]\n"
            f"[SOURCE={item['source']}]\n"
            f"{item['text']}"
        )
        for item in passages
    )

    prompt = f"""
You are the evidence-selection component of CourseMind.

You are NOT answering the user.

Your ONLY job is to select PASSAGE_ID values that contain information
directly useful for answering the question.

STRICT RULES:

1. Return ONLY JSON.
2. Select existing PASSAGE_ID values only.
3. Never write a quote.
4. Never paraphrase a passage.
5. Never generate evidence text.
6. Never use general knowledge.
7. Never infer information.
8. Never calculate anything.
9. Never combine two passages into a new fact.
10. Select evidence separately for every named concept.
11. For a comparison, select evidence for both sides.
12. Prefer passages that directly address the requested property.
13. Do not select a passage simply because it mentions the topic.
14. If the course does not establish something, do not invent evidence.
15. Select at most 3 passages per concept.
16.Prefer COMPLETE_CHUNK passages when they directly contain the requested information.
17.Use WINDOW passages when they provide a more focused and directly relevant section.

Return exactly this structure:

[
  {{
    "concept": "merge sort",
    "passage_id": 12
  }},
  {{
    "concept": "binary search",
    "passage_id": 18
  }}
]

USER QUESTION:
{question}

COURSE PASSAGES:
{formatted_passages}

JSON:
""".strip()

    try:

        raw = generate_answer(
            prompt,
            max_tokens=500,
            temperature=0.0,
        )

        data = _extract_json_array(
            raw
        )

        passage_map = {
            item["passage_id"]: item
            for item in passages
        }

        validated = []

        seen = set()
        concept_counts = {}

        for item in data:

            if not isinstance(
                item,
                dict,
            ):
                continue

            concept = str(
                item.get(
                    "concept",
                    "",
                )
            ).strip()

            try:
                passage_id = int(
                    item.get(
                        "passage_id"
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if not concept:
                continue

            if passage_id not in passage_map:
                continue

            concept_key = concept.lower()

            if concept_counts.get(
                concept_key,
                0,
            ) >= 3:
                continue

            key = (
                concept_key,
                passage_id,
            )

            if key in seen:
                continue

            seen.add(key)

            selected = passage_map[
                passage_id
            ]

            validated.append(
                {
                    "concept": concept,
                    "passage_id": passage_id,
                    "source": selected[
                        "source"
                    ],
                    "quote": selected[
                        "text"
                    ],
                }
            )

            concept_counts[
                concept_key
            ] = (
                concept_counts.get(
                    concept_key,
                    0,
                )
                + 1
            )

        return validated

    except Exception as error:

        print(
            "Evidence extraction failed:",
            str(error),
        )

        return []