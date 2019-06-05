import socketio
import RPi.GPIO as GPIO

sio = socketio.Client(
	reconnection = True,
	reconnection_attempts = 10,
	reconnection_delay = 6
)
sio.connect('http://192.168.2.13:27372', namespaces=['/controller'])

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

sio.register_namespace(ControllerNameSpace('/controller'))
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

	