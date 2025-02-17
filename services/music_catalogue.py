from flask import Flask, request, jsonify
import sqlite3
import os
import base64
import zlib

app = Flask(__name__)
DB_FILE = "shamzam.db"

@app.route('/tracks', methods=['GET'])
def list_tracks():
    """
    Retrieve all tracks from the catalogue.
    Returns a 404 error with JSON if no tracks exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, artist, encoded_file FROM tracks")
    tracks = cursor.fetchall()
    conn.close()

    if not tracks:
        return jsonify({"error": "No tracks found"}), 404

    return jsonify({
        "tracks": [
            {"id": t[0], "title": t[1], "artist": t[2], "encoded_file": t[3]}
            for t in tracks
        ]
    }), 200

@app.route('/tracks', methods=['POST'])
def add_track():
    """
    Add a full track to the catalogue.
    The admin sends a JSON payload with title, artist, and the full track file path
    (e.g., from the "full" folder).
    The service reads the file, compresses it with zlib, then encodes it in Base85,
    and stores the encoded string in the database.
    """
    data = request.get_json()
    title = data.get('title')
    artist = data.get('artist')
    file_path = data.get('file_path')  # e.g., "/Users/morgan/Desktop/EnterprsieCA/full/Blinding Lights.wav"

    if not title or not artist or not file_path:
        return jsonify({"error": "Missing required fields"}), 400

    if not os.path.exists(file_path):
        return jsonify({"error": "Full track file does not exist at provided path"}), 400

    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()
            compressed_data = zlib.compress(raw_data)
            # Encode using Base85 for a shorter ASCII representation compared to Base64.
            encoded_file = base64.b85encode(compressed_data).decode('ascii')
    except Exception as e:
        return jsonify({"error": "Failed to encode file", "details": str(e)}), 500

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tracks (title, artist, encoded_file) VALUES (?, ?, ?)",
        (title, artist, encoded_file)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Track added successfully"}), 201

@app.route('/tracks/<int:track_id>', methods=['DELETE'])
def remove_track(track_id):
    """
    Remove a track from the catalogue by its ID.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
    track = cursor.fetchone()

    if not track:
        conn.close()
        return jsonify({"error": "Track not found"}), 404

    cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Track removed"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)
