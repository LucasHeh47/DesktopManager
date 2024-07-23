import threading
import pyaudio
import math
import struct
import wave
import time
import os
from evdev import InputDevice, categorize, ecodes, KeyEvent

# Set the input device path
input_device_path = '/dev/input/event16'

# Check if the input device is accessible
if not os.access(input_device_path, os.R_OK):
    raise PermissionError(f"Permission denied: '{input_device_path}'")

keyboard = InputDevice(input_device_path)
keys_pressed = {}
R_KEY = ecodes.KEY_R  # or KEY_RIGHTMETA depending on your keyboard
CTRL_KEY = ecodes.KEY_LEFTCTRL  # or KEY_RIGHTCTRL
WIN_KEY = ecodes.KEY_LEFTMETA
Threshold = 10
SHORT_NORMALIZE = (1.0 / 32768.0)
chunk = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
swidth = 2
TIMEOUT_LENGTH = 1.5

def check_keys():
    return keys_pressed.get(WIN_KEY, False) and keys_pressed.get(CTRL_KEY, False) and keys_pressed.get(R_KEY, False)

class Recorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=chunk)
        self.recording_thread = None
        self.keep_recording = False

    def rms(self, frame):
        count = len(frame) / swidth
        shorts = struct.unpack("%dh" % count, frame)
        sum_squares = sum(n * SHORT_NORMALIZE * n * SHORT_NORMALIZE for n in shorts)
        return math.sqrt(sum_squares / count) * 1000

    def record_loop(self):
        print("Recording...")
        rec = []
        while self.keep_recording:
            data = self.stream.read(chunk, exception_on_overflow=False)
            rec.append(data)
        self.write(b''.join(rec))
        print("Recorded")

    def write(self, recording):
        filename = "message.wav"
        print(f"Writing to file {filename}, size {len(recording)} bytes")
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(recording)

    def start_recording(self):
        self.keep_recording = True
        self.recording_thread = threading.Thread(target=self.record_loop)
        self.recording_thread.start()

    def stop_recording(self):
        self.keep_recording = False
        if self.recording_thread:
            self.recording_thread.join()

    def monitor_keys(self):
        print("Listening for keys...")
        while True:
            event = keyboard.read_one()
            if event and event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                # Ignore auto-repeat events
                if key_event.keystate == KeyEvent.key_hold:
                    continue  # Skip the loop iteration if it's a repeat event

                keys_pressed[key_event.scancode] = (key_event.keystate == KeyEvent.key_down)

                # Debug output to understand what's happening
                state = 'pressed' if key_event.keystate == KeyEvent.key_down else 'released'
                print(f"Key {key_event.keycode} {state}")

                if check_keys() and not self.keep_recording:
                    print("Starting recording...")
                    self.start_recording()
                elif not check_keys() and self.keep_recording:
                    print("Stopping recording...")
                    self.stop_recording()

            # Add a slight delay to reduce CPU usage
            time.sleep(0.01)

    def close(self):
        self.stream.close()
        self.p.terminate()

# Create an instance of Recorder
recorder = Recorder()

try:
    # Start monitoring keys
    recorder.monitor_keys()
except KeyboardInterrupt:
    # Handle exit gracefully
    print("Exiting...")
    recorder.close()
