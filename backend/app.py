from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse, parse_qs
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from backend.chunker import chunk_test
from backend.retriever import retrieve , retrieve_course
from backend.context_builder import build_context
from backend.prompt_builder import build_prompt
from backend.llm import generate_answer
from backend.vector_store import load_vector
import traceback
import json
import os
import threading
import sys
import subprocess

app = FastAPI()


# -----------------------------------------
# SUMMARY GENERATION LOCKS
# -----------------------------------------

summary_locks = {}
summary_locks_guard = threading.Lock()

#course indexing jobs
index_jobs_running = set()
index_jobs_guard = threading.Lock()


# -----------------------------------------
# CORS
# -----------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------
# REQUEST MODELS
# -----------------------------------------

class CourseRequest(BaseModel):
    url: HttpUrl


class AskRequest(BaseModel):
    video_id: str
    question: str
    top_k: int = 5
    history: list = []

class CourseAskRequest(BaseModel):
    playlist_id: str
    question : str
    top_k : int = 5
    history: list = []


# -----------------------------------------
# CLEAN TRANSCRIPT
# -----------------------------------------

def clean_transcript(text):
    text = text.replace("♪", "")
    text = " ".join(text.split())
    return text


# -----------------------------------------
# HOME
# -----------------------------------------

@app.get("/")
def home():
    return {
        "message": "Coursemind backend is running!"
    }


# -----------------------------------------
# COURSE INFO
# -----------------------------------------


@app.post("/course/info")
def course_info(course: CourseRequest):
    url = str(course.url)
    parsed_url = urlparse(url)

    if (
        parsed_url.hostname not in {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
            "www.youtu.be"
        }
    ):
        return {"message": "Please enter a valid YouTube URL."}

    playlist_id = parse_qs(parsed_url.query).get("list", [None])[0]

    if not playlist_id:
        return {
            "message": "Please provide a YouTube playlist URL containing a list parameter."
        }

    # Force yt-dlp to fetch the playlist, not just its first video.
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"

    ydl_opts = {
        "quiet": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "ignoreerrors": True,
        "noplaylist": False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

            if not info:
                return {
                    "message": "Could not retrieve playlist information.",
                    "playlist_id": playlist_id,
                    "total_videos": 0,
                    "videos": []
                }

            videos = []

            for entry in info.get("entries") or []:
                if not entry:
                    continue

                video_id = entry.get("id")
                if not video_id:
                    continue

                videos.append({
                    "video_id": video_id,
                    "title": entry.get("title") or "Untitled video"
                })

            if not videos:
                return {
                    "message": "Playlist was retrieved, but no videos could be extracted.",
                    "playlist_id": playlist_id,
                    "title": info.get("title"),
                    "total_videos": 0,
                    "videos": []
                }

            return {
                "message": "Course information fetched successfully",
                "playlist_id": playlist_id,
                "title": info.get("title"),
                "total_videos": len(videos),
                "videos": videos
            }

    except Exception as e:
        return {
            "message": "Failed to fetch playlist information",
            "playlist_id": playlist_id,
            "error": str(e),
            "total_videos": 0,
            "videos": []
        }




#course indexing

INDEX_JOB_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "index_jobs"
)

def read_index_status(playlist_id):
    status_file = os.path.join(
        INDEX_JOB_DIR ,
        f"{playlist_id}.json"
    )
    if not os.path.exists(status_file):
        return None

    with open(status_file , "r" , encoding="utf-8") as file:
        return json.load(file)

def wait_for_index_process(process,playlist_id):
    return_code = process.wait()

    with index_jobs_guard:
        index_jobs_running.discard(playlist_id)

    if return_code != 0:
        try:
            status = read_index_status(playlist_id) or {}
            status["status"] = "failed"
            status["error"] = (
                status.get("error")
                or f"index process exisited with code{return_code   }"
            )

            os.makedirs(INDEX_JOB_DIR , exist_ok=True)

            status_file = os.path.join(
                INDEX_JOB_DIR,
                f"{playlist_id}.json"
            )

            with open(status_file , "w" , encoding="utf-8") as file:
                json.dump(status , file , indent=2 , ensure_ascii=False)

        except Exception as error:
            print("could not update indexing status:",error)

@app.post("/course/index")
def start_course_indexing(course: CourseRequest):
    url = str(course.url)
    parsed_url = urlparse(url)

    playlist_id = parse_qs(
        parsed_url.query
    ).get("list",[None])[0]

    if not playlist_id:
        return{
            "message":"A youtube playlist url is required"
        }

    playlist_url = (
        f"http://www.youtube.com/playlist?list={playlist_id}"
    )

    with index_jobs_guard:
        if playlist_id in index_jobs_running:
            return {
                "message":"indexing is already running",
                "playlist_id":playlist_id,
                "status":"running"
            }


        existing_status = read_index_status(playlist_id)

        if (
            existing_status
            and existing_status.get("status") == "running"
            and playlist_id in index_jobs_running
        ):
            return {
                "message": "Indexing is already running.",
                "playlist_id": playlist_id,
                "status": "running"
            }

        os.makedirs(INDEX_JOB_DIR , exist_ok=True)

        initial_status = {
            "playlist_id":playlist_id,
            "status":"queued",
            "total":0,
            "processed":0,
            "successful":0,
            "skipped":0,
            "failed":0,
            "current_video":"",
            "failed_video":[],
            "error":None
        }

        status_file = os.path.join(
            INDEX_JOB_DIR,
            f"{playlist_id}.json"
        )

        with open(status_file , "w" , encoding="utf-8") as file:
            json.dump(initial_status , file , indent=2)

        script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "index_course_job.py"
        )
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        process = subprocess.Popen(
            [
                sys.executable,
                "-X", "utf8",
                script_path,
                playlist_url,
                playlist_id
            ],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env
        )

        index_jobs_running.add(playlist_id)

    monitor = threading.Thread(
        target = wait_for_index_process,
        args=(process,playlist_id),
        daemon=True
    )

    monitor.start()

    return {
        "message": "Course indexing started.",
        "playlist_id": playlist_id,
        "status": "running"
    }


@app.get("/course/index/{playlist_id}")
def get_course_index_status(playlist_id:str):
    if not playlist_id or "/" in playlist_id or "\\" in playlist_id:
        return {"message":"invalid Playlist id."}
    status = read_index_status(playlist_id)

    if status is None:
        return {
            "message": "No indexing job found for this playlist.",
            "playlist_id": playlist_id,
            "status": "not_started"
        }

    return status

# -----------------------------------------
# ADD COURSE
# -----------------------------------------

@app.post("/course")
def add_course(course: CourseRequest):

    url = str(course.url)
    parsed_url = urlparse(url)

    if (
        "youtube.com" not in parsed_url.netloc
        and "youtu.be" not in parsed_url.netloc
    ):
        return {
            "massage": "please enter valid youtube url..."
        }

    video_id = None

    if "youtube.com" in parsed_url.netloc:

        video_id = parse_qs(
            parsed_url.query
        ).get("v", [None])[0]

    elif "youtu.be" in parsed_url.netloc:

        video_id = parsed_url.path.strip("/")

    if not video_id:

        return {
            "message": "Could not find YouTube video ID"
        }

    api = YouTubeTranscriptApi()

    transcript = api.fetch(video_id)

    text = " ".join(
        [item.text for item in transcript]
    )

    clean_text = clean_transcript(text)

    chunks = chunk_test(
        clean_text,
        chunk_size=500,
        overlap=100
    )

    return {
        "message": "transcript fetched successfully",
        "video_id": video_id,
        "transcript": clean_text,
        "chunks": chunks
    }


# -----------------------------------------
# ASK QUESTION
# -----------------------------------------

@app.post("/ask")
def ask_question(request: AskRequest):

    try:

        print(
            "\n=========== COURSE QUESTION ==========="
        )

        print(
            "Video ID:",
            request.video_id
        )

        print(
            "Question:",
            request.question
        )

        retrieval_question = request.question

        if request.history:

            last_question = (
                request.history[-1]["question"]
            )

            retrieval_question = (
                last_question
                + " "
                + request.question
            )

            print(
                "\n========== RETRIEVAL QUERY =========="
            )

            print(
                retrieval_question
            )

        results = retrieve(
            video_id=request.video_id,
            question=retrieval_question,
            top_k=3
        )

        if not results:

            return {
                "answer":
                    "I couldn't find this information in the provided course content.",
                "sources": []
            }

        context = build_context(results)

        print(
            "\n========== RETRIEVED CONTEXT =========="
        )

        print(context)

        print(
            "========================================"
        )

        prompt = build_prompt(
            request.question,
            context,
            request.history
        )

        answer = generate_answer(prompt)

        print(
            "\n=========== GENERATED ANSWER ==========="
        )

        print(answer)

        return {
            "answer": answer,
            "sources": [
                {
                    "chunk_id": result["chunk_id"],
                    "similarity": result["similarity"]
                }
                for result in results
            ]
        }

    except Exception as e:

        print(
            "\n========== QUESTION ERROR =========="
        )

        print(str(e))

        return {
            "message": "Failed to generate answer",
            "error": str(e)
        }



# -----------------------------------------
# COURSE-LEVEL AI TUTOR
# -----------------------------------------
from backend.question_handler import handle_course_question


@app.post("/ask/course")
def ask_course_question(request: CourseAskRequest):
    return handle_course_question(
        playlist_id=request.playlist_id,
        question=request.question,
        history=request.history,
        top_k=request.top_k,
    )


# -----------------------------------------
# LECTURE SUMMARY
# -----------------------------------------

@app.get("/summary/{video_id}")
def lecture_summary(video_id: str):

    # -----------------------------------------
    # GET PER-VIDEO LOCK
    # -----------------------------------------

    with summary_locks_guard:

        if video_id not in summary_locks:

            summary_locks[video_id] = (
                threading.Lock()
            )

        video_lock = summary_locks[video_id]

    print(
        f"\nWaiting for summary lock: {video_id}"
    )

    # -----------------------------------------
    # LOCK THIS LECTURE
    # -----------------------------------------

    with video_lock:

        print(
            f"Summary lock acquired: {video_id}"
        )

        try:

            print(
                "\n====lecture summary===="
            )

            print(
                "video_id",
                video_id
            )

            # -----------------------------------------
            # SUMMARY CACHE
            # -----------------------------------------

            summary_dir = os.path.join(
                os.path.dirname(__file__),
                "data",
                "summary"
            )

            os.makedirs(
                summary_dir,
                exist_ok=True
            )

            summary_file = os.path.join(
                summary_dir,
                f"{video_id}.json"
            )

            # -----------------------------------------
            # CHECK FINAL SUMMARY CACHE
            # -----------------------------------------

            if os.path.exists(summary_file):

                print(
                    "Loading cached lecture summary..."
                )

                with open(
                    summary_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    cached_data = json.load(file)

                if cached_data.get("summary"):

                    print(
                        "Cached summary found."
                    )

                    return {
                        "summary":
                            cached_data["summary"]
                    }

            # -----------------------------------------
            # LOAD VECTOR DATA
            # -----------------------------------------

            vectors = load_vector(video_id)

            if not vectors:

                return {
                    "summary":
                        "no processed content found"
                }

            print(
                "total chunks",
                len(vectors)
            )

            # -----------------------------------------
            # GET CHUNK TEXT
            # -----------------------------------------

            texts = []

            for item in vectors:

                chunk_text = item.get(
                    "text",
                    ""
                )

                if not isinstance(
                    chunk_text,
                    str
                ):

                    print(
                        "WARNING: chunk text is not a string:",
                        type(chunk_text)
                    )

                    continue

                chunk_text = (
                    chunk_text.strip()
                )

                if chunk_text:

                    texts.append(
                        chunk_text
                    )

            print(
                "Total text chunks:",
                len(texts)
            )

            # -----------------------------------------
            # CREATE BATCHES
            # -----------------------------------------

            batch_size = 8

            batches = []

            for i in range(
                0,
                len(texts),
                batch_size
            ):

                batch = texts[
                    i:i + batch_size
                ]

                batches.append(
                    "\n".join(batch)
                )

            print(
                "Total summary batches:",
                len(batches)
            )

            # -----------------------------------------
            # LOAD EXISTING CACHE DATA
            # -----------------------------------------

            cached_data = {}

            if os.path.exists(summary_file):

                try:

                    with open(
                        summary_file,
                        "r",
                        encoding="utf-8"
                    ) as file:

                        cached_data = json.load(
                            file
                        )

                except Exception:

                    cached_data = {}

            batches_summaries = (
                cached_data.get(
                    "batch_summaries",
                    []
                )
            )

            # -----------------------------------------
            # GENERATE BATCH SUMMARIES
            # -----------------------------------------

            for index, batch in enumerate(
                batches,
                start=1
            ):

                # Reuse cached batch
                if (
                    index
                    <= len(batches_summaries)
                ):

                    print(
                        f"Using cached batch {index}"
                    )

                    continue

                print(
                    "\ngenerating batch summary."
                )

                print(
                    f"{index}/{len(batches)}"
                )

                prompt = f"""
You are CourseMind AI.

Summarize ONLY the lecture content below.

Do NOT use general knowledge.

Do NOT add outside information.

Do NOT invent examples.

Extract only the important concepts
explained in this section.

Keep the summary SHORT.

Use simple language.

LECTURE CONTENT:

{batch}

BATCH SUMMARY:
"""

                summary = generate_answer(
                    prompt,
                    max_tokens=300,
                    temperature=0.2
                )

                batches_summaries.append(
                    summary
                )

                # -----------------------------------------
                # SAVE AFTER EVERY BATCH
                # -----------------------------------------

                cached_data[
                    "batch_summaries"
                ] = batches_summaries

                with open(
                    summary_file,
                    "w",
                    encoding="utf-8"
                ) as file:

                    json.dump(
                        cached_data,
                        file,
                        indent=2,
                        ensure_ascii=False
                    )

                print(
                    f"batch {index} completed"
                )

            print(
                "all batches are completed"
            )

            # -----------------------------------------
            # GROUP BATCH SUMMARIES
            # -----------------------------------------

            group_size = 5

            summary_groups = []

            for i in range(
                0,
                len(batches_summaries),
                group_size
            ):

                group = batches_summaries[
                    i:i + group_size
                ]

                summary_groups.append(
                    group
                )

            print(
                "Total summary groups:",
                len(summary_groups)
            )

            # -----------------------------------------
            # LOAD GROUP CACHE
            # -----------------------------------------

            group_summaries = (
                cached_data.get(
                    "group_summaries",
                    []
                )
            )

            # -----------------------------------------
            # GENERATE GROUP SUMMARIES
            # -----------------------------------------

            for index, group in enumerate(
                summary_groups,
                start=1
            ):

                # Reuse cached group
                if (
                    index
                    <= len(group_summaries)
                ):

                    print(
                        f"Using cached group {index}"
                    )

                    continue

                print(
                    "\ngenerating group summary."
                )

                print(
                    f"{index}/{len(summary_groups)}"
                )

                group_text = (
                    "\n\n".join(group)
                )

                group_prompt = f"""
You are CourseMind AI.

Combine the lecture section summaries below.

Use ONLY the information provided.

Do NOT use general knowledge.

Do NOT add outside information.

Do NOT invent examples.

Remove repeated information.

Keep the important concepts.

Use simple language.

Keep the summary concise.

LECTURE SECTION SUMMARIES:

{group_text}

GROUP SUMMARY:
"""

                group_summary = generate_answer(
                    group_prompt,
                    max_tokens=300,
                    temperature=0.2
                )

                group_summaries.append(
                    group_summary
                )

                # -----------------------------------------
                # SAVE AFTER EVERY GROUP
                # -----------------------------------------

                cached_data[
                    "group_summaries"
                ] = group_summaries

                with open(
                    summary_file,
                    "w",
                    encoding="utf-8"
                ) as file:

                    json.dump(
                        cached_data,
                        file,
                        indent=2,
                        ensure_ascii=False
                    )

                print(
                    f"group {index} completed"
                )

            print(
                "all summary groups completed"
            )

            # -----------------------------------------
            # FINAL SUMMARY
            # -----------------------------------------

            final_input = (
                "\n\n".join(
                    group_summaries
                )
            )

            final_prompt = f"""
You are CourseMind AI.

Create a concise final summary of the lecture
using ONLY the group summaries provided below.

Do NOT use general knowledge.

Do NOT add information that is not present
in the group summaries.

Combine repeated ideas.

Focus on the main concepts and important
points from the lecture.

Write:

1. A short overview paragraph.

2. Important key points using bullet points.

Keep the final answer concise.

GROUP SUMMARIES:

{final_input}

FINAL LECTURE SUMMARY:
"""

            print(
                "\nGenerating final lecture summary..."
            )

            final_summary = generate_answer(
                final_prompt,
                max_tokens=500,
                temperature=0.2
            )

            print(
                "\n============= SUMMARY GENERATED ============="
            )

            print(
                final_summary
            )

            # -----------------------------------------
            # SAVE FINAL SUMMARY
            # -----------------------------------------

            cached_data[
                "summary"
            ] = final_summary

            with open(
                summary_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    cached_data,
                    file,
                    indent=2,
                    ensure_ascii=False
                )

            print(
                "Lecture summary saved to cache."
            )

            return {
                "summary": final_summary
            }

        except Exception as e:

            print(
                "\n========== SUMMARY ERROR =========="
            )

            print(
                "ERROR TYPE:",
                type(e).__name__
            )

            print(
                "ERROR MESSAGE:",
                repr(str(e))
            )

            traceback.print_exc()

            return {
                "message":
                    "Failed to generate lecture summary",
                "error":
                    str(e)
            }
