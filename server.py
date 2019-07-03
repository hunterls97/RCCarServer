import os
import io
import cv2
import time
import argparse
import eventlet
import queue
import threading
import socketio as sio
import numpy as np
from PIL import Image
from flask import Flask
from flask import send_from_directory
from flask_socketio import SocketIO, Namespace, emit

eventlet.monkey_patch()

s = sio.Server(async_mode="threading")
app = Flask(__name__)
app.wsgi_app = sio.Middleware(s, app.wsgi_app)

socketio = SocketIO(app, async_mode="eventlet")
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

class ImageProcessor(threading.Thread):
	def __init__(self, owner):
		super(ImageProcessor, self).__init__()
		self.owner = owner
		self.terminate = False
		self.isRendering = False
		self.frameQueue = queue.Queue(5)
		self.frame = io.BytesIO()
		self.start()

	def load_queue(self, data):
		if(self.frameQueue.full()):
			self.frameQueue.get()

		self.frameQueue.put(data)

	def run(self):
		while not self.terminate:
			try:
				self.frame.write(self.frameQueue.get(timeout=1))
			except queue.Empty:
				pass
			else:
				if not self.isRendering:
					self.isRendering = True
					self.frame.seek(0)

					#img processing will be here
					img = cv2.imdecode(np.asarray(bytearray(self.frame.read()), np.uint8), 1)

					self.frame.seek(0)
					self.frame.truncate()

					cv2.imshow('img', img)
					cv2.waitKey(1)
					self.isRendering = False


class CameraNameSpace(Namespace):
	def __init__(self, namespace):
		self.namespace = namespace
		self.imagePool = []

	def on_connect(self):
		if(args.camera):
			print('rpi camera connected')
			self.imagePool.append(ImageProcessor(self))
			pass
		
	def on_camera_data(self, data):
		if(args.camera and data):
			self.imagePool[0].load_queue(data) #temporary while only 1 camera, when more cameras then load queue for rc car that sent data

class ControllerNameSpace(threading.Thread, Namespace):
	def __init__(self, namespace):
		super(ControllerNameSpace, self).__init__()
		self.namespace = namespace
		self.simukinkConnection = False
		self.terminate = False
		self.commandQueue = queue.Queue(5)
		self.buff = bytearray(8)
		self.command = io.BytesIO()
		
		if(args.simulink):
			print("establishing simulink connection")
			self.executor = threading.Thread(target=self.execute)
			self.start()
			self.executor.start()
		#threading.Thread.__init__(self)
		#self.daemon = True

	def tr1(self):
		socketio.emit('tr1', broadcast=True, namespace='/controller')

	def tl1(self):
		socketio.emit('tll', broadcast=True, namespace='/controller')

	def tl0(self):
		socketio.emit('tl0', broadcast=True, namespace='/controller') #tl0 is same as tr0

	#need t do it with python socket instead of socketio because of socketio bug
	def run(self):
		with app.test_request_context():
			import socket
			import struct

			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(("192.168.2.4", 18000))
			#sock = socket.create_connection(("192.168.2.4", 18000))

			#works
			while not self.terminate:
				self.command.write(sock.recv(8))
				self.command.seek(0)

				if(self.commandQueue.full()):
					self.commandQueue.get()

				c = int(struct.unpack_from("<d", bytearray(self.command.read()))[0])
				self.commandQueue.put(c)

				self.command.seek(0)
				self.command.truncate()

	def execute(self):
		while not self.terminate:
			c = self.commandQueue.get(timeout=1)
			if(not c == -1):
				print(c)

			if(c == int(1)):
				socketio.emit('tr1', broadcast=True, namespace='/controller')
				#self.tr1()

			if(c == int(0)):
				socketio.emit('tl1', broadcast=True, namespace='/controller')
				#self.tl1()
				
			if(c == int(-1)):
				socketio.emit('tr0', broadcast=True, namespace='/controller')
				#self.tl0()

			time.sleep(0.02)

	def on_connect(self):
		print('connected!')

		if(not self.simukinkConnection):
			#sc = SimulinkConnector("192.168.2.4", 18000)
			self.simukinkConnection = True
			socketio.start_background_task(target=self.run)

		pass

	#global control commands
	def on_sp(self, data):
		emit('sp', data, broadcast=True)

	def on_dp(self, data):
		emit('dp', data, broadcast=True)

	def on_a1(self):
		emit('a1', broadcast=True)

	def on_tl1(self):
		emit('tl1', broadcast=True)
		#emit('tl1', broadcast=True)

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

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Server Arguments")
	parser.add_argument('--c', dest='camera', help='enable camera mode', action='store_true')
	parser.add_argument('--sc', dest='simulink', help='enable simulink connection', action='store_true')
	parser.set_defaults(camera=False)
	parser.set_defaults(simulink=False)

	args = parser.parse_args()

	socketio.on_namespace(ControllerNameSpace('/controller'))
	socketio.on_namespace(CameraNameSpace('/camera'))

	print('Starting Server')
	#eventlet.wsgi.server(eventlet.listen(("192.168.2.11", 27372)), app)
	#app.run(threaded=True, host='192.168.2.11', port=27372)
	socketio.run(app, log_output=False, host='192.168.2.11', port=27372)

	# sc.start()
	# contns.start()

	# try:
	# 	while True:
	# 		time.sleep(100)
	# except (KeyboardInterrupt, SystemExit):
	# 	sc.join()
	# 	contns.join()