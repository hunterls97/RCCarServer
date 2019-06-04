import os
from flask import Flask
from flask import send_from_directory
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)
static_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'public')
#logger = logging.getLogger('logger')
#logger.setLevel(logging.ERROR)

@app.route('/')
def serve():
	return send_from_directory(static_dir, 'index.html')

@app.route('/<path:path>', methods=['GET'])
def serve_in_path(path):
	if not os.path.isfile(os.path.join(static_dir, path)):
		path = os.path.join(path, 'index.html')

	return send_from_directory(static_dir, path)

@socketio.on('connect')
def connection():
	print('connected!')

#global control commands
@socketio.on('sp')
def set_steer_power(data):
	socketio.emit('sp', data)

@socketio.on('dp')
def set_drive_power(data):
	socketio.emit('dp', data)

@socketio.on('a1')
def accelerate():
	socketio.emit('a1')

@socketio.on('tl1')
def turn_left():
	socketio.emit('tl1')

@socketio.on('r1')
def reverse():
	socketio.emit('r1')

@socketio.on('tr1')
def turn_right():
	socketio.emit('tr1')

@socketio.on('a0')
def stop_accelerate():
	socketio.emit('a0')

@socketio.on('tl0')
def stop_turn_left():
	socketio.emit('tl0')

@socketio.on('r0')
def stop_reverse():
	socketio.emit('r0')

@socketio.on('tr0')
def stop_turn_right():
	socketio.emit('tr0')


if __name__ == "__main__":
	socketio.run(app, log_output=False, host='192.168.2.13', port=27372)