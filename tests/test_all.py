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

# Updated absolute paths (new location)
VALID_TEST_SONG = "./wavs/Blinding Lights.wav"
VALID_TEMP_SONG = "./wavs/fake_audio.wav"

# For recognition (S4), preload a track.
PRELOAD_TRACK = {
    "title": "Don't Look Back In Anger",  # Use exact punctuation as expected.
    "artist": "Oasis",
    "file_path": "./wavs/Don't Look Back In Anger.wav"
}
# Corresponding fragment file (S4 happy path) should be named with a tilde.
FRAGMENT_PATH = "./wavs/~Don't Look Back In Anger.wav"


# ------------------------- S4: Recognition Tests -------------------------
class TestRecognition(unittest.TestCase):
    def setUp(self):
        # Preload the catalogue with the expected track for recognition.
        requests.post(CATALOGUE_URL, json=PRELOAD_TRACK)

    def test_recognize_valid_audio(self):
        """
        S4 Happy Path:
        As a user, I want to convert a music fragment to a track,
        so that I can listen to it.
        This test verifies that a valid audio fragment returns a 200 response
        and that the full Base64 string (using testmode=true) decodes to a non‑empty WAV file.
        """
        try:
            with open(FRAGMENT_PATH, "rb") as audio_file:
                content = audio_file.read()
            files = {"file": (os.path.basename(FRAGMENT_PATH), content)}
        except FileNotFoundError:
            self.fail(f"Fragment file not found at path: {FRAGMENT_PATH}")
        
        # Request test mode to get the full encoded string.
        response = requests.post(f"{RECOGNITION_URL}?testmode=true", files=files)
        
        # Happy path: Expect 200 since the track is preloaded.
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}")
        response_json = response.json()
        self.assertIn("track", response_json, "Expected 'track' key in response, but got none")
        track = response_json["track"]
        self.assertIn("encoded_file", track, "Expected 'encoded_file' in track data, but got none")
        
        full_encoded = track["encoded_file"]
        # Write full encoded string for manual verification.
        with open("full_encoded_output.txt", "w") as f:
            f.write(full_encoded)
        
        # Decode and write out the full audio.
        try:
            wav_data = base64.b64decode(full_encoded)
        except Exception as e:
            self.fail(f"Decoding failed: {e}")
        
        with open("answer.wav", "wb") as out_f:
            out_f.write(wav_data)
        
        # Assert that the audio is non-empty.
        self.assertTrue(len(wav_data) > 0, "Decoded audio is empty")

    def test_recognize_missing_file(self):
        """
        S4 Unhappy Path:
        Test that if no file is uploaded, the service returns a 400 error.
        """
        response = requests.post(RECOGNITION_URL)
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}")
        self.assertEqual(response.json().get("error"), "No audio file provided")

    def test_recognize_invalid_audio(self):
        """
        S4 Unhappy Path:
        Test that if an invalid audio file is provided, the service returns an error.
        """
        try:
            with open(VALID_TEMP_SONG, "rb") as fake_audio:
                content = fake_audio.read()
            files = {"file": (os.path.basename(VALID_TEMP_SONG), content)}
        except FileNotFoundError:
            self.fail(f"Invalid audio file not found at path: {VALID_TEMP_SONG}")
        response = requests.post(RECOGNITION_URL, files=files)
        print("Recognition invalid audio - Status Code:", response.status_code)
        print("Recognition invalid audio - JSON:", response.json())
        response_json = response.json()
        self.assertIn("error", response_json, "Expected error in response, but got success")


# ------------------------- S1, S2, S3: Catalogue Tests -------------------------
class TestCatalogue(unittest.TestCase):
    def setUp(self):
        # Reset the catalogue database (covers S1, S2, S3 Happy Paths)
        repo = TrackRepository()
        repo.db_teardown()

    # --- S1: Adding a Music Track ---
    def test_add_track(self):
        """
        S1 Happy Path:
        As an administrator, I want to add a music track to the catalogue,
        so that a user can listen to it.
        This test verifies that adding a valid track returns a 201 response.
        """
        data = {
            "title": "Test Song",
            "artist": "Test Artist",
            "file_path": VALID_TEST_SONG
        }
        response = requests.post(CATALOGUE_URL, json=data)
        self.assertEqual(response.status_code, 201, f"Expected 201, got {response.status_code}")
        self.assertEqual(response.json().get("message"), "Track added successfully")

    def test_add_track_missing_fields(self):
        """
        S1 Unhappy Path:
        As an administrator, if I try to add a track with missing fields,
        the system should return a 400 error.
        """
        data = {"title": "Incomplete Song"}  # Missing 'artist' and 'file_path'
        response = requests.post(CATALOGUE_URL, json=data)
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}")
        self.assertIn("error", response.json())

    # --- S2: Removing a Music Track ---
    def test_remove_track(self):
        """
        S2 Happy Path:
        As an administrator, I want to remove a music track from the catalogue,
        so that a user cannot listen to it.
        This test verifies that removing an existing track (by title and artist) returns 200.
        """
        data = {
            "title": "Temp Song",
            "artist": "Temp Artist",
            "file_path": VALID_TEMP_SONG
        }
        add_response = requests.post(CATALOGUE_URL, json=data)
        self.assertEqual(add_response.status_code, 201)
        
        # Delete the track using query parameters.
        delete_url = f"{CATALOGUE_URL}?title=Temp%20Song&artist=Temp%20Artist"
        delete_response = requests.delete(delete_url)
        self.assertEqual(delete_response.status_code, 200, f"Expected 200, got {delete_response.status_code}")
        self.assertEqual(delete_response.json().get("message"), "Track removed")

    def test_remove_non_existent_track(self):
        """
        S2 Unhappy Path:
        As an administrator, if I try to remove a track that doesn't exist,
        the system should return a 404 error.
        """
        delete_url = f"{CATALOGUE_URL}?title=NonExistentSong&artist=NonExistentArtist"
        response = requests.delete(delete_url)
        self.assertEqual(response.status_code, 404, f"Expected 404, got {response.status_code}")
        try:
            data = response.json()
        except Exception:
            data = {}
        self.assertEqual(data.get("error"), "Track not found")

    # --- S3: Listing Music Tracks ---
    def test_list_tracks(self):
        """
        S3 Happy Path:
        As an administrator, I want to list the names of the music tracks in the catalogue,
        so that I know what it contains.
        This test verifies that after adding a track, the catalogue returns a list containing that track.
        """
        data = {
            "title": "Test Song",
            "artist": "Test Artist",
            "file_path": VALID_TEST_SONG
        }
        add_response = requests.post(CATALOGUE_URL, json=data)
        self.assertEqual(add_response.status_code, 201)
        
        response = requests.get(CATALOGUE_URL)
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}")
        tracks = response.json().get("tracks")
        self.assertIsInstance(tracks, list)
        found = any(track["title"] == "Test Song" and "encoded_file" in track for track in tracks)
        self.assertTrue(found, "Test Song not found or missing encoded_file")

    def test_list_tracks_empty(self):
        """
        S3 Unhappy Path:
        As an administrator, if the catalogue is empty, listing tracks should return a 404 error.
        """
        response = requests.get(CATALOGUE_URL)
        self.assertEqual(response.status_code, 404, f"Expected 404, got {response.status_code}")
        self.assertIn("error", response.json())
        self.assertEqual(response.json().get("error"), "No tracks found")

    def test_invalid_request_format(self):
        """
        S3 Unhappy/General Path:
        Test that an invalid POST request (without a JSON body) returns a 400 error.
        """
        response = requests.post(CATALOGUE_URL)
        self.assertEqual(response.status_code, 400, "Expected 400 for a bad request")

if __name__ == '__main__':
    unittest.main()
