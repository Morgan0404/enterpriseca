from flask import Flask, request, jsonify
import requests
import os
import base64

app = Flask(__name__)

# Retrieve the API key from the environment variable.
try:
    API_KEY = os.environ["KEY"]
except KeyError:
    raise Exception("Environment variable KEY not set. Please set it before running the service.")

@app.route("/audapi", methods=["POST"])
def audapi():
    """
    Receives a Base64-encoded audio file in JSON, decodes it, and forwards it to the audd.io API
    for recognition.
    """
    # Expect JSON input
    data = request.get_json()
    if not data or "file" not in data:
        return jsonify({"error": "Missing or invalid JSON body with 'file' field"}), 400

    base64_encoded = data.get("file")
    filename = data.get("filename", "audio.wav")  # Default filename if not provided

    # Decode Base64 to raw binary data
    try:
        raw_data = base64.b64decode(base64_encoded)
    except Exception as e:
        return jsonify({"error": "Failed to decode Base64 audio", "details": str(e)}), 400

    # Prepare the file as multipart/form-data for audd.io
    files = {"file": (filename, raw_data)}
    data = {"api_token": API_KEY}

    try:
        response = requests.post("https://api.audd.io/", files=files, data=data)
    except requests.exceptions.RequestException:
        return jsonify({"error": "AudD API call failed"}), 500

    if response.status_code == 200:
        result = response.json().get("result")
        if result and "title" in result and "artist" in result:
            return jsonify({"result": result}), 200
        else:
            return jsonify({"error": "Recognition failed"}), 500
    return jsonify({"error": "Failed to process audio"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5003)