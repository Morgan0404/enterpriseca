import sys
import os
import unittest
import requests
import base64
import os





# Insert the project root so that the services folder is in the Python path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.repository import TrackRepository

# Base URLs for the two services.
RECOGNITION_URL = "http://127.0.0.1:5002/recognise"
CATALOGUE_URL = "http://127.0.0.1:5001/tracks"

# Updated absolute paths (new location)
VALID_TEST_SONG = "./wavs/Blinding Lights.wav"
UNRECOGNIZED_AUDIO = "./wavs/~Davos.wav"

# For S4 (Recognition Happy Path), preload a known track.
PRELOAD_TRACK = {
    "title": "Don't Look Back In Anger",
    "artist": "Oasis",
    "file_path": "./wavs/Don't Look Back In Anger.wav"
}
FRAGMENT_PATH = "./wavs/~Don't Look Back In Anger.wav"

# ======================== S4: Recognition Tests ========================
class TestRecognition(unittest.TestCase):
    def setUp(self):
        # S4 Happy Path Preload:
        # Preload the catalogue with a track known to be recognized.
        response = requests.post(CATALOGUE_URL, json=PRELOAD_TRACK)
        self.assertEqual(response.status_code, 201, "Failed to preload track for recognition tests")

    def test_recognise_valid_audio_happy(self):
        """
        S4 Happy Path:
        As a user, I want to convert a music fragment to a track so that I can listen to it.
        This test verifies that a valid audio fragment returns a 200 response and that the full
        Base64-encoded audio (with testmode=true) decodes into a non-empty WAV file.
        """
        try:
            with open(FRAGMENT_PATH, "rb") as audio_file:
                content = audio_file.read()
            files = {"file": (os.path.basename(FRAGMENT_PATH), content)}
        except FileNotFoundError:
            self.fail(f"Fragment file not found at path: {FRAGMENT_PATH}")
        
        # Call the recognition service in test mode to get the full (non-truncated) encoded string.
        response = requests.post(f"{RECOGNITION_URL}?testmode=true", files=files)
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}: {response.text}")
        
        response_json = response.json()
        self.assertIn("encoded_base64", response_json, "Expected 'encoded_base64' key in response")
        
        full_encoded = response_json["encoded_base64"]
        # Write the full encoded string to a file for manual verification.
        with open("full_encoded_output.txt", "w") as f:
            f.write(full_encoded)
        
        # Decode the full Base64 string and write it to fulltrackbacktest.wav
        try:
            wav_data = base64.b64decode(full_encoded)
        except Exception as e:
            self.fail(f"Decoding failed: {e}")
        with open("fulltrackbacktest.wav", "wb") as out_f:
            out_f.write(wav_data)
        
        # Assert that the decoded audio is non-empty.
        self.assertTrue(len(wav_data) > 0, "Decoded audio is empty")

    def test_recognise_missing_file_unhappy(self):
        """
        S4 Unhappy Path:
        As a user, if I do not upload a file, I should receive a 400 error.
        """
        response = requests.post(RECOGNITION_URL)
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}")
        self.assertEqual(response.json().get("error"), "No audio file provided")

    def test_recognise_invalid_audio_unhappy(self):
        """
        S4 Unhappy Path:
        As a user, if I upload an audio file that cannot be processed (unrecognised by AudD.io),
        I should receive an error.
        This test uses an unrecognized audio file (e.g., ~Davos.wav).
        """
        try:
            with open(UNRECOGNIZED_AUDIO, "rb") as audio_file:
                content = audio_file.read()
            files = {"file": (os.path.basename(UNRECOGNIZED_AUDIO), content)}
        except FileNotFoundError:
            self.fail(f"Unrecognized audio file not found at path: {UNRECOGNIZED_AUDIO}")
            
        response = requests.post(RECOGNITION_URL, files=files)
        self.assertEqual(response.status_code, 500, f"Expected 500 for unrecognized audio, got {response.status_code}: {response.text}")
        try:
            resp_json = response.json()
        except Exception:
            self.fail(f"Response did not contain valid JSON: {response.text}")
        self.assertEqual(resp_json.get("error"), "Recognition failed")
    
    def test_recognise_invalid_audio_format_unhappy(self):
        """
        S4 Unhappy Path:
        If I upload a non-audio file (e.g., a text file), the system should return a 400 error.
        """
        # Create a dummy text file content (simulating an invalid audio file)
        invalid_content = b"This is not an audio file."
        files = {"file": ("invalid.txt", invalid_content)}

        response = requests.post(RECOGNITION_URL, files=files)

        # Expecting a 400 error due to invalid file format
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}")
        self.assertIn("error", response.json())
        self.assertEqual(response.json().get("error"), "Invalid audio file format")

# ======================== S1, S2, S3: Catalogue Tests ========================
class TestCatalogue(unittest.TestCase):
    def setUp(self):
        # Reset the catalogue database before each test to ensure a clean state.
        repo = TrackRepository()
        repo.db_teardown()

    # ----- S1: Adding a Music Track -----
    def test_add_track_happy(self):
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

    def test_add_track_unhappy_missing_fields(self):
        """
        S1 Unhappy Path:
        If I try to add a track with missing required fields,
        the system should return a 400 error.
        """
        data = {"title": "Incomplete Song"}  # Missing 'artist' and 'file_path'
        response = requests.post(CATALOGUE_URL, json=data)
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}")
        self.assertIn("error", response.json())
    
    def test_add_track_unhappy_nonexistent_file(self):
        """
        S1 Unhappy Path:
        If I try to add a track with a non-existent file path,
        the system should return a 400 error.
        """
        data = {
            "title": "Ghost Track",
            "artist": "Phantom Artist",
            "file_path": "/invalid/path/to/nonexistent.wav"  # Non-existent file
        }
        response = requests.post(CATALOGUE_URL, json=data)
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}")
        self.assertIn("error", response.json())
        self.assertEqual(response.json().get("error"), "Full track file does not exist at provided path")
    
    
        
    


    # ----- S2: Removing a Music Track -----
    def test_remove_track_happy(self):
        """
        S2 Happy Path:
        As an administrator, I want to remove a music track from the catalogue,
        so that a user cannot listen to it.
        This test verifies that removing an existing track (by title and artist) returns a 200 response.
        """
        data = {
            "title": "Temp Song",
            "artist": "Temp Artist",
            "file_path": VALID_TEST_SONG  # Using a valid file path.
        }
        add_response = requests.post(CATALOGUE_URL, json=data)
        self.assertEqual(add_response.status_code, 201)
        
        # Delete the track using query parameters.
        delete_url = f"{CATALOGUE_URL}?title=Temp%20Song&artist=Temp%20Artist"
        delete_response = requests.delete(delete_url)
        self.assertEqual(delete_response.status_code, 200, f"Expected 200, got {delete_response.status_code}")
        self.assertEqual(delete_response.json().get("message"), "Track removed")

    def test_remove_track_unhappy_nonexistent(self):
        """
        S2 Unhappy Path:
        If I try to remove a track that does not exist,
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
    
    def test_remove_track_unhappy_missing_parameters(self):
        """
        S2 Unhappy Path:
        If I try to remove a track without providing both 'title' and 'artist',
        the system should return a 400 Bad Request error.
        """
        # Attempt to delete a track with only the title (missing artist)
        delete_url = f"{CATALOGUE_URL}?title=SomeSong"
        response1 = requests.delete(delete_url)
        self.assertEqual(response1.status_code, 400, f"Expected 400, got {response1.status_code}")
        self.assertIn("error", response1.json())
        self.assertEqual(response1.json().get("error"), "Missing required parameters: title and artist")

        # Attempt to delete a track with only the artist (missing title)
        delete_url = f"{CATALOGUE_URL}?artist=SomeArtist"
        response2 = requests.delete(delete_url)
        self.assertEqual(response2.status_code, 400, f"Expected 400, got {response2.status_code}")
        self.assertIn("error", response2.json())
        self.assertEqual(response2.json().get("error"), "Missing required parameters: title and artist")

        # Attempt to delete a track with neither title nor artist
        delete_url = f"{CATALOGUE_URL}"
        response3 = requests.delete(delete_url)
        self.assertEqual(response3.status_code, 400, f"Expected 400, got {response3.status_code}")
        self.assertIn("error", response3.json())
        self.assertEqual(response3.json().get("error"), "Missing required parameters: title and artist")


    
    

    # ----- S3: Listing Music Tracks -----
    def test_list_tracks_happy(self):
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

    def test_list_tracks_unhappy_empty(self):
        """
        S3 Unhappy Path:
        If the catalogue is empty, listing tracks should return a 404 error.
        """
        response = requests.get(CATALOGUE_URL)
        self.assertEqual(response.status_code, 404, f"Expected 404, got {response.status_code}")
        self.assertIn("error", response.json())
        self.assertEqual(response.json().get("error"), "No tracks found")

    def test_invalid_request_format(self):
        """
        S3 Unhappy/General Path:
        An invalid POST request (without a JSON body) should return a 400 error.
        """
        response = requests.post(CATALOGUE_URL)
        self.assertEqual(response.status_code, 400, "Expected 400 for a bad request")

if __name__ == '__main__':
    unittest.main()
