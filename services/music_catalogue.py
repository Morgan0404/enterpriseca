import sys
import os
from flask import Flask, request, jsonify
import base64

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.repository import TrackRepository

app = Flask(__name__)
repo = TrackRepository()

@app.route('/tracks', methods=['GET'])
def list_tracks():
    tracks = repo.list_all()
    if not tracks:
        return jsonify({"error": "No tracks found"}), 404
    return jsonify({"tracks": tracks}), 200

@app.route('/tracks', methods=['POST'])
def add_track():
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
    title = request.args.get("title")
    artist = request.args.get("artist")
    if not title or not artist:
        return jsonify({"error": "Missing required parameters: title and artist"}), 400
    rowcount = repo.delete_by_title_artist(title, artist)
    if rowcount == 0:
        return jsonify({"error": "Track not found"}), 404
    return jsonify({"message": "Track removed"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)