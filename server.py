import os
import io
import cv2
import time
import queue
import threading
import socketio as sio
import numpy as np
from PIL import Image
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
		print('rpi camera connected')
		#self.imagePool.append(ImageProcessor(self))
		pass
		
	#def on_camera_data(self, data):
		#if(data):
			#self.imagePool[0].load_queue(data) #temporary while only 1 camera, when more cameras then load queue for rc car that sent data

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

class SimulinkConnector(threading.Thread):
	def __init__(self, host, port):
		self.host = host
		self.port = port

		threading.Thread.__init__(self)
		self.daemon = True
		self.start()

	#need t do it with python socket instead of socketio because of socketio bug
	def run(self):
		import socket
		import struct

		sock = socket.create_connection((self.host, self.port))

		#works
		while True:
			data = sock.recv(16)

			if data:
				while True:
					try:
						c = int(struct.unpack_from("<d", data)[0])
						print(c)

						if(c == 1):
							emit('tr1', broadcast=True)
						elif(c == 0):
							emit('tll', broadcast=True)
						else:
							emit('tl0', broadcast=True) #tl0 is same as tr0

					except struct.error:
						break

			time.sleep(2) #same clock as server

		# self.sioc = sio.Client(
		# 	reconnection = True,
		# 	reconnection_attempts = 10,
		# 	reconnection_delay = 6
		# )

		# @self.sioc.on("connect")
		# def on_connect(self):
		# 	print('connected to simulink')

		# 	#on connect, set drive power to half and begin acceleration
		# 	emit('dp', {
		# 		'val': 0.5
		# 	})

		# 	emit('a1')

		# @self.sioc.on("data")
		# def on_data(self, sid, data):
		# 	d = []
		# 	if(data):
		# 		print(data)
		# 		while 1:
		# 			try:
		# 				d.append(struct.unpack_from("<Q", data)[0])
		# 			except struct.error:
		# 				print(d)
		# 				break

		# 		#send turn command
		# 		if(d[0] == 1):
		# 			emit('tl1')
		# 		elif(d[0] == 0):
		# 			emit('tl0')

sc = SimulinkConnector("192.168.2.4", 18000)
socketio.on_namespace(ControllerNameSpace('/controller'))
socketio.on_namespace(CameraNameSpace('/camera'))

if __name__ == "__main__":
	print('Starting Server')
	socketio.run(app, log_output=False, host='192.168.2.11', port=27372)