import sqlite3

# Connect to SQLite database
conn = sqlite3.connect("user_data.db")
cursor = conn.cursor()

# Query all data from the users table before deletion
cursor.execute("SELECT * FROM users")
print("Data before deletion:")
rows_before_deletion = cursor.fetchall()
for row in rows_before_deletion:
    print(row)

# Specify the condition for deletion (for example, delete users with a certain condition)
condition = "user_id = 'abhi04'"  # Corrected the condition with single quotes

# Delete rows based on the specified condition
cursor.execute("DELETE FROM users WHERE {}".format(condition))

# Commit the changes
conn.commit()

# Query all data from the users table after deletion
cursor.execute("SELECT * FROM users")
print("\nData after deletion:")
rows_after_deletion = cursor.fetchall()
for row in rows_after_deletion:
    print(row)

# Close the connection
conn.close()
