from flask import Flask, request, jsonify
import requests
import os
from repository import TrackRepository  # Make sure services is a package

app = Flask(__name__)

# Read the API key from Key.txt
try:
    with open("Key.txt", "r") as key_file:
        API_KEY = key_file.read().strip()
except Exception as e:
    raise Exception("Failed to read API key from Key.txt: " + str(e))

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
    
    If the query parameter testmode=true is present, the full Base64-encoded string is returned
    without truncation, so that tests can decode it and verify the complete audio.
    """
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No audio file provided"}), 400

    # Send the audio file to AudD.io
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
            # Use the repository to look up the track by title and artist.
            catalogue_metadata = repo.lookup_by_title_artist(result["title"], result["artist"])
            if catalogue_metadata:
                # Check for test mode: if not in test mode, truncate the encoded_file.
                if request.args.get("testmode") != "true":
                    encoded = catalogue_metadata.get("encoded_file", "")
                    if len(encoded) > 100:
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
        return jsonify({"error": "Recognition failed"}), 500
    return jsonify({"error": "Failed to process audio"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)
