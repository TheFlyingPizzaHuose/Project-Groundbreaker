import time
import board
import busio
import digitalio
import adafruit_rfm9x
import adafruit_lsm9ds1
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_gps

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
accel_timeBtwnSamp = 0.05

gyro_sumX0 = gyro_sumY0 = gyro_sumZ0 = gyro_samps = gyro_lastSamp = 0
gyro_timeBtwnSamp = .05

print("Calibrating Sensors...")
sampleTime = 3
calibrationStart = time.time()
while time.time() - calibrationStart < sampleTime:
    print("helloooooo")
    #print(time.time()-calibrationStart)
    if time.time() - gyro_lastSamp > gyro_timeBtwnSamp:
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

    if time.time()-lastCollected >= 0.01:
        lastCollected = time.time()
        if not gps.has_fix:
            gps.latitude = 0
            gps.longitude = 0
            gps.satellites = 0
        #ser.open()
        #ser.flushOutput()
        # Read acceleration, magnetometer, gyroscope, temperature.
        accel_x,accel_y, accel_z = sensor.acceleration
        #print(accel_x,accel_y,accel_z)
        #accel_x = (accel_x-accel_x0) * 3.28084
        #accel_y = (accel_y-accel_y0) * 3.28084
        #accel_z = (accel_z-accel_z0) * 3.28084
        #print(accel_x,accel_y,accel_z)
        mag_x, mag_y, mag_z = sensor.magnetic
        gyro_x, gyro_y, gyro_z = sensor.gyro
        #print(gyro_x, gyro_x-init_gyro_x)
        #print("="*40)
        #print(gyro_x,gyro_y,gyro_z)
        gyro_x = gyro_x-gyro_x0
        gyro_y = gyro_y-gyro_y0
        gyro_z = gyro_z-gyro_z0
        #print(gyro_x,gyro_y,gyro_z)
        temp = bme280.temperature * (9/5) + 32
        humidity = bme280.humidity
        pressure = bme280.pressure
        altitude = (bme280.altitude - initial_altitude) * 3.28084

        # Delay for a second.
        #time.sleep(1.0)
        if gps.altitude_m is None:
                gps.altitude_m = 0
        if gps.speed_knots is None:
                gps.speed_knots = 0
        data = "{0:0.3f},{1:0.3f},{2:0.3f},{3:0.3f},{4:0.3f},{5:0.3f},{6:0.3f},{7:0.3f},{8:0.3f},{9:0.3f},{10:0.3f},{11:0.3f},{12:0.3f},{13:0.3f},{14:0.3f},{15:0.3f},{16:0.3f},{17:0.3f},{18:0.3f},{19:0.3f},\n".format(
		time.time()-startTime ,accel_x, accel_y, accel_z, mag_x, mag_y, mag_z, gyro_x, gyro_y, gyro_z, temp, humidity, pressure, altitude,
                gps.fix_quality, gps.satellites, gps.latitude, gps.longitude, gps.altitude_m*3.28084, gps.speed_knots*1.688)
        
        rfm9x.send(data.encode('utf-8'))
        #print(data)
        #ser.write(data.encode('utf-8'))
        #ser.close()
