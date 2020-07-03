import smbus			
import time          
import RPi.GPIO as GPIO  
import math
import serial
import pigpio
from simple_pid import PID

pid = PID(0.03 , 7 , 0, setpoint=0)
pid2 = PID(0.05, 7, 0, setpoint=0)

pid.sample_time = 0.01
pid2.sample_time = 0.01

pi = pigpio.pi()

pi.set_servo_pulsewidth(13,1500)
pi.set_servo_pulsewidth(18,1500)
time.sleep(5)


pmv1=0
pmv2=0

def truncate(number, digits):
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper
    
 
GPIO.setmode(GPIO.BOARD)
GPIO.setup(12,GPIO.OUT)  
GPIO.setup(33,GPIO.OUT)  
#p = GPIO.PWM(12, 50)
#p2 = GPIO.PWM(33, 50)

#p.start(2.5)
#p2.start(2.5)
#p.ChangeDutyCycle(7.5)
#time.sleep(5)
 
bias1=0
bias2=0 

PWR_MGMT_1   = 0x6B
SMPLRT_DIV   = 0x19
CONFIG       = 0x1D
GYRO_CONFIG  = 0x1B
INT_ENABLE   = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47


def MPU_Init():
	bus.write_byte_data(Device_Address, SMPLRT_DIV, 7)
	
	bus.write_byte_data(Device_Address, PWR_MGMT_1, 1)
	
	bus.write_byte_data(Device_Address, CONFIG, 0)
	
	bus.write_byte_data(Device_Address, GYRO_CONFIG, 24)
	
	bus.write_byte_data(Device_Address, INT_ENABLE, 1)

def read_raw_data(addr):
		#value are 16-bit
        high = bus.read_byte_data(Device_Address, addr)
        low = bus.read_byte_data(Device_Address, addr+1)
    
        #concatenate higher and lower value
        value = ((high << 8) | low)
        
        #to get signed value from mpu6050
        if(value > 32768):
                value = value - 65536
        return value


bus = smbus.SMBus(1) 	#initialize i2c
Device_Address = 0x68   # MPU6050 address

MPU_Init()

while True:
	"""try:
		x=ser.readline()
		print (x)
		z=x.split('.')
		bias1= int(z[0])
		bias2= int(z[1])
	except:
		pass"""
	
	#Read Accelerometer raw value
	acc_x = read_raw_data(ACCEL_XOUT_H)
	acc_y = read_raw_data(ACCEL_YOUT_H)
	acc_z = read_raw_data(ACCEL_ZOUT_H)
	
	Ax = acc_x/16384.0
	Ay = acc_y/16384.0
	Az = acc_z/16384.0
	
	#print(Ax,Ay,Az)    
	       
	try:
		angle = truncate(math.degrees(math.atan(Ax/Az)),0)
	except:
		angle = 90
	
	try:
		angle2 = truncate(math.degrees(math.atan(-Ay/(Ax*Ax+Az*Az))),0)
	except:
		angle2 = 90
	
	if(angle>0):
		angle = 90 + (90 - angle)
	if(angle<0):
		angle = 90 - (90 + angle)	
	
	angle2 = 90 + angle2	
	
	if(angle>86 and angle<94):
		angle=90
	if(angle2>87 and angle2<93):
		angle2=90

	#anglex=(pmv1+angle)/2
	#angley=(pmv2+angle2)/2
	
	errorx = int(angle - 90)
	errory = int(angle2 - 90)
	
	
	#pmv1=angle
	#pmv2=angle2
	
	#pcont = 0.3
	#errorx =  pcont * errorx
	#errory =  pcont * errory
	
	z=pid(errorx)
	z2=pid2(errory)
	
	
	anglex = 90 + z
	angley = 90 + z2
	
	#print(z,angle,anglex)
	
	#anglex = pcont*anglex
	#angley = pcont*angley
	
	#print(anglex,angley,angle,angle2)
	
	#anglex = pid(anglex)
	
	#angle x step reduction filter
	#anglex = anglex - anglex%2
	#angle x step reduction filter
	#angley = angley - angley%2
	

	
	duty2 = 500 + (angley/180)*2000
	if(duty2>2500):
		duty2=2500
	if(duty2<500):
		duty2=500
	pi.set_servo_pulsewidth(13, duty2)
	
	

	duty = 500 + (anglex/180)*2000
	if(duty>2500):
		duty=2500
	if(duty<500):
		duty=500
	pi.set_servo_pulsewidth(18,duty)
	
	#print(duty,duty2)
	time.sleep(0.01)
