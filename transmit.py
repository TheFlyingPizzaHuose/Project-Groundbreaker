import time
import board
import busio
import digitalio
import adafruit_rfm9x
import adafruit_lsm9ds1
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_gps
import math

import serial
import time

i2c = board.I2C()

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.CE1)
reset = digitalio.DigitalInOut(board.D25)

# GPS:
uart = serial.Serial("/dev/ttyS0",baudrate=9600,timeout=10)
gps = adafruit_gps.GPS(uart, debug=False)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220, 1000")


rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 433.0)
rfm9x.tx_power = 17

lastCollected = time.time()
last_gps_update = time.monotonic()
startTime = time.time()

sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

initial_altitude = bme280.altitude
init_accel_x,init_accel_y, init_accel_z = sensor.acceleration
init_gyro_x,init_gyro_y,init_gyro_z = sensor.gyro

accel_sumX0 = accel_sumY0 = accel_sumZ0 = accel_samps = accel_lastSamp = 0
accel_timeBtwnSamp = 0.001

gyro_sumX0 = gyro_sumY0 = gyro_sumZ0 = gyro_samps = gyro_lastSamp = 0
gyro_timeBtwnSamp = .001

pitchX = yawY = rollZ = 0

def getQuatRotn(dx, dy, dz, gyroGain):

    #Local Vectors
    Quat = [0.0, 1.0, 0.0, 0.0, 0.0]
    QuatDiff =[0, 0, 0, 0, 0]
    Rotn1=[0, 0, 0, 0]
    Rotn2=[0, 0, 0, 0]
    Rotn3=[0, 0, 0, 0]

    #Local rotation holders
    prevRollZ = 0
    quatRollZ = 0
    fullRollZ = 0

    #convert to radians
    rotn2rad = gyroGain * (3.14159265359 / 180) / 1000000
    dx *= rotn2rad
    dy *= rotn2rad
    dz *= rotn2rad

    #Compute quaternion derivative
    QuatDiff[1] = 0.5 * (-1 * dx * Quat[2] - dy * Quat[3] - dz * Quat[4])
    QuatDiff[2] = 0.5 * (     dx * Quat[1] - dy * Quat[4] + dz * Quat[3])
    QuatDiff[3] = 0.5 * (     dx * Quat[4] + dy * Quat[1] - dz * Quat[2])
    QuatDiff[4] = 0.5 * (-1 * dx * Quat[3] + dy * Quat[2] + dz * Quat[1])

    #Update the quaternion
    Quat[1] += QuatDiff[1]
    Quat[2] += QuatDiff[2]
    Quat[3] += QuatDiff[3]
    Quat[4] += QuatDiff[4]

    #re-normalize
    quatLen = pow( Quat[1]*Quat[1] + Quat[2]*Quat[2] + Quat[3]*Quat[3] + Quat[4]*Quat[4], -0.5)
    Quat[1] *= quatLen
    Quat[2] *= quatLen
    Quat[3] *= quatLen
    Quat[4] *= quatLen

    #compute the components of the rotation matrix
    a = Quat[1]
    b = Quat[2]
    c = Quat[3]
    d = Quat[4]
    a2 = a*a
    b2 = b*b
    c2 = c*c
    d2 = d*d
    ab = a*b
    ac = a*c
    ad = a*d
    bc = b*c
    bd = b*d
    cd = c*d

    #Compute rotation matrix
    Rotn1[1] = a2 + b2 - c2 - d2
    #Rotn1[2] = 2 * (bc - ad)
    #Rotn1[3] = 2 * (bd + ac)
    Rotn2[1] = 2 * (bc + ad)
    #Rotn2[2] = a2 - b2 + c2 - d2
    #Rotn2[3] = 2 * (cd - ab)
    Rotn3[1] = 2 * (bd - ac)
    Rotn3[2] = 2 * (cd + ab)
    Rotn3[3] = a2 - b2 - c2 + d2

    #compute 3D orientation
    
    pitchX = math.atan2(Rotn3[2], Rotn3[3])#this returns tenths of a degree, not whole degrees
    yawY = math.asin(-1*Rotn3[1])#this returns tenths of a degree, not whole degrees

    prevRollZ = quatRollZ
    quatRollZ = math.atan2(Rotn2[1], Rotn1[1])
    if quatRollZ - prevRollZ > 1800:
        fullRollZ = fullRollZ - 1
    elif quatRollZ - prevRollZ < -1800:
        fullRollZ = fullRollZ + 1
    rollZ = (fullRollZ*3600 + quatRollZ)*.1#this is in whole degrees since its usually MUCH bigger than pitch and yaw

    #Compute angle off vertical
    tanYaw = math.tan(yawY)
    tanPitch = math.tan(pitchX)
    hyp1 = tanYaw*tanYaw + tanPitch*tanPitch
    hyp2 = pow(hyp1, 0.5)
    offVert = math.atan(hyp2)#this returns tenths of a degree, not whole degrees

    print(pitchX,yawY,rollZ)

currentEvent = "Preflight"

print("Calibrating Sensors...")
sampleTime = 3
calibrationStart = time.time()
while time.time() - calibrationStart < sampleTime:
    if time.time() - gyro_lastSamp > gyro_timeBtwnSamp:
        print(time.time() - gyro_lastSamp)
        gyro_x,gyro_y,gyro_z = sensor.gyro
        gyro_lastSamp = time.time()

        gyro_sumX0 += gyro_x
        gyro_sumY0 += gyro_y
        gyro_sumZ0 += gyro_z
        gyro_samps += 1

    if time.time() - accel_lastSamp > accel_timeBtwnSamp:
        accel_x,accel_y,accel_z = sensor.acceleration
        accel_lastSamp = time.time()

        accel_sumX0 += accel_x
        accel_sumY0 += accel_y
        accel_sumZ0 += accel_z
        accel_samps += 1


gyro_x0 = (gyro_sumX0/gyro_samps)
gyro_y0 = (gyro_sumY0/gyro_samps)
gyro_z0 = (gyro_sumZ0/gyro_samps)

accel_x0 = (accel_sumX0/accel_samps)
accel_y0 = (accel_sumY0/accel_samps)
accel_z0 = (accel_sumZ0/accel_samps)
print("Accelerometer error: ", accel_x0,accel_y0,accel_z0)
print("Gyro error: ", gyro_x0,gyro_y0,gyro_z0)



print("Transmitting!!")
#ser.close()
while True:
    if time.monotonic() - last_gps_update >= 1.0:
        gps.update()
        last_gps_update - time.monotonic()
    #Current events: 0=preflight, 1=liftoff, 2=apogeee
    if currentEvent == 0:
        timeBtwnSamples = 1.5
    elif currentEvent == 1:
        timeBtwnSamples = 0.001
    
    
    if time.time()-lastCollected >= timeBtwnSamples:
        lastCollected = time.time()
        if not gps.has_fix:
            gps.latitude = 0
            gps.longitude = 0
            gps.satellites = 0

        # Read acceleration, magnetometer, gyroscope, temperature.
        accel_x,accel_y, accel_z = sensor.acceleration
        mag_x, mag_y, mag_z = sensor.magnetic
        gyro_x, gyro_y, gyro_z = sensor.gyro
        
        gyro_x = gyro_x-gyro_x0
        gyro_y = gyro_y-gyro_y0
        gyro_z = gyro_z-gyro_z0

        getQuatRotn(-gyro_x*.001,gyro_z*.001, gyro_y*.001, 0.07)#update absolute rotation values
        
        temp = bme280.temperature * (9/5) + 32
        humidity = bme280.humidity
        pressure = bme280.pressure
        altitude = (bme280.altitude - initial_altitude) * 3.28084

        if gps.altitude_m is None:
                gps.altitude_m = 0
        if gps.speed_knots is None:
                gps.speed_knots = 0
        data = "{0:0.3f},{1:0.3f},{2:0.3f},{3:0.3f},{4:0.3f},{5:0.3f},{6:0.3f},{7:0.3f},{8:0.3f},{9:0.3f},{10:0.3f},{11:0.3f},{12:0.3f},{13:0.3f},{14:0.3f},{15:0.3f},{16:0.3f},{17:0.3f},{18:0.3f},{19:0.3f},{20:0.3f},{21:0.3f},{22:0.3f},{23:0.3f}\n".format(
		time.time()-startTime ,accel_x, accel_y, accel_z, mag_x, mag_y, mag_z, gyro_x, gyro_y, gyro_z, temp, humidity, pressure, altitude,
                gps.fix_quality, gps.satellites, gps.latitude, gps.longitude, gps.altitude_m*3.28084, gps.speed_knots*1.688, currentEvent, pitchX, yawY, rollZ)
        
        rfm9x.send(data.encode('utf-8'))