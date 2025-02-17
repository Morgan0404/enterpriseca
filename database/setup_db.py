import sqlite3

DB_FILE = "shamzam.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Drop table if it exists (optional)
cursor.execute("DROP TABLE IF EXISTS tracks;")

# Create table for tracks with a column for the Base85 encoded full track file
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
