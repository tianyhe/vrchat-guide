import io
import json
import time
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment, silence
import pyaudio
from csvLogger import CSVLogger, LogElements
import os
import random
import fillerWords
import VRC_OSCLib
from TTS import openaiTTS
import argparse
from pythonosc import udp_client
import threading
import time
from TTS import audio_device

INPUT_DEVICE_INDEX = audio_device.get_vbcable_devices_info().stereo_mix.id # Stereo Mix



TEMP_FILE = "speech_check.wav"
MODEL_PATH = "./vosk-model/vosk-model-small-en-us-0.15"
AUDIO_CSV_LOGGER = ""
# VRC client
parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="127.0.0.1",
                    help="The ip of the OSC server")
parser.add_argument("--port", type=int, default=9000,
                    help="The port the OSC server is listening on")
parser.add_argument("--use_cable_d", action="store_true",
                    help="Use CABLE-D as the input device")

args = parser.parse_args()
    
if args.use_cable_d:
    INPUT_DEVICE_INDEX = audio_device.get_vbcable_devices_info().cable_d_output.id # CABLE-D Output
    print("Using CABLE-D as the input device", INPUT_DEVICE_INDEX)

VRCclient = udp_client.SimpleUDPClient(args.ip, args.port)

def fillerShort():

    selected_filler_key = random.choice(list(fillerWords.fillersA.keys()))
    threading.Thread(target=VRC_OSCLib.actionChatbox,
                     args=(VRCclient, fillerWords.fillersA[selected_filler_key],)).start()
    # VRC_OSCLib.actionChatbox(VRCclient, fillerWords.fillers[selected_filler_key])
    openaiTTS.read_audio_file("TTS/fillerWord/" + selected_filler_key + ".ogg", audio_device.get_vbcable_devices_info().cable_c_input.id)


# print(listenAndRecord("text1.wav"))
def recordAudioToByteStream(silenceThreshold=-40, maxSilenceLength=1):

    fs = 16000  # Sample rate
    CHUNK_SIZE = int(fs * 0.5)  # Record in chunks of 0.5 seconds

    audio_chunks = []
    silence_duration = 0
    recording_started = False
    p = pyaudio.PyAudio()

    # Open stream
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=fs,
                    input=True,
                    input_device_index=INPUT_DEVICE_INDEX,
                    frames_per_buffer=CHUNK_SIZE)

    print("Recording started... Speak something...")
    # fillerShort()
    while True:
        audio_chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)

        # Convert byte data to AudioSegment for silence detection
        segment = AudioSegment.from_raw(io.BytesIO(audio_chunk), sample_width=2, frame_rate=fs, channels=1)

        # current_time = time.time()
        #
        # # Calculate the elapsed time by subtracting the start time from the current time
        # elapsed_time = current_time - start_time
        #
        # # Check if 3 seconds have passed
        # if elapsed_time >= 3 and play is True:
        #     fillerShort()
        #     play = False

        # Check for non-silence to start recording
        if segment.dBFS > silenceThreshold:
            recording_started = True

        if recording_started:
            audio_chunks.append(audio_chunk)
            # Check for silence to stop recording
            if segment.dBFS < silenceThreshold:
                silence_duration += CHUNK_SIZE / fs
                if silence_duration >= maxSilenceLength:
                    print("Silence detected, stopping recording.")
                    fillerShort()
                    break
            else:
                silence_duration = 0

    # Combine audio chunks and return as byte stream
    audio_data = b''.join(audio_chunks)
    byte_stream = io.BytesIO(audio_data)
    return byte_stream


def convertAndCheckAudio(byte_stream):
    print("inside convertAndCheckAudio")
    # Convert audio to the desired format in memory
    audio_data = AudioSegment.from_raw(byte_stream, sample_width=2, frame_rate=16000, channels=1)
    normalized_audio_data = audio_data.normalize()
    converted_stream = io.BytesIO()

    start = time.perf_counter()
    normalized_audio_data.export(converted_stream, format="wav")
    end = time.perf_counter()
    normalize_time = round(end - start, 2)
    AUDIO_CSV_LOGGER.set_enum(LogElements.TIME_FOR_VOICE_NORMALIZATION, normalize_time)

    converted_stream.seek(0)

    # Check if the converted audio contains human speech
    return isHumanSpeechByte(converted_stream)


def isHumanSpeechByte(byte_stream):
    global AUDIO_CSV_LOGGER
    global transcribeText
    start = time.perf_counter()

    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, 16000)
    end = time.perf_counter()
    detect_time = round(end - start, 2)
    AUDIO_CSV_LOGGER.set_enum(
        LogElements.TIME_FOR_HUMAN_SPEECH_RECOGNITION, detect_time
    )

    start = time.perf_counter()
    # byte_stream.seek(0)
    while True:
        data = byte_stream.read(8000)  # Read in chunks of 4000 bytes
        if len(data) == 0:
            break  # Break the loop if no more data is available
        rec.AcceptWaveform(data)

    result = json.loads(rec.FinalResult())
    if len(result.get("text", "")) > 0:
        transcribeText = result.get("text", "")
        end = time.perf_counter()
        detect_time = round(end - start, 2)
        AUDIO_CSV_LOGGER.set_enum(
            LogElements.TIME_AUDIO_TO_TEXT, detect_time
        )
        # fillerShort()
        return True
    else:
        return False


def listenAndRecordDirect(CSV_LOGGER, audio_file_name):
    print("inside listenAndRecordDirect")
    global AUDIO_CSV_LOGGER
    global play
    AUDIO_CSV_LOGGER = CSV_LOGGER
    start_time = time.time()
    while True:
        start = time.perf_counter()
        audio_byte_stream = recordAudioToByteStream()
        end = time.perf_counter()
        record_time = round(end - start, 2)
        AUDIO_CSV_LOGGER.set_enum(LogElements.TIME_FOR_AUDIO_RECORD, record_time)

        if not convertAndCheckAudio(audio_byte_stream):
            print("Nothing recorded, speak again!")
            continue
            # Saving the audio data to a file

            break

        current_time = time.time()

        # Calculate the elapsed time by subtracting the start time from the current time
        elapsed_time = current_time - start_time

        # Check if 3 seconds have passed

        with open(audio_file_name, "wb") as f:
            audio_byte_stream.seek(0)
            raw_audio_data = AudioSegment.from_raw(audio_byte_stream, sample_width=2, frame_rate=16000, channels=1)
            raw_audio_data.export(audio_file_name, format="wav")

        break
    return


def deleteAudioFile(fileName):
    try:
        os.remove(fileName)
    except:
        return
