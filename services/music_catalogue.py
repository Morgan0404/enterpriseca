from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_FILE = "shamzam.db"

@app.route('/tracks', methods=['GET'])
def list_tracks():
    """
    Retrieve all tracks from the catalogue.
    Returns a 404 error with JSON if no tracks exist.
    For display purposes, the 'file_path' is truncated.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, artist, file_path FROM tracks")
    tracks = cursor.fetchall()
    conn.close()

    if not tracks:
        return jsonify({"error": "No tracks found"}), 404

    # Truncate the file_path for display (e.g., first 100 characters)
    track_list = []
    for t in tracks:
        fp = t[3]
        truncated_fp = fp if len(fp) <= 100 else fp[:100] + "..."
        track_list.append({
            "id": t[0],
            "title": t[1],
            "artist": t[2],
            "file_path": truncated_fp  # Display only a truncated version
        })

    return jsonify({"tracks": track_list}), 200

@app.route('/tracks', methods=['POST'])
def add_track():
    """
    Add a full track to the catalogue.
    The admin provides the track's title, artist, and full track file path 
    (e.g., from the "full" folder). This endpoint stores the provided file path in the database.
    """
    data = request.get_json()
    title = data.get('title')
    artist = data.get('artist')
    file_path = data.get('file_path')  # e.g., "/Users/morgan/Desktop/EnterprsieCA/full/Blinding Lights.wav"

    if not title or not artist or not file_path:
        return jsonify({"error": "Missing required fields"}), 400

    if not os.path.exists(file_path):
        return jsonify({"error": "Full track file does not exist at provided path"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tracks (title, artist, file_path) VALUES (?, ?, ?)", 
                   (title, artist, file_path))
    conn.commit()
    conn.close()

    return jsonify({"message": "Track added successfully"}), 201

@app.route('/tracks/<int:track_id>', methods=['DELETE'])
def remove_track(track_id):
    """
    Remove a track from the catalogue using its ID.
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
