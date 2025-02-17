from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DB_FILE = "shamzam.db"

# ✅ Get all tracks (returns 404 if empty)
@app.route('/tracks', methods=['GET'])
def list_tracks():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, artist FROM tracks")
    tracks = cursor.fetchall()
    conn.close()

    if not tracks:
        return jsonify({"error": "No tracks found"}), 404  # ✅ Now returns 404 when empty

    return jsonify({"tracks": [{"id": t[0], "title": t[1], "artist": t[2]} for t in tracks]}), 200


# ✅ Add a track to the catalogue
@app.route('/tracks', methods=['POST'])
def add_track():
    data = request.get_json()
    title = data.get('title')
    artist = data.get('artist')
    file_path = data.get('file_path')

    if not title or not artist or not file_path:
        return jsonify({"error": "Missing required fields"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tracks (title, artist, file_path) VALUES (?, ?, ?)", 
                   (title, artist, file_path))
    conn.commit()
    conn.close()

    return jsonify({"message": "Track added successfully"}), 201


# ✅ Remove a track by ID
@app.route('/tracks/<int:track_id>', methods=['DELETE'])
def remove_track(track_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if track exists before deletion
    cursor.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
    track = cursor.fetchone()

    if not track:
        conn.close()
        return jsonify({"error": "Track not found"}), 404  # ✅ Now returns 404 if track doesn't exist

    cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Track removed"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5001)
