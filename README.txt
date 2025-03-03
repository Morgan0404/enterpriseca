README.txt
==========

This file provides instructions to run and test the Shamzam audio recognition system, implemented as three Python microservices for ECM3408 Enterprise Computing coursework.

Prerequisites
-------------
- Anaconda installed (Windows/Linux/macOS compatible).
- Python dependencies: `flask`, `requests`, `base64` (install via `pip install flask requests`).
- Directory: `EnterpriseCA/` containing `services/` and `tests/` subdirectories.
- Audio files in `wavs/` (e.g., `Blinding Lights.wav`, `~Don't Look Back In Anger.wav`, etc.).
- Environment variable `KEY` set to a valid AudD.io API key (e.g., `export KEY=your_audd_io_key` on Unix, `set KEY=your_audd_io_key` on Windows).

Files
-----
- `services/audio_recognition.py`: Main API for audio fragment recognition (port 5002).
    Serves as the user-facing gateway. It accepts an audio fragment, forwards it to the Aud Service for recognition,
    and then integrates the external metadata with locally stored catalogue data

- `services/aud_service.py`: Audio recognition via AudD.io (port 5003).Acts as an intermediary with the external AudD.io API.
    It receives an audio file and returns recognition metadata (e.g., title, artist, album, release date).

- `services/music_catalogue.py`: Music track catalogue management (port 5001).Manages the track database. This service enables
    administrators to add new tracks (S1), remove tracks (S2), and list all tracks (S3). This separation
    adheres to the Single Responsibility Principle and allows independent scaling 
  
- `tests/test_all.py`: Comprehensive test suite for all microservices.

Running the Microservices
-------------------------
1. Open separate Anaconda Command Prompts (or terminals).
2. Navigate to the project directory:
3. Start each microservice in its own prompt:
- Music Catalogue (port 5001): python services/music_catalogue.py
- Audio Recognition (port 5002): python services/audio_recognition.py
- Aud Service (port 5003): python services/aud_service.py (requires KEY env var found in Key.txt)


Testing the System
------------------
1. Ensure all three microservices are running (see above).
2. In a new Anaconda Command Prompt, navigate to `EnterpriseCA/`:
3. Run the command "python -m unittest tests.test_all"

Notes
-----
- Ensure ports 5001, 5002, and 5003 are free before starting services.
- WAV files in `wavs/` must be 16 kHz mono for recognition tests (e.g., `~Davos.wav` for unrecognized audio).
- Debug mode is enabled in all services; errors will appear in the console if issues arise.
- Tests assume a clean catalogue state (reset via `db_teardown` before each test).
- When you open a compressed file it may have the tendency to change ' to _ hence please look into wavs to ensure they are renamed back to ', likewise sometimes ~ can change to _

------
ECM3408 Shamzam Coursework Submission