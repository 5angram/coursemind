from backend.app import log_learning_event
from backend.database import get_db_connection

# Test the learning event logger
event_id = log_learning_event(
    playlist_id="PLfqMhTWNBTe137I_EPQd34TsgV6IO55pt",
    event_type="video_opened",
    youtube_video_id="P08Z_NC8GuY",
)

print("Test successful. Event ID:", event_id)

# Verify that the event was saved
connection = get_db_connection()

try:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM public.learning_events
            ORDER BY event_id DESC;
        """)

        rows = cursor.fetchall()

        print("\nLEARNING EVENTS:")
        for row in rows:
            print(row)

finally:
    connection.close()