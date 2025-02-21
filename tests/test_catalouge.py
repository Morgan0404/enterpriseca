import sys
import os
import unittest
import requests

# Insert the project root so that the services folder is in the Python path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.repository import TrackRepository

# Base URL for the catalogue service.
BASE_URL = "http://127.0.0.1:5001/tracks"

# Update these absolute paths to valid files on your system.
VALID_TEST_SONG = "/Users/morgan/Desktop/EnterpriseCA/full/Blinding Lights.wav"
VALID_TEMP_SONG = "/Users/morgan/Desktop/EnterpriseCA/full/fake_audio.wav"

def reset_database():
    """Reset the database by calling the repository's db_teardown() method."""
    repo = TrackRepository()
    repo.db_teardown()

class TestCatalogue(unittest.TestCase):
    def setUp(self):
        # Reset the database before each test to ensure a clean state.
        reset_database()

    def test_add_track(self):
        """Test adding a valid track to the catalogue."""
        data = {
            "title": "Test Song",
            "artist": "Test Artist",
            "file_path": VALID_TEST_SONG
        }
        response = requests.post(BASE_URL, json=data)
        self.assertEqual(response.status_code, 201,
                         f"Expected 201, got {response.status_code}")
        self.assertEqual(response.json().get("message"), "Track added successfully")

    def test_list_tracks(self):
        """Test listing all tracks in the catalogue."""
        # Add a track so there is something to list.
        data = {
            "title": "Test Song",
            "artist": "Test Artist",
            "file_path": VALID_TEST_SONG
        }
        add_response = requests.post(BASE_URL, json=data)
        self.assertEqual(add_response.status_code, 201)

        response = requests.get(BASE_URL)
        self.assertEqual(response.status_code, 200,
                         f"Expected 200, got {response.status_code}")
        tracks = response.json().get("tracks")
        self.assertIsInstance(tracks, list)
        # Check that "Test Song" exists and includes an "encoded_file" key.
        found = any(track["title"] == "Test Song" and "encoded_file" in track
                    for track in tracks)
        self.assertTrue(found, "Test Song not found or missing encoded_file")

    def test_remove_track(self):
        """Test removing a track from the catalogue."""
        # Add a track first.
        data = {
            "title": "Temp Song",
            "artist": "Temp Artist",
            "file_path": VALID_TEMP_SONG
        }
        add_response = requests.post(BASE_URL, json=data)
        self.assertEqual(add_response.status_code, 201)

        # Retrieve the track list to find the ID.
        response = requests.get(BASE_URL)
        tracks = response.json().get("tracks")
        track_id = next((t["id"] for t in tracks if t["title"] == "Temp Song"), None)
        self.assertIsNotNone(track_id, "Track ID not found")

        # Delete the track.
        delete_response = requests.delete(f"{BASE_URL}/{track_id}")
        self.assertEqual(delete_response.status_code, 200,
                         f"Expected 200, got {delete_response.status_code}")
        self.assertEqual(delete_response.json().get("message"), "Track removed")

    def test_add_track_missing_fields(self):
        """Test adding a track with missing required fields."""
        data = {"title": "Incomplete Song"}  # Missing 'artist' and 'file_path'
        response = requests.post(BASE_URL, json=data)
        self.assertEqual(response.status_code, 400,
                         f"Expected 400, got {response.status_code}")
        self.assertIn("error", response.json())

    def test_remove_non_existent_track(self):
        """Test removing a track that does not exist."""
        response = requests.delete(f"{BASE_URL}/99999")  # Assuming 99999 does not exist.
        self.assertEqual(response.status_code, 404,
                         f"Expected 404, got {response.status_code}")
        self.assertEqual(response.json().get("error"), "Track not found")

    def test_list_tracks_empty(self):
        """Test listing tracks when the catalogue is empty."""
        # Since setUp resets the database, there should be no tracks.
        response = requests.get(BASE_URL)
        self.assertEqual(response.status_code, 404,
                         f"Expected 404, got {response.status_code}")
        self.assertIn("error", response.json())
        self.assertEqual(response.json().get("error"), "No tracks found")

    def test_invalid_request_format(self):
        """Test an invalid POST request without a JSON body."""
        response = requests.post(BASE_URL)
        self.assertEqual(response.status_code, 400,
                         "Expected 400 for a bad request")

if __name__ == '__main__':
    unittest.main()
