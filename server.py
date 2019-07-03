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

eventlet.monkey_patch() #idk if this is even needed anymore lol

#setup server stuff
s = sio.Server(async_mode="threading")
app = Flask(__name__)
app.wsgi_app = sio.Middleware(s, app.wsgi_app)

socketio = SocketIO(app, async_mode="eventlet")
static_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'public')

#setup server routes, mostly for html contoller (for manual car control in emergency case)
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

#simple image processing class, each car w/ camera runs on separate thread
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

#namespace for the camera, creates an image pool for all the cars with cameras 
class CameraNameSpace(Namespace):
	def __init__(self, namespace):
		self.namespace = namespace
		self.imagePool = []

	def on_connect(self):
		if(args.camera):
			print('rpi camera connected')
			self.imagePool.append(ImageProcessor(self))
			pass
	
	#load camera queue, only really need between 8-10 fps
	def on_camera_data(self, data):
		if(args.camera and data):
			self.imagePool[0].load_queue(data) #temporary while only 1 camera, when more cameras then load queue for rc car that sent data

#namespace for all control messages (manual or from simulink etc)
class ControllerNameSpace(threading.Thread, Namespace):
	def __init__(self, namespace):
		super(ControllerNameSpace, self).__init__()
		self.namespace = namespace
		self.simukinkConnection = False
		self.terminate = False
		self.commandQueue = queue.Queue(5)
		self.buff = bytearray(8)
		self.command = io.BytesIO()
		
		#when simulink is running, need to process on two threads because of too many dumb issues with matlab,
		#essentially all incoming commands are processed and loaded in the run function, and then the commands
		#are broadcasted to the working cars in the executor function
		if(args.simulink):
			print("establishing simulink connection")
			self.executor = threading.Thread(target=self.execute)
			self.start()
			self.executor.start()

	#need to do it with python socket instead of socketio because of bug
	def run(self):
		with app.test_request_context():
			import socket
			import struct

			#create socket and connect to optitrack system
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect(("192.168.2.4", 18000))

			#get commands and load them into a queue, if queue is full then just pop first entry
			while not self.terminate:
				self.command.write(sock.recv(8))
				self.command.seek(0)

				if(self.commandQueue.full()):
					self.commandQueue.get()

				#matlab/quanser only sends little endian encoded doubles, but it also doesn't tell you that... fml
				c = int(struct.unpack_from("<d", bytearray(self.command.read()))[0])
				self.commandQueue.put(c)

				self.command.seek(0)
				self.command.truncate()

	#broadcast commands
	def execute(self):
		while not self.terminate:
			c = self.commandQueue.get(timeout=1)
			if(not c == -1):
				print(c)

			if(c == int(1)):
				socketio.emit('tr1', broadcast=True, namespace='/controller')

			if(c == int(0)):
				socketio.emit('tl1', broadcast=True, namespace='/controller')
				
			if(c == int(-1)):
				socketio.emit('tr0', broadcast=True, namespace='/controller')

			time.sleep(0.02)

	def on_connect(self):
		print('connected!')

		if(not self.simukinkConnection):
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
	#parser to determine wheteher or not to listen to car cameras or simulink model
	#typically one, the other, but not both
	parser = argparse.ArgumentParser(description="Server Arguments")
	parser.add_argument('--c', dest='camera', help='enable camera mode', action='store_true')
	parser.add_argument('--sc', dest='simulink', help='enable simulink connection', action='store_true')
	parser.set_defaults(camera=False)
	parser.set_defaults(simulink=False)

	args = parser.parse_args()

	socketio.on_namespace(ControllerNameSpace('/controller'))
	socketio.on_namespace(CameraNameSpace('/camera'))

	print('Starting Server')
	socketio.run(app, log_output=False, host='192.168.2.11', port=27372)

