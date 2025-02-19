# catalogue.py (or your preferred filename for microservice 2)
from flask import Flask, request, jsonify
import os, base64
from repository import TrackRepository

app = Flask(__name__)
repo = TrackRepository()

@app.route('/tracks', methods=['GET'])
def list_tracks():
    """
    Retrieve all tracks from the catalogue.
    Truncate the encoded_file to 100 characters for display.
    """
    tracks = repo.list_all()
    if not tracks:
        return jsonify({"error": "No tracks found"}), 404

    # Truncate encoded_file for display purposes
    for track in tracks:
        encoded_file = track["encoded_file"]
        track["encoded_file"] = encoded_file if len(encoded_file) <= 100 else encoded_file[:100] + "..."
    return jsonify({"tracks": tracks}), 200

@app.route('/tracks', methods=['POST'])
def add_track():
    """
    Add a full track to the catalogue.
    Reads the file, encodes it in Base64, and stores the track.
    """
    data = request.get_json()
    title = data.get('title')
    artist = data.get('artist')
    file_path = data.get('file_path')

    if not title or not artist or not file_path:
        return jsonify({"error": "Missing required fields"}), 400

    if not os.path.exists(file_path):
        return jsonify({"error": "Full track file does not exist at provided path"}), 400

    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()
            encoded_file = base64.b64encode(raw_data).decode("ascii")
    except Exception as e:
        return jsonify({"error": "Failed to encode file", "details": str(e)}), 500

    track_id = repo.insert({
        "title": title,
        "artist": artist,
        "encoded_file": encoded_file
    })
    return jsonify({"message": "Track added successfully", "track_id": track_id}), 201

@app.route('/tracks/<int:track_id>', methods=['DELETE'])
def remove_track(track_id):
    """
    Remove a track from the catalogue using its ID.
    """
    rowcount = repo.delete(track_id)
    if rowcount == 0:
        return jsonify({"error": "Track not found"}), 404

    return jsonify({"message": "Track removed"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)
