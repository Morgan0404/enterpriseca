import requests

BASE_URL = "http://127.0.0.1:5001"

# Update these absolute paths to point to valid files on your system.
VALID_TEST_SONG = "/Users/morgan/Desktop/EnterprsieCA/full/Blinding Lights.wav"
VALID_TEMP_SONG = "/Users/morgan/Desktop/EnterprsieCA/full/fake_audio.wav"

def test_add_track():
    """Test adding a valid track to the catalogue."""
    data = {
        "title": "Test Song",
        "artist": "Test Artist",
        "file_path": VALID_TEST_SONG
    }
    response = requests.post(f"{BASE_URL}/tracks", json=data)
    # Expect 201 if the file exists at the given path.
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    assert response.json().get("message") == "Track added successfully"

def test_list_tracks():
    """Test listing all tracks in the catalogue."""
    response = requests.get(f"{BASE_URL}/tracks")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    tracks = response.json().get("tracks")
    assert isinstance(tracks, list)
    # Check that "Test Song" exists and that it has an "encoded_file" key.
    assert any(track["title"] == "Test Song" and "encoded_file" in track for track in tracks), "Test Song not found or missing encoded_file"

def test_remove_track():
    """Test removing a track from the catalogue."""
    # First, add a track to ensure we have one to delete.
    data = {
        "title": "Temp Song",
        "artist": "Temp Artist",
        "file_path": VALID_TEMP_SONG
    }
    add_response = requests.post(f"{BASE_URL}/tracks", json=data)
    assert add_response.status_code == 201, f"Expected 201, got {add_response.status_code}"

    # Get the track ID for "Temp Song".
    response = requests.get(f"{BASE_URL}/tracks")
    tracks = response.json().get("tracks")
    track_id = next((t["id"] for t in tracks if t["title"] == "Temp Song"), None)
    assert track_id is not None, "Track ID not found"

    # Delete the track.
    delete_response = requests.delete(f"{BASE_URL}/tracks/{track_id}")
    assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
    assert delete_response.json().get("message") == "Track removed"

def test_add_track_missing_fields():
    """Test adding a track with missing required fields."""
    data = {"title": "Incomplete Song"}  # Missing artist & file_path
    response = requests.post(f"{BASE_URL}/tracks", json=data)
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert "error" in response.json()

def test_remove_non_existent_track():
    """Test removing a track that does not exist."""
    response = requests.delete(f"{BASE_URL}/tracks/99999")  # Assuming track ID 99999 does not exist
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    assert response.json().get("error") == "Track not found"

def test_list_tracks_empty():
    """Test listing tracks when the catalogue is empty."""
    # Remove all existing tracks.
    response = requests.get(f"{BASE_URL}/tracks")
    if response.status_code == 200:
        tracks = response.json().get("tracks", [])
        for track in tracks:
            requests.delete(f"{BASE_URL}/tracks/{track['id']}")

    response = requests.get(f"{BASE_URL}/tracks")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    assert "error" in response.json()
    assert response.json().get("error") == "No tracks found"
