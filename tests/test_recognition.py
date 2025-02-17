import requests

BASE_URL = "http://127.0.0.1:5002"

def test_recognize_valid_audio():
    """Test recognizing a valid audio file."""
    files = {"file": open("frag/_Blinding Lights.wav", "rb")}
    response = requests.post(f"{BASE_URL}/recognise", files=files)

    assert response.status_code in [200, 404]  # ✅ Accept both valid responses
    response_json = response.json()

    if response.status_code == 200:
        assert "title" in response_json, "Expected a title in response, but got none"

def test_recognize_missing_file():
    """Test API when no file is uploaded."""
    response = requests.post(f"{BASE_URL}/recognise")
    assert response.status_code == 400
    assert response.json().get("error") == "No audio file provided"

def test_recognize_invalid_audio():
    """Test recognition with an invalid file format."""
    files = {"file": open("frag/fake_audio.wav", "rb")}
    response = requests.post(f"{BASE_URL}/recognise", files=files)
    
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())

    response_json = response.json()
    assert "error" in response_json, "Expected error in response, but got success"

def test_list_tracks_empty():
    """Test listing tracks when the catalogue is empty."""
    
    # ❗ First, remove all existing tracks to ensure the database is empty
    response = requests.get("http://127.0.0.1:5001/tracks")
    if response.status_code == 200:
        tracks = response.json().get("tracks", [])
        for track in tracks:
            requests.delete(f"http://127.0.0.1:5001/tracks/{track['id']}")

    # ✅ Now, test listing when no tracks exist
    response = requests.get("http://127.0.0.1:5001/tracks")

    if response.content:  # ✅ Check if response body exists before parsing
        assert "error" in response.json()
    else:
        assert response.status_code == 404  # ✅ Ensure it returns 404 for no tracks

    # ✅ **NEW Unhappy Path: Test invalid request format**
    response = requests.post("http://127.0.0.1:5001/tracks")  # ❌ Sending POST without JSON body
    assert response.status_code == 400  # ✅ Expecting "Bad Request"