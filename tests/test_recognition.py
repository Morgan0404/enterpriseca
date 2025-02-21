import unittest
import requests
import base64
import os

# Base URL for the recognition service.
BASE_URL = "http://127.0.0.1:5002"

class TestRecognition(unittest.TestCase):

    def test_recognize_valid_audio(self):
        """Test recognizing a valid audio file and decode the full encoded string into answer.wav."""
        with open("frag/_Dont Look Back In Anger.wav", "rb") as audio_file:
            files = {"file": audio_file}
            # Use testmode=true to get the full encoded string (no truncation)
            response = requests.post(f"{BASE_URL}/recognise?testmode=true", files=files)
        
        # We expect a 200 response when the track is recognised and found.
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}")
        response_json = response.json()
        
        # Verify that required keys exist in the 'track' object.
        self.assertIn("track", response_json, "Expected 'track' key in response, but got none")
        track = response_json["track"]
        self.assertIn("encoded_file", track, "Expected 'encoded_file' in track data, but got none")
        
        full_encoded = track["encoded_file"]
        # Write the full encoded string to a file for verification.
        with open("full_encoded_output.txt", "w") as f:
            f.write(full_encoded)
        
        # Now decode the full Base64 string and write it to answer.wav.
        try:
            wav_data = base64.b64decode(full_encoded)
        except Exception as e:
            self.fail(f"Decoding failed: {e}")
        
        with open("answer.wav", "wb") as out_f:
            out_f.write(wav_data)
        
        # Check that the decoded data is non-empty.
        self.assertTrue(len(wav_data) > 0, "Decoded audio is empty")
        
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
        # Optionally print details for debugging.
        print("Response Status Code:", response.status_code)
        print("Response JSON:", response.json())
        response_json = response.json()
        self.assertIn("error", response_json,
                      "Expected error in response, but got success")

if __name__ == '__main__':
    unittest.main()
