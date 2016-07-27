from math import sin
from time import sleep
import serial
import PyQt4
from scipy.interpolate import interp1d
#s = serial.Serial(port='/dev/cu.wchusbserial1420', baudrate=9600)
s = serial.Serial(port='/dev/cu.wchusbserial1410', baudrate=115200)

def _str(s): return str.encode(str(s));

servoMins = (150,150,150,150,150,150,150,150,150,150,150,150,150,150)
servoMaxs = (550,550,550,550,550,550,550,550,550,550,550,550,550,550)

offsets = (   0.0581622678397,
			  -0.0229716520039,
			  0.0386119257087,
			  0.0532746823069,
			  0.0395894428152,
			  -0.033724340176,
			  0,
			  0,
			  0,
			  0,
			  0,
			  0,
			  0,
			  0,
			  0,
			  0,)

def setServo(i, u):
	u = max(0, min(1.0, u + offsets[i]))
	v = servoMins[i] + float(servoMaxs[i] - servoMins[i]) * (1.0 + u) * 0.5;
	#print 's servo: ' + str(int(i)) + ' value: ' + str(int(v))
	s.write('1 ' + str(int(i)) + ' ' + str(int(v)) + '\r\n')
	#print(str(s.readline()).strip())


f = 0.0

mult = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]

m1 = interp1d([0, 1023], [0, 1])

speed = 0.05
pos = 0

import sys
sys.path.append('/anaconda/lib/python3.5/site-packages')

#class GlutonServoAdjust(QWindow, ):


while True:
	for i in range(0,13):
		#setServo(i, sin(f*mult[i]))
		#setServo(i, pos)
		setServo(i, 0.5 + pos)
	f += speed
	s.write('2 1\r\n')
	r = str(s.readline()).strip()
	print('r', r)
	s.write('3 0\r\n')
	#v = int(str(s.readline()).strip())
	v = 0

	pos = 0.5 - m1(v)
	print('pos', pos)
