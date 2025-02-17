import sqlite3

DB_FILE = "shamzam.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Create table for all tracks (both manually added and matched from recognition)
cursor.execute("""
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    file_path TEXT NOT NULL
);
""")

conn.commit()
conn.close()

print("✅ Database setup complete!")
