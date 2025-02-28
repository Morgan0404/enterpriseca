from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Retrieve the API key from the environment variable.
try:
    API_KEY = os.environ["KEY"]
except KeyError:
    raise Exception("Environment variable KEY not set. Please set it before running the service.")

@app.route("/recognize_audio", methods=["POST"])
def recognize_audio():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No audio file provided"}), 400

    files = {"file": (file.filename, file.read())}
    data = {"api_token": API_KEY}
    try:
        response = requests.post("https://api.audd.io/", files=files, data=data)
    except requests.exceptions.RequestException:
        return jsonify({"error": "AudD API call failed"}), 500

    if response.status_code == 200:
        # Get the result without defaulting to an empty dict.
        result = response.json().get("result")
        if result and "title" in result and "artist" in result:
            return jsonify({"result": result}), 200
        else:
            return jsonify({"error": "Recognition failed"}), 500
    return jsonify({"error": "Failed to process audio"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5003)
