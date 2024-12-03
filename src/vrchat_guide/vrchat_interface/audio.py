import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import io
from pathlib import Path
from openai import AsyncOpenAI
from loguru import logger
import asyncio
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class AudioDeviceManager:
    """Manages audio devices and virtual microphone settings."""

    def __init__(self):
        self.devices = sd.query_devices()
        # self.list_devices()  # Debug output once
        self.virtual_mic_channel = self._get_virtual_mic_channel()

    def _get_virtual_mic_channel(self) -> int:
        """Find virtual audio cable device and return its channel number."""
        for i, device in enumerate(self.devices):
            name = device.get("name", "")
            if isinstance(name, str) and "CABLE Input" in name:  # Windows VB-Cable name
                return i
        return sd.default.device[1]  # Fallback to default output

    def get_virtual_mic_channel(self) -> int:
        return self.virtual_mic_channel

    def list_devices(self):
        """List all audio devices for debugging."""
        logger.info("\n=== Audio Devices ===")
        if self.devices is not None:
            for i, device in enumerate(self.devices):
                logger.info(f"[{i}] {device.get('name', 'Unknown Device')}")
        else:
            logger.error("No audio devices found!")


class AudioCues:
    def __init__(self):
        self.sample_rate = 44100

    def generate_beep(self, frequency=440, duration=0.2):
        """Generate a beep sound."""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        beep = np.sin(2 * np.pi * frequency * t)
        return beep

    async def play_start_cue(self):
        """Rising beep for start."""
        beep = self.generate_beep(440, 0.2)
        sd.play(beep, self.sample_rate)
        sd.wait()

    async def play_end_cue(self):
        """Falling beep for end."""
        beep = self.generate_beep(330, 0.2)
        sd.play(beep, self.sample_rate)
        sd.wait()


class AudioService:
    def __init__(self):
        self.is_speaking = False
        self.is_listening = False
        self.audio_cues = AudioCues()
        self.listen_duration = 8.0
        self.recording_buffer = []  # Add buffer for recording

    async def start_listening(self):
        if self.is_speaking:
            return

        self.is_listening = True
        self.recording_buffer.clear()  # Clear previous recording
        await self.audio_cues.play_start_cue()

        # Start actual recording
        self.stream = sd.InputStream(
            channels=1, samplerate=44100, callback=self._audio_callback
        )
        self.stream.start()

    def _audio_callback(self, indata, frames, time, status):
        if self.is_listening:
            self.recording_buffer.append(indata.copy())

    async def stop_listening(self):
        self.is_listening = False
        if hasattr(self, "stream"):
            self.stream.stop()
            self.stream.close()


class TTSService:
    """Text-to-Speech service using OpenAI."""

    def __init__(self, device: str = None):  # device parameter optional
        self.device = device
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.sample_rate = 24000  # OpenAI TTS sample rate
        self.is_speaking = False

    async def speak(self, text: str, channel: int):
        """Convert text to speech and play it."""
        try:
            self.is_speaking = True
            audio_data = await self._generate_audio(text)
            await self._play_audio(audio_data, channel)
        finally:
            self.is_speaking = False
            # Signal that agent finished speaking

    async def _generate_audio(self, text: str) -> np.ndarray:
        """Generate audio using OpenAI TTS."""
        response = await self.client.audio.speech.create(
            model="tts-1", voice="alloy", input=text
        )
        # Decode audio properly using soundfile
        audio_data, _ = sf.read(io.BytesIO(response.content))
        return audio_data

    async def _play_audio(self, audio_data: np.ndarray, channel: int):
        """Play audio through specified channel."""
        sd.play(audio_data, self.sample_rate, device=channel)
        await asyncio.sleep(len(audio_data) / self.sample_rate)
        sd.wait()


class STTService:
    """Speech-to-Text service using OpenAI Whisper."""

    def __init__(self, device: str):
        self.device = device
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.silence_threshold = -40
        self.min_speech_duration = 0.1  # Minimum 100ms of speech
        self.speech_timeout = 2  # 500ms of silence to stop

    async def listen_and_record(
        self, save_path: Path, max_duration: float = 10.0
    ) -> Path:
        try:
            chunks = []
            silence_duration = 0
            speech_duration = 0
            recording_started = False
            max_samples = int(max_duration * self.sample_rate)
            total_samples = 0

            stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=self.chunk_size,
            )

            with stream:
                while total_samples < max_samples:
                    audio_chunk, _ = stream.read(self.chunk_size)

                    # Calculate audio level in dB
                    audio_level = 20 * np.log10(np.abs(audio_chunk).mean() + 1e-10)

                    # Debug logging
                    logger.debug(f"Audio level: {audio_level:.2f} dB")

                    # Start recording when speech detected
                    if audio_level > self.silence_threshold:
                        if not recording_started:
                            logger.debug("Speech detected, starting recording")
                        recording_started = True
                        silence_duration = 0
                        speech_duration += self.chunk_size / self.sample_rate
                        chunks.append(audio_chunk)
                        total_samples += self.chunk_size
                    elif recording_started:
                        silence_duration += self.chunk_size / self.sample_rate
                        chunks.append(
                            audio_chunk
                        )  # Keep some silence for natural speech
                        total_samples += self.chunk_size

                        # Stop after sufficient silence and minimum speech
                        if (
                            silence_duration >= self.speech_timeout
                            and speech_duration >= self.min_speech_duration
                        ):
                            logger.debug(
                                f"Stopping recording: {speech_duration:.2f}s speech, {silence_duration:.2f}s silence"
                            )
                            break

            # Save if we captured enough speech
            if recording_started and speech_duration >= self.min_speech_duration:
                recording = np.concatenate(chunks)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                sf.write(save_path, recording, self.sample_rate)
                logger.info(f"Saved recording: {speech_duration:.2f}s speech")
                return save_path

            logger.warning("No valid speech detected")
            return None

        except Exception as e:
            logger.error(f"Recording error: {e}")
            raise

    async def transcribe(self, audio_path: Path) -> Optional[str]:
        """Transcribe audio file using OpenAI Whisper."""
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file
                )
            return transcript.text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
