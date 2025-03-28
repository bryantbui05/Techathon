import pyaudio
import wave
import time
import requests
from gpiozero import Button
import ai_caller
from gtts import gTTS
import os

# Constants for audio recording
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono audio
BITRATE = 44100  # Audio bitrate (44.1kHz)
CHUNK_SIZE = 512  # Chunk size for audio reading
WAVE_OUTPUT_FILENAME = "myrecording.wav"
base_url = "https://api.assemblyai.com/v2"
headers = {"authorization": "22561d5247224eb2a02afabe6a1b4478"}  # Replace with your AssemblyAI API key

# Initialize audio and button
audio = pyaudio.PyAudio()
button = Button(17)  # Assuming button is connected to GPIO 17

# Initialize empty list to store frames
recording_frames = []

# Function to start recording
def start_recording():
    print("Recording started...")
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=BITRATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    global recording_frames
    recording_frames = []  # Clear previous frames if any
    while button.is_pressed:  # Continue recording while button is pressed
        data = stream.read(CHUNK_SIZE)
        recording_frames.append(data)
    stream.stop_stream()
    stream.close()

# Function to save the recorded audio to a .wav file
def save_recording():
    print("Saving recording...")
    try:
        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(BITRATE)
        waveFile.writeframes(b''.join(recording_frames))
        waveFile.close()
        print(f"Recording saved as {WAVE_OUTPUT_FILENAME}")
    except Exception as e:
        print(f"Error saving recording: {e}")
        return False
    return True

# Function to send audio to AssemblyAI for transcription
def transcribe_audio():
    # Upload the file to AssemblyAI
    with open(WAVE_OUTPUT_FILENAME, "rb") as f:
        response = requests.post(base_url + "/upload", headers=headers, data=f)

    if response.status_code != 200:
        print(f"Error: {response.status_code}, Response: {response.text}")
        response.raise_for_status()

    upload_json = response.json()
    upload_url = upload_json["upload_url"]
    
    # Request transcription
    data = {
        "audio_url": upload_url,
        "speaker_labels": True  # Enable speaker segmentation
    }
    response = requests.post(base_url + "/transcript", headers=headers, json=data)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, Response: {response.text}")
        response.raise_for_status()

    # Get transcript ID from the response
    transcript_json = response.json()
    transcript_id = transcript_json["id"]

    # Polling endpoint to check transcription status
    polling_endpoint = f"{base_url}/transcript/{transcript_id}"

    # Poll until the transcription is completed
    while True:
        transcript = requests.get(polling_endpoint, headers=headers).json()
        
        if transcript["status"] == "completed":
            # print(f"\n{transcript['text']}")
            response = ai_caller.get_ai_response(transcript['text'])
            response = response[len("AI Response:"):]
            print('\n' + response)
            tts = gTTS(response, lang="en")
            tts.save("output.mp3")
            os.system("mpg321 output.mp3")
            break

        elif transcript["status"] == "error":
            raise RuntimeError(f"Transcription failed: {transcript['error']}")

        else:
            print("Transcription in progress...")
            time.sleep(3)  # Wait before checking again

# Main loop to handle button press and release
try:

    while True:
        if button.is_pressed:
            if not recording_frames:  # Start recording only once on press
                start_recording()

        else:
            if recording_frames:  # Stop and save recording when button is released
                if save_recording():
                    transcribe_audio()  # Send the recording for transcription

                else:
                    print("Error: Recording was not saved properly.")
                recording_frames = []  # Reset frames after saving and processing
            time.sleep(0.1)  # Check every 100ms for button state

except KeyboardInterrupt:
    print("\nProgram interrupted. Exiting...")
    audio.terminate()
