import json
from pathlib import Path
from getpass import getpass

import psycopg2

backend_dir = Path(__file__).resolve().parent

manifest_path = (
    backend_dir
    /"data"
    /"course_manifests"
    /"PLfqMhTWNBTe137I_EPQd34TsgV6IO55pt.json"
)

with manifest_path.open("r" , encoding="utf-8") as file:
    manifest = json.load(file)

videos = manifest["videos"]
expected_total = manifest["total_videos"]

if len(videos) != expected_total:
    raise ValueError("Manifest video count does not match total_videos.")

video_ids = [video["video_id"] for video in videos]
video_numbers = [video["video_number"] for video in videos]

if len(set(video_ids)) != len(video_ids):
    raise ValueError("Duplicate YouTube video IDs found.")

if len(set(video_numbers)) != len(video_numbers):
    raise ValueError("Duplicate video numbers found.")

if sorted(video_numbers) != list(range(1, expected_total + 1)):
    raise ValueError("Video numbers are missing or out of sequence.")


password = getpass("PostgreSQL password for user postgres:")

connection = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="coursemind",
    user="postgres",
    password=password, 
)

try:
    with connection.cursor() as cursor:

        playlist_id = manifest["playlist_id"]

        youtube_url = (
            "https://www.youtube.com/playlist?list="
            + playlist_id
        )

        cursor.execute(
            """
            INSERT INTO courses (
                playlist_id,
                course_name,
                youtube_url,
                total_videos
            )
            VALUES (%s , %s, %s, %s)
            ON CONFLICT (playlist_id)
            DO UPDATE SET
                course_name = EXCLUDED.course_name,
                youtube_url = EXCLUDED.youtube_url,
                total_videos = EXCLUDED.total_videos
            RETURNING course_id;
            """,
            (
                playlist_id,
                manifest["course_name"],
                youtube_url,
                expected_total,
            ),
        )

        course_id = cursor.fetchone()[0]

        video_rows = [
            (
                course_id,
                video["video_number"],
                video["video_id"],
                video["title"],
            )
            for video in videos
        ]

        cursor.executemany(
            """
            INSERT INTO videos (
                course_id,
                video_number,
                youtube_video_id,
                title
            )
            VALUES (%s , %s , %s , %s)
            ON CONFLICT (youtube_video_id)
            DO UPDATE SET
                course_id = EXCLUDED.course_id,
                video_number = EXCLUDED.video_number,
                title = EXCLUDED.title;
            """,
            video_rows,
        )


        cursor.execute(
            """
            SELECT COUNT(*)
            FROM videos
            WHERE course_id = %s;
            """,
            (course_id,),
        )

        stored_count = cursor.fetchone()[0]

        if stored_count != expected_total:
            raise ValueError(
                f"Expecter {expected_total} videos, "
                f"but found {stored_count}."
            )

    connection.commit()

    print("Course import successful!")
    print(f"Course: {manifest['course_name']}")
    print(f"Course ID: {course_id}")
    print(f"Videos stored: {stored_count}")

except Exception:
    connection.rollback()

finally:
    connection.close()
    