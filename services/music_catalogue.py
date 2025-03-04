import sys
import os
from flask import Flask, request, jsonify
import base64

# Modify sys.path to include the project root directory for module imports (only if necessary)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the TrackRepository class from the services.repository module
from services.repository import TrackRepository

# Create a Flask application instance with the current module name
app = Flask(__name__)

# Instantiate a TrackRepository object for database operations
repo = TrackRepository()


@app.route('/tracks', methods=['GET'])
def list_tracks():
    """List all tracks in the catalogue; returns 200 with tracks or 404 if empty."""
    tracks = repo.list_all()
    if not tracks:
        return jsonify({"error": "No tracks found"}), 404
    return jsonify({"tracks": tracks}), 200

@app.route('/tracks', methods=['POST'])
def add_track():
    """Add a track to the catalogue from a JSON body; returns 201 on success, 400/500 on failure."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Missing JSON body"}), 400
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

@app.route('/tracks', methods=['DELETE'])
def remove_track():
    """Delete a track by title and artist from a JSON body; returns 200 on success, 400/404 on failure."""
    data = request.get_json(silent=True)
    if not data or "title" not in data or "artist" not in data:
        return jsonify({"error": "Missing required fields: title and artist"}), 400
    title = data.get("title")
    artist = data.get("artist")
    rowcount = repo.delete_by_title_artist(title, artist)
    if rowcount == 0:
        return jsonify({"error": "Track not found"}), 404
    return jsonify({"message": "Track removed"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)