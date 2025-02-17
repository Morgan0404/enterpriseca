from flask import Flask, request, jsonify
import requests
import sqlite3

app = Flask(__name__)
API_KEY = "5290aaf3282bc88ef23a7184f76eeb22"  # Replace with your AudD.io API key
DB_FILE = "shamzam.db"

def get_track_metadata(title, artist):
    """
    Look up a track in the catalogue using its title and artist.
    Returns a dictionary with id, title, artist, and the Base85-encoded full track (truncated for display).
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, artist, encoded_file FROM tracks WHERE title = ? AND artist = ?",
        (title, artist)
    )
    track = cursor.fetchone()
    conn.close()
    if track:
        encoded_file = track[3]
        truncated = encoded_file if len(encoded_file) <= 100 else encoded_file[:100] + "..."
        return {
            "id": track[0],
            "title": track[1],
            "artist": track[2],
            "encoded_file": truncated
        }
    return None

@app.route("/", methods=['GET'])
def home():
    return jsonify({"message": "Shamzam Audio Recognition API is running"}), 200

@app.route('/recognise', methods=['POST'])
def recognise_track():
    """
    Receives an audio fragment, sends it to AudD.io for recognition,
    and then checks if the corresponding full track (added by the admin) exists in the catalogue.
    Returns a JSON response containing:
      - A message indicating success or failure,
      - The catalogue metadata (including the truncated Base85-encoded full track),
      - A selected subset of metadata from AudD.io (title, artist, album, release_date).
    """
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No audio file provided"}), 400

    files = {'file': (file.filename, file.read())}
    data = {'api_token': API_KEY}
    response = requests.post("https://api.audd.io/", files=files, data=data)
    if response.status_code == 200:
        result = response.json().get("result", {})
        if "title" in result and "artist" in result:
            selected_metadata = {
                "title": result.get("title"),
                "artist": result.get("artist"),
                "album": result.get("album"),
                "release_date": result.get("release_date")
            }
            catalogue_metadata = get_track_metadata(result["title"], result["artist"])
            if catalogue_metadata:
                return jsonify({
                    "message": "Track recognised and found in catalogue",
                    "track": catalogue_metadata,
                    "metadata": selected_metadata
                }), 200
            else:
                return jsonify({
                    "message": "Track recognised but not found in catalogue",
                    "title": result["title"],
                    "artist": result["artist"],
                    "metadata": selected_metadata
                }), 404
        return jsonify({"error": "Recognition failed"}), 500
    return jsonify({"error": "Failed to process audio"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)
