import sqlite3
def setup_database():
    # Connect to SQLite database
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()


    # Create users1 table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            published TEXT,
            title TEXT,
            summary TEXT,
            sentiment_title REAL,
            sentiment_summary REAL
        )
    ''')
    # Commit changes and close the connection
    conn.commit()
    conn.close()
# Call the setup function
setup_database()
