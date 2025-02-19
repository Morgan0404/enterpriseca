from flask import Flask, request, jsonify
import sqlite3
import base64

app = Flask(__name__)
DB_FILE = "shamzam.db"

@app.route('/tracks', methods=['POST'])
def store_track():
    """Stores a track in Base64 encoding."""
    data = request.get_json()
    title = data.get('title')
    artist = data.get('artist')
    file_path = data.get('file_path')

    if not title or not artist or not file_path:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()
            encoded_file = base64.b64encode(raw_data).decode("ascii")
    except Exception as e:
        return jsonify({"error": "Failed to encode file", "details": str(e)}), 500

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tracks (title, artist, encoded_file) VALUES (?, ?, ?)",
                   (title, artist, encoded_file))
    conn.commit()
    conn.close()

    return jsonify({"message": "Track stored successfully"}), 201

@app.route('/tracks/<int:track_id>', methods=['GET'])
def retrieve_track(track_id):
    """Retrieves an encoded track from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT encoded_file FROM tracks WHERE id = ?", (track_id,))
    track = cursor.fetchone()
    conn.close()

    if track:
        return jsonify({"encoded_file": track[0]}), 200
    return jsonify({"error": "Track not found"}), 404

@app.route('/tracks/<int:track_id>', methods=['DELETE'])
def delete_track(track_id):
    """Deletes a track from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Track removed"}), 200

@app.route("/", methods=['GET'])
def home():
    return jsonify({"message": "Shamzam Track Storage API is running"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5003)
