import sqlite3

class TrackRepository:
    def __init__(self, db_file="shamzam.db"):
        self.db_file = db_file
        self.create_table()

    def create_table(self):
        """Create the tracks table if it doesn't exist."""
        with sqlite3.connect(self.db_file) as connection:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    encoded_file TEXT NOT NULL
                )
            """)
            connection.commit()

    def db_teardown(self):
        """
        Drop the tracks table and re-create it.
        Useful for testing to ensure a clean slate.
        """
        with sqlite3.connect(self.db_file) as connection:
            cursor = connection.cursor()
            cursor.execute("DROP TABLE IF EXISTS tracks")
            connection.commit()
        # Re-create the table after dropping it.
        self.create_table()

    def clear(self):
        """Delete all records from the tracks table (useful for testing)."""
        with sqlite3.connect(self.db_file) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM tracks")
            connection.commit()

    def insert(self, track):
        """
        Insert a track into the catalogue.
        :param track: A dict with keys 'title', 'artist', 'encoded_file'
        :return: The id of the inserted track.
        """
        with sqlite3.connect(self.db_file) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO tracks (title, artist, encoded_file) VALUES (?, ?, ?)",
                (track["title"], track["artist"], track["encoded_file"])
            )
            connection.commit()
            return cursor.lastrowid

    def update(self, track):
        """
        Update a track in the catalogue.
        :param track: A dict with keys 'id', 'title', 'artist', 'encoded_file'
        :return: Number of rows affected.
        """
        with sqlite3.connect(self.db_file) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE tracks SET title = ?, artist = ?, encoded_file = ? WHERE id = ?",
                (track["title"], track["artist"], track["encoded_file"], track["id"])
            )
            connection.commit()
            return cursor.rowcount

    def lookup_by_title_artist(self, title, artist):
        """
        Retrieve a track from the catalogue by title and artist.
        :return: A dict with track details or None if not found.
        """
        with sqlite3.connect(self.db_file) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id, title, artist, encoded_file FROM tracks WHERE title = ? AND artist = ?",
                (title, artist)
            )
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "title": row[1], "artist": row[2], "encoded_file": row[3]}
            return None

    def list_all(self):
        """
        List all tracks in the catalogue.
        :return: A list of dictionaries representing tracks.
        """
        with sqlite3.connect(self.db_file) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id, title, artist, encoded_file FROM tracks")
            rows = cursor.fetchall()
            return [{"id": row[0], "title": row[1], "artist": row[2], "encoded_file": row[3]} for row in rows]

    def delete(self, track_id):
        """
        Remove a track from the catalogue by id.
        :return: Number of rows affected.
        """
        with sqlite3.connect(self.db_file) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
            connection.commit()
            return cursor.rowcount
    def delete_by_title_artist(self, title, artist):
        """
        Remove a track from the catalogue by matching title and artist.
        :return: Number of rows affected.
        """
        with sqlite3.connect(self.db_file) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM tracks WHERE title = ? AND artist = ?",
                (title, artist)
            )
            connection.commit()
            return cursor.rowcount

