import sqlite3

DB_FILE = "shamzam.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Drop table if it exists (optional)
cursor.execute("DROP TABLE IF EXISTS tracks;")

# Create table with an encoded_file column to store the Base85-encoded, compressed full track.
cursor.execute("""
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    encoded_file TEXT NOT NULL
);
""")
conn.commit()
conn.close()

print("✅ Database reset complete!")
