import sqlite3

# Connect to SQLite database
conn = sqlite3.connect("user_data.db")
cursor = conn.cursor()

# Query all data from the users table
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

# Print the data
for row in rows:
    print(row)

# Close the connection
conn.close()
