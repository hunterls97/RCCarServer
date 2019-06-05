import os
import io
from flask import Flask
from flask import send_from_directory
from flask_socketio import SocketIO, Namespace, emit

app = Flask(__name__)
socketio = SocketIO(app)
static_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'public')

@app.route('/')
def serve():
	return send_from_directory(static_dir, 'index.html')

@app.route('/camera')
def view_camera():
	return send_from_directory(static_dir, 'camera.html')


@app.route('/<path:path>', methods=['GET'])
def serve_in_path(path):
	if not os.path.isfile(os.path.join(static_dir, path)):
		path = os.path.join(path, 'index.html')

	return send_from_directory(static_dir, path)

class ControllerNameSpace(Namespace):
	def on_connect(self):
		print('connected!')
		pass

	#global control commands
	def on_sp(self, data):
		emit('sp', data, broadcast=True)

	def on_dp(self, data):
		emit('dp', data, broadcast=True)

	def on_a1(self):
		print('accel')
		emit('a1', broadcast=True)

	def on_tl1(self):
		emit('tl1', broadcast=True)

	def on_r1(self):
		emit('r1', broadcast=True)

	def on_tr1(self):
		emit('tr1', broadcast=True)

	def on_a0(self):
		emit('a0', broadcast=True)

	def on_tl0(self):
		emit('tl0', broadcast=True)

	def on_r0(self):
		emit('r0', broadcast=True)

	def on_tr0(self):
		emit('tr0', broadcast=True)

socketio.on_namespace(ControllerNameSpace('/controller'))
if __name__ == "__main__":
	socketio.run(app, log_output=False, host='192.168.2.13', port=27372)