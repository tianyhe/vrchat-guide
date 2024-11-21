
from openai import OpenAI
import os
from dotenv import load_dotenv
import threading
import sounddevice
import soundfile
from pydub import AudioSegment

from . import audio_device

event = threading.Event()


load_dotenv()
API_KEY = os.environ.get("API_KEY")
client = OpenAI()
CURRENT_FRAME = 0

response = client.audio.speech.create(
    model="tts-1",
    voice="nova",
    input="Hello world! This is a streaming test.",
    response_format="mp3",
)
# Global lock for synchronizing audio playback
playback_lock = threading.Lock()
# Global variable to keep track of the current frame position
CURRENT_FRAME = 0

def read_audio_file(filepath: str, output_device_index: int):
    global CURRENT_FRAME

    # Acquire the lock before starting playback
    playback_lock.acquire()

    def callback(data_out, frames, _, status):
        global CURRENT_FRAME
        if status:
            print("status: ", status)
        chunk_size = min(len(data) - CURRENT_FRAME, frames)
        data_out[:chunk_size] = data[CURRENT_FRAME : CURRENT_FRAME + chunk_size]
        if chunk_size < frames:
            data_out[chunk_size:] = 0
            CURRENT_FRAME = 0
            raise sounddevice.CallbackStop()
        CURRENT_FRAME += chunk_size

    def stream_thread():
        with stream:
            event.wait()  # Wait until playback is finished
        event.clear()
        playback_lock.release()  # Release the lock after playback

    try:
        data, samplerate = soundfile.read(filepath, always_2d=True)
    except Exception as e:
        print("Error reading audio file:", e)
        playback_lock.release()
        return

    event = threading.Event()

    try:
        stream = sounddevice.OutputStream(
            samplerate=samplerate,
            device=output_device_index,
            channels=audio_device.get_info_from_id(output_device_index).max_output_channels,
            callback=callback,
            finished_callback=event.set,
        )
    except sounddevice.PortAudioError as e:
        print("Error creating audio stream in openaiTTS sounddevice port:", e, "for device index", output_device_index)
        playback_lock.release()
        return

    thread = threading.Thread(target=stream_thread)
    thread.start()


def generateAudio(text, device_index):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        response_format="mp3",
    )
    response.stream_to_file("speech/output.mp3")
    AudioSegment.from_file("speech/output.mp3").export("speech/example.ogg", format="ogg")
    read_audio_file("speech/example.ogg", device_index)



# response.stream_to_file("output.mp3")
# AudioSegment.from_file("output.mp3").export("example.ogg", format="ogg")

