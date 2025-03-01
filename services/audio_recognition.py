from flask import Flask, request, jsonify
import requests
import os
import base64
from repository import TrackRepository

app = Flask(__name__)

# Initialize the repository (it creates the table if needed)
repo = TrackRepository()

# Define the URL of the new aud_service microservice.
AUD_SERVICE_URL = "http://127.0.0.1:5003/recognize_audio"

@app.route("/", methods=['GET'])
def home():
    return jsonify({"message": "Shamzam Audio Recognition API is running"}), 200

@app.route('/recognise', methods=['POST'])
def recognise_track():
    """
    Receives an audio fragment, encodes it as Base64, forwards it to the aud_service microservice
    as JSON for recognition, then checks if the corresponding full track exists in the catalogue.
    If found, returns JSON with a message, selected metadata, and the encoded Base64 audio.
    
    When the query parameter testmode=true is present (case-insensitive),
    the full Base64-encoded audio is returned without truncation.
    """
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No audio file provided"}), 400

    # Read the raw binary data and encode it as Base64
    raw_data = file.read()
    base64_encoded = base64.b64encode(raw_data).decode('ascii')

    # Prepare JSON payload instead of multipart/form-data
    payload = {
        "file": base64_encoded,
        "filename": file.filename
    }

    try:
        # Send the Base64-encoded file as JSON to aud_service
        aud_response = requests.post(AUD_SERVICE_URL, json=payload)
    except requests.exceptions.RequestException:
        return jsonify({"error": "Recognition failed"}), 500

    if aud_response.status_code == 200:
        result = aud_response.json().get("result")
        if result and "title" in result and "artist" in result:
            selected_metadata = {
                "title": result.get("title"),
                "artist": result.get("artist"),
                "album": result.get("album"),
                "release_date": result.get("release_date")
            }
            # Look up the track in the catalogue by title and artist
            catalogue_metadata = repo.lookup_by_title_artist(result["title"], result["artist"])
            if catalogue_metadata:
                encoded = catalogue_metadata.get("encoded_file", "")
                test_mode = request.args.get("testmode", "false").lower() == "true"
                if not test_mode and len(encoded) > 100:
                    encoded = encoded[:100] + "..."
                return jsonify({
                    "message": "Track recognised and found in catalogue",
                    "metadata": selected_metadata,
                    "encoded_base64": encoded
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
    return jsonify({"error": "Recognition failed"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)