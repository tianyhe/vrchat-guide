from audioRecorder import listenAndRecordDirect
from csvLogger import CSVLogger
import os
import threading
import time

# Delete existing recording if present
if os.path.exists("./speech/current_conversation.wav"):
    os.remove("./speech/current_conversation.wav")

# Create speech directory if it doesn't exist
os.makedirs("./speech", exist_ok=True)

CSV_LOGGER = CSVLogger()
FILENAME = "./speech/current_conversation.wav"

# Set recording duration in seconds
RECORDING_DURATION = 10

def stop_recording():
    time.sleep(RECORDING_DURATION)
    os._exit(0)

print(f"Testing microphone input for {RECORDING_DURATION} seconds...")
print("Speak into your microphone...")

# Start the timer thread
timer_thread = threading.Thread(target=stop_recording)
timer_thread.daemon = True
timer_thread.start()

# Start recording
listenAndRecordDirect(CSV_LOGGER, FILENAME)