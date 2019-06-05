import io
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
sio.connect('http://192.168.2.13:27372', namespaces=['/controller', '/camera'])

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
	print('accelerating')
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
		print(data.get('val'))
		setPWM0(float(data.get('val', 1)))
		

	def on_dp(self, data):
		print(data.get('val'))
		setPWM1(float(data.get('val', 1)))

	def on_a1(self, data):
		print('accel')
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
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(11, GPIO.OUT)
	GPIO.setup(12, GPIO.OUT)
	GPIO.setup(13, GPIO.OUT)
	GPIO.setup(16, GPIO.OUT)
	GPIO.setup(18, GPIO.OUT)
	GPIO.setup(33, GPIO.OUT)

	pwm0 = GPIO.PWM(12, 1000)
	pwm1 = GPIO.PWM(33, 1000)
	pwm0.start(70)
	pwm1.start(70)

	output = StreamingOutput()
	sio.register_namespace(ControllerNameSpace('/controller'))
	sio.register_namespace(CameraNameSpace('/camera'))

	with picamera.PiCamera() as camera:
	  camera.resolution = (640, 480)
	  camera.framerate = 10

	  start = time.time()
	  stream = io.BytesIO()
	  try:
	    for foo in camera.capture_continuous(output, 'jpeg'):
	      stream.seek(0)

	      if time.time() - start > 30:
	          break
	      # Reset the stream for the next capture
	      stream.seek(0)
	      stream.truncate()
	  except Exception as e:
	  	print('camera fail')
	  	print(e)

	# 
	# with picamera.PiCamera(resolution='640x480', framerate=10) as camera:
	# 	output = StreamingOutput()
	# 	

	# 	start = time.time()
	# 	camera.start_recording(output, format='mjpeg')

	# 	#stop recording after 30 seconds
	# 	if time.time() - start > 30:
	# 		camera.stop_recording()



	