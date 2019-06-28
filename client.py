import io
import sys
import time
import threading
import picamera
import socketio
import RPi.GPIO as GPIO

sio = socketio.Client(
	reconnection = True,
	reconnection_attempts = 10,
	reconnection_delay = 6
)
sio.connect('http://192.168.2.11:27372', transports=['websocket'], namespaces=['/controller', '/camera'])

def stop():
	GPIO.output(11, GPIO.LOW)
	GPIO.output(13, GPIO.LOW)
	GPIO.output(16, GPIO.LOW)
	GPIO.output(18, GPIO.LOW)

def turn(f):
	if f == -1:
		GPIO.output(11, GPIO.LOW)
		GPIO.output(13, GPIO.LOW)
	else:
		GPIO.output(11, GPIO.LOW if f == 1 else GPIO.HIGH)
		GPIO.output(13, GPIO.HIGH if f == 1 else GPIO.LOW)

def accel(f):
	if f == -1:
		GPIO.output(16, GPIO.LOW)
		GPIO.output(18, GPIO.LOW)
	else:
		GPIO.output(16, GPIO.LOW if f == 1 else GPIO.HIGH)
		GPIO.output(18, GPIO.HIGH if f == 1 else GPIO.LOW)

def setPWM0(p):
	pwm0.ChangeDutyCycle(p * 100)

def setPWM1(p):
	pwm1.ChangeDutyCycle(p * 100)

class ControllerNameSpace(socketio.ClientNamespace):
	def on_connect(self):
		print('connected to controller')
		pass

	#global control commands
	def on_sp(self, data):
		setPWM0(float(data.get('val', 1)))
		

	def on_dp(self, data):
		setPWM1(float(data.get('val', 1)))

	def on_a1(self, data):
		accel(1)

	def on_tl1(self, data):
		turn(0)

	def on_r1(self, data):
		accel(0)

	def on_tr1(self, data):
		turn(1)

	def on_a0(self, data):
		accel(-1)

	def on_tl0(self, data):
		turn(-1)

	def on_r0(self, data):
		accel(-1)

	def on_tr0(self, data):
		turn(-1)

class CameraNameSpace(socketio.ClientNamespace):
	def on_connect(self):
		print('connected to pi camera')
		
		while True:
			with output.condition:
				output.condition.wait()
				frame = output.frame

			self.emit('camera_data', frame)
			sio.sleep(0.125) #match camera frame rate

class StreamingOutput(object):
	def __init__(self):
		self.frame = None
		self.buffer = io.BytesIO()
		self.condition = threading.Condition()

	def write(self, buf):
		if buf.startswith(b'\xff\xd8'):
			self.buffer.truncate()

			with self.condition:
				self.frame = self.buffer.getvalue()
				self.condition.notify_all()

			self.buffer.seek(0)

		return self.buffer.write(buf);

if __name__ == '__main__':
	cameraMode = False

	if len(sys.argv) > 1:
		if int(sys.argv[1]) == 1:
			cameraMode = True

	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(11, GPIO.OUT)
	GPIO.setup(12, GPIO.OUT)
	GPIO.setup(13, GPIO.OUT)
	GPIO.setup(16, GPIO.OUT)
	GPIO.setup(18, GPIO.OUT)
	GPIO.setup(33, GPIO.OUT)

	pwm0 = GPIO.PWM(12, 1000)
	pwm1 = GPIO.PWM(33, 1000)
	pwm0.start(20)
	pwm1.start(20)

	output = StreamingOutput()
	sio.register_namespace(ControllerNameSpace('/controller'))

	if cameraMode:
		sio.register_namespace(CameraNameSpace('/camera'))
		with picamera.PiCamera() as camera:
		  camera.resolution = (640, 480)
		  camera.framerate = 8

		  start = time.time()
		  camera.start_recording(output, format='mjpeg', quality=10)

		  while True:
		  	camera.wait_recording(1)