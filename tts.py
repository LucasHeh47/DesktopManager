import aiohttp
import threading
import io
import simpleaudio as sa
import asyncio
from pydub import AudioSegment
from queue import Queue
import time

api_key = ""

CHUNK_SIZE = 1024
VOICE_ID = "YTPeFxVpy0d77hJ7p33S"

tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

headers = {
    "Accept": "application/json",
    "xi-api-key": api_key
}

class AudioQueue:
    def __init__(self):
        self.queue = Queue()
        self.lock = threading.Lock()
        self.playback_thread = threading.Thread(target=self.play_audio_queue)
        self.playback_thread.start()

    def add(self, audio_data):
        with self.lock:
            self.queue.put(audio_data)

    def play_audio_queue(self):
        while True:
            audio_data = self.queue.get()
            if audio_data is None:
                break
            self.play_audio_stream(audio_data)

    def play_audio_stream(self, audio_data):
        with io.BytesIO(audio_data) as audio_stream:
            # Convert MP3 data to raw PCM data
            audio_segment = AudioSegment.from_file(audio_stream, format="mp3")
            raw_data = audio_segment.raw_data
            num_channels = audio_segment.channels
            bytes_per_sample = audio_segment.sample_width
            sample_rate = audio_segment.frame_rate

            # Ensure buffer size is correct
            expected_buffer_size = len(raw_data)
            expected_size = num_channels * bytes_per_sample * (expected_buffer_size // (num_channels * bytes_per_sample))
            if expected_buffer_size != expected_size:
                raise ValueError("Buffer size is incorrect for the given audio parameters.")

            # Play the audio
            playback = sa.play_buffer(raw_data, num_channels=num_channels, bytes_per_sample=bytes_per_sample, sample_rate=sample_rate)
            while playback.is_playing():
                time.sleep(0.1)

audio_queue = AudioQueue()

async def speak(text: str):
    async with aiohttp.ClientSession() as session:
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.87,
                "similarity_boost": 1,
                "style": 0.6,
                "use_speaker_boost": False
            }
        }

        async with session.post(tts_url, headers=headers, json=data) as response:
            if response.ok:
                audio_data = b''
                while True:
                    chunk = await response.content.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    audio_data += chunk
                audio_queue.add(audio_data)
            else:
                print(await response.text())
