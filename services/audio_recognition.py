from flask import Flask, request, jsonify
import requests
import sqlite3

app = Flask(__name__)
API_KEY = "5290aaf3282bc88ef23a7184f76eeb22"
DB_FILE = "shamzam.db"

def track_exists(title, artist):
    """Checks if the recognised track exists in the catalogue."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tracks WHERE title = ? AND artist = ?", (title, artist))
    track = cursor.fetchone()
    conn.close()
    return track is not None

@app.route("/", methods=['GET'])
def home():
    return jsonify({"message": "Shamzam Audio Recognition API is running"}), 200

@app.route('/recognise', methods=['POST'])
def recognise_track():
    file = request.files.get('file')

    if not file:
        return jsonify({"error": "No audio file provided"}), 400

    files = {'file': (file.filename, file.read())}
    data = {'api_token': API_KEY}
    response = requests.post("https://api.audd.io/", files=files, data=data)

    if response.status_code == 200:
        result = response.json().get("result", {})

        if "title" in result and "artist" in result:
            track_found = track_exists(result["title"], result["artist"])
            if track_found:
                return jsonify({"message": "Track recognised and found in catalogue", "title": result["title"], "artist": result["artist"]}), 200
            else:
                return jsonify({"message": "Track recognised but not found in catalogue", "title": result["title"], "artist": result["artist"]}), 404
        else:
            return jsonify({"error": "Recognition failed"}), 500

    return jsonify({"error": "Failed to process audio"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)
