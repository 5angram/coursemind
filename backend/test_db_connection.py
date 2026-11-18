from  backend.database import get_db_connection

def main():
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT current_database(), current_user;"
            )
            database_name , username = cursor.fetchone()

            print("PostgreSQL connection successful!")
            print(f"Database: {database_name}")
            print(f"User: {username}")
    finally:
        connection.close()

if __name__ == "__main__":
    main()