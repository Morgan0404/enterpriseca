import requests

BASE_URL = "http://127.0.0.1:5001"

def test_add_track():
    """Test adding a valid track to the catalogue."""
    data = {"title": "Test Song", "artist": "Test Artist", "file_path": "test_song.mp3"}
    response = requests.post(f"{BASE_URL}/tracks", json=data)
    assert response.status_code == 201
    assert response.json().get("message") == "Track added successfully"

def test_list_tracks():
    """Test listing all tracks in the catalogue."""
    response = requests.get(f"{BASE_URL}/tracks")
    assert response.status_code == 200
    tracks = response.json().get("tracks")
    assert isinstance(tracks, list)
    assert any(track["title"] == "Test Song" for track in tracks)  # Ensure "Test Song" exists

def test_remove_track():
    """Test removing a track from the catalogue."""
    # First, add a track to ensure we have one to delete
    data = {"title": "Temp Song", "artist": "Temp Artist", "file_path": "temp.mp3"}
    add_response = requests.post(f"{BASE_URL}/tracks", json=data)
    assert add_response.status_code == 201

    # Get the latest track ID
    response = requests.get(f"{BASE_URL}/tracks")
    tracks = response.json().get("tracks")
    track_id = next((t["id"] for t in tracks if t["title"] == "Temp Song"), None)
    assert track_id is not None, "Track ID not found"

    # Delete the track
    delete_response = requests.delete(f"{BASE_URL}/tracks/{track_id}")
    assert delete_response.status_code == 200
    assert delete_response.json().get("message") == "Track removed"

def test_add_track_missing_fields():
    """Test adding a track with missing required fields."""
    data = {"title": "Incomplete Song"}  # Missing artist & file_path
    response = requests.post(f"{BASE_URL}/tracks", json=data)
    assert response.status_code == 400
    assert "error" in response.json()

def test_remove_non_existent_track():
    """Test removing a track that does not exist."""
    response = requests.delete(f"{BASE_URL}/tracks/99999")  # Assuming track ID 99999 does not exist
    assert response.status_code == 404  # ✅ Now correctly expects 404
    assert response.json().get("error") == "Track not found"  # ✅ Match expected error message

def test_list_tracks_empty():
    """Test listing tracks when the catalogue is empty."""
    
    # ❗ First, remove all existing tracks to ensure the database is empty
    response = requests.get(f"{BASE_URL}/tracks")
    if response.status_code == 200:  # If there are tracks, delete them
        tracks = response.json().get("tracks", [])
        for track in tracks:
            requests.delete(f"{BASE_URL}/tracks/{track['id']}")

    # ✅ Now, run the actual test
    response = requests.get(f"{BASE_URL}/tracks")
    assert response.status_code == 404  # ✅ Expecting 404, since the API returns "No tracks found"
    assert "error" in response.json()
    assert response.json().get("error") == "No tracks found"
