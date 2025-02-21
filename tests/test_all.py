import sys
import os
import unittest
import requests
import base64

# Insert the project root so that the services folder is in the Python path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.repository import TrackRepository

# Base URLs for the two services.
RECOGNITION_URL = "http://127.0.0.1:5002/recognise"
CATALOGUE_URL = "http://127.0.0.1:5001/tracks"

# Update these absolute paths to valid files on your system.
VALID_TEST_SONG = "/Users/morgan/Desktop/EnterpriseCA/full/Blinding Lights.wav"
VALID_TEMP_SONG = "/Users/morgan/Desktop/EnterpriseCA/full/fake_audio.wav"

class TestRecognition(unittest.TestCase):
    def setUp(self):
        # Preload the catalogue with the expected track so that recognition returns 200.
        # Ensure that the preloaded track exactly matches what AudD.io returns.
        track_data = {
            "title": "Don't Look Back In Anger",  # Use exact punctuation
            "artist": "Oasis",
            "file_path": "/Users/morgan/Desktop/EnterpriseCA/full/Dont Look Back In Anger.wav"
        }
        # Add the track to the catalogue. (If it already exists, that's acceptable.)
        requests.post(CATALOGUE_URL, json=track_data)

    def test_recognize_valid_audio(self):
        """Test recognizing a valid audio file and decode the full encoded string into answer.wav."""
        with open("frag/_Dont Look Back In Anger.wav", "rb") as audio_file:
            files = {"file": audio_file}
            # Use testmode=true to get the full encoded string (no truncation)
            response = requests.post(f"{RECOGNITION_URL}?testmode=true", files=files)
        
        # We expect a 200 response now that the track exists in the catalogue.
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}")
        response_json = response.json()
        self.assertIn("track", response_json, "Expected 'track' key in response, but got none")
        track = response_json["track"]
        self.assertIn("encoded_file", track, "Expected 'encoded_file' in track data, but got none")
        
        full_encoded = track["encoded_file"]
        # Write the full encoded string to a file for verification.
        with open("full_encoded_output.txt", "w") as f:
            f.write(full_encoded)
        
        # Decode the full Base64 string and write it to answer.wav.
        try:
            wav_data = base64.b64decode(full_encoded)
        except Exception as e:
            self.fail(f"Decoding failed: {e}")
        
        with open("answer.wav", "wb") as out_f:
            out_f.write(wav_data)
        
        # Assert that the decoded audio is non-empty.
        self.assertTrue(len(wav_data) > 0, "Decoded audio is empty")
        
    def test_recognize_missing_file(self):
        """Test API behavior when no file is uploaded."""
        response = requests.post(RECOGNITION_URL)
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}")
        self.assertEqual(response.json().get("error"), "No audio file provided")

    def test_recognize_invalid_audio(self):
        """Test recognition with an invalid file format."""
        with open("frag/fake_audio.wav", "rb") as fake_audio:
            files = {"file": fake_audio}
            response = requests.post(RECOGNITION_URL, files=files)
        print("Recognition invalid audio - Status Code:", response.status_code)
        print("Recognition invalid audio - JSON:", response.json())
        response_json = response.json()
        self.assertIn("error", response_json, "Expected error in response, but got success")


class TestCatalogue(unittest.TestCase):
    def setUp(self):
        # Reset the catalogue database before each test.
        repo = TrackRepository()
        repo.db_teardown()

    def test_add_track(self):
        """Test adding a valid track to the catalogue."""
        data = {
            "title": "Test Song",
            "artist": "Test Artist",
            "file_path": VALID_TEST_SONG
        }
        response = requests.post(CATALOGUE_URL, json=data)
        self.assertEqual(response.status_code, 201,
                         f"Expected 201, got {response.status_code}")
        self.assertEqual(response.json().get("message"), "Track added successfully")

    def test_list_tracks(self):
        """Test listing all tracks in the catalogue."""
        # Add a track so that there is something to list.
        data = {
            "title": "Test Song",
            "artist": "Test Artist",
            "file_path": VALID_TEST_SONG
        }
        add_response = requests.post(CATALOGUE_URL, json=data)
        self.assertEqual(add_response.status_code, 201)
        
        response = requests.get(CATALOGUE_URL)
        self.assertEqual(response.status_code, 200,
                         f"Expected 200, got {response.status_code}")
        tracks = response.json().get("tracks")
        self.assertIsInstance(tracks, list)
        # Check that "Test Song" exists and includes an "encoded_file" key.
        found = any(track["title"] == "Test Song" and "encoded_file" in track for track in tracks)
        self.assertTrue(found, "Test Song not found or missing encoded_file")

    def test_remove_track(self):
        """Test removing a track from the catalogue."""
        data = {
            "title": "Temp Song",
            "artist": "Temp Artist",
            "file_path": VALID_TEMP_SONG
        }
        add_response = requests.post(CATALOGUE_URL, json=data)
        self.assertEqual(add_response.status_code, 201)
        
        response = requests.get(CATALOGUE_URL)
        tracks = response.json().get("tracks")
        track_id = next((t["id"] for t in tracks if t["title"] == "Temp Song"), None)
        self.assertIsNotNone(track_id, "Track ID not found")
        
        delete_response = requests.delete(f"{CATALOGUE_URL}/{track_id}")
        self.assertEqual(delete_response.status_code, 200,
                         f"Expected 200, got {delete_response.status_code}")
        self.assertEqual(delete_response.json().get("message"), "Track removed")

    def test_add_track_missing_fields(self):
        """Test adding a track with missing required fields."""
        data = {"title": "Incomplete Song"}  # Missing 'artist' and 'file_path'
        response = requests.post(CATALOGUE_URL, json=data)
        self.assertEqual(response.status_code, 400,
                         f"Expected 400, got {response.status_code}")
        self.assertIn("error", response.json())

    def test_remove_non_existent_track(self):
        """Test removing a track that does not exist."""
        response = requests.delete(f"{CATALOGUE_URL}/99999")
        self.assertEqual(response.status_code, 404,
                         f"Expected 404, got {response.status_code}")
        self.assertEqual(response.json().get("error"), "Track not found")

    def test_list_tracks_empty(self):
        """Test listing tracks when the catalogue is empty."""
        response = requests.get(CATALOGUE_URL)
        self.assertEqual(response.status_code, 404,
                         f"Expected 404, got {response.status_code}")
        self.assertIn("error", response.json())
        self.assertEqual(response.json().get("error"), "No tracks found")

    def test_invalid_request_format(self):
        """Test an invalid POST request without a JSON body."""
        response = requests.post(CATALOGUE_URL)
        self.assertEqual(response.status_code, 400,
                         "Expected 400 for a bad request")

if __name__ == '__main__':
    unittest.main()
