import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reviews.db')
print(f"Database path: {db_path}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if user_id column exists in products table
cursor.execute("PRAGMA table_info(products)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
print(f"Current columns in products table: {column_names}")

# Add user_id column if it doesn't exist
if 'user_id' not in column_names:
    print("Adding user_id column to products table...")
    cursor.execute("ALTER TABLE products ADD COLUMN user_id TEXT")
    conn.commit()
    print("Column added successfully.")
else:
    print("user_id column already exists.")

# Verify the change
cursor.execute("PRAGMA table_info(products)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
print(f"Updated columns in products table: {column_names}")

# Close the connection
conn.close()
print("Database schema update completed.") 