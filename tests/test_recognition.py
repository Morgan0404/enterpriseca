import unittest
import requests
import base64

# Base URL for the recognition service.
BASE_URL = "http://127.0.0.1:5002"

class TestRecognition(unittest.TestCase):

    def test_recognize_valid_audio(self):
        """Test recognizing a valid audio file."""
        with open("frag/_Blinding Lights.wav", "rb") as audio_file:
            files = {"file": audio_file}
            response = requests.post(f"{BASE_URL}/recognise", files=files)
        # Accept either 200 or 404 as valid responses.
        self.assertIn(response.status_code, [200, 404],
                      f"Expected 200 or 404, got {response.status_code}")
        response_json = response.json()
        if response.status_code == 200:
            self.assertIn("track", response_json,
                          "Expected 'track' key in response, but got none")
            self.assertIn("title", response_json["track"],
                          "Expected 'title' in track data, but got none")

    def test_recognize_missing_file(self):
        """Test API behavior when no file is uploaded."""
        response = requests.post(f"{BASE_URL}/recognise")
        self.assertEqual(response.status_code, 400,
                         f"Expected 400, got {response.status_code}")
        self.assertEqual(response.json().get("error"), "No audio file provided")

    def test_recognize_invalid_audio(self):
        """Test recognition with an invalid file format."""
        with open("frag/fake_audio.wav", "rb") as fake_audio:
            files = {"file": fake_audio}
            response = requests.post(f"{BASE_URL}/recognise", files=files)
        # Optionally print details for debugging:
        print("Response Status Code:", response.status_code)
        print("Response JSON:", response.json())
        response_json = response.json()
        self.assertIn("error", response_json,
                      "Expected error in response, but got success")

if __name__ == '__main__':
    unittest.main()
