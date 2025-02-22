from flask import Flask, request, jsonify
import requests
import os
from repository import TrackRepository  # Make sure services is a package

app = Flask(__name__)

# Retrieve the API key from the environment variable.
try:
    API_KEY = os.environ["KEY"]
except KeyError:
    raise Exception("Environment variable KEY not set. Please set it before running the service.")

# Initialize the repository (it creates the table if needed)
repo = TrackRepository()

@app.route("/", methods=['GET'])
def home():
    return jsonify({"message": "Shamzam Audio Recognition API is running"}), 200

@app.route('/recognise', methods=['POST'])
def recognise_track():
    """
    Receives an audio fragment, sends it to AudD.io for recognition,
    then checks if the corresponding full track exists in the catalogue using the repository.
    If found, returns JSON with a message, the catalogue track, and selected metadata from AudD.io.
    
    When the query parameter testmode=true is present (case-insensitive),
    the full Base64-encoded audio is returned without truncation.
    """
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No audio file provided"}), 400

    # Send the audio file to AudD.io
    files = {'file': (file.filename, file.read())}
    data = {'api_token': API_KEY}
    try:
        response = requests.post("https://api.audd.io/", files=files, data=data)
    except requests.exceptions.RequestException as e:
        # Catch connection errors and return a JSON error response.
        return jsonify({"error": "Recognition failed"}), 500

    if response.status_code == 200:
        # Do not default result to {} so that a missing result is detected.
        result = response.json().get("result")
        if result and "title" in result and "artist" in result:
            selected_metadata = {
                "title": result.get("title"),
                "artist": result.get("artist"),
                "album": result.get("album"),
                "release_date": result.get("release_date")
            }
            # Look up the track in the catalogue by title and artist.
            catalogue_metadata = repo.lookup_by_title_artist(result["title"], result["artist"])
            if catalogue_metadata:
                encoded = catalogue_metadata.get("encoded_file", "")
                test_mode = request.args.get("testmode", "false").lower() == "true"
                if not test_mode and len(encoded) > 100:
                    catalogue_metadata["encoded_file"] = encoded[:100] + "..."
                return jsonify({
                    "message": "Track recognised and found in catalogue",
                    "metadata": selected_metadata,
                    "track": catalogue_metadata
                }), 200
            else:
                return jsonify({
                    "message": "Track recognised but not found in catalogue",
                    "title": result["title"],
                    "artist": result["artist"],
                    "metadata": selected_metadata
                }), 404
        else:
            return jsonify({"error": "Recognition failed"}), 500
    return jsonify({"error": "Failed to process audio"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)
