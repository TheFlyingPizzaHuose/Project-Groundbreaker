import pygame
import board
import busio
import digitalio
import adafruit_rfm9x
import time
import RPi_I2C_driver
import math
import pygame_chart as pyc


# Colors:
background_color = (0,59,92)
panel_color = (200,201,199)
text_color = (0,0,0)

mylcd = RPi_I2C_driver.lcd()

# LoFa Radio Setup:
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.CE1)
reset = digitalio.DigitalInOut(board.D25)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 433.0)

# pygame setup
pygame.init()
screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode((screen_width, screen_height), flags=pygame.FULLSCREEN | pygame.SCALED)
clock = pygame.time.Clock()



Title_Font = pygame.font.SysFont("calibri",45)
Header_Font = pygame.font.SysFont("calibri", 50,True)
Subheader_Font = pygame.font.SysFont("calibri", 30,True)
Data_Font = pygame.font.SysFont("calibri", 50)
Small_Data_Font = pygame.font.SysFont("calibri", 30)
Chute_Font = pygame.font.SysFont("calibri", 35)
Clock_Font = pygame.font.SysFont("calibri", 40)
title_text = Title_Font.render("SAINT LOUIS UNIVERSITY ROCKET PROPULSION LAB: PROJECT GROUNDBREAKER", True, (255, 255, 255))
gndbkr_text = Header_Font.render("Groundbreaker", True, (255, 255, 255))
#gndstn_text = Header_Font.render("Gyro Plot", True, (255, 255, 255))

parachute_text = Subheader_Font.render("Parachutes", True, text_color)


velocity_header = Subheader_Font.render("Velocity", True, text_color)
acceleration_header = Subheader_Font.render("Accelerometer", True, text_color)
gyro_header = Subheader_Font.render("Gyro", True, text_color)
mag_header = Subheader_Font.render("Magnometer", True, text_color)


Groundbreaker_Panel = pygame.Rect(0, 760, 1125, screen_height/3)

Ground_Station_Panel = pygame.Rect(screen_width*(3/4) + 12, 760, screen_width/4, screen_height/3)

camera_scale = 1.2
camera_width = 640*camera_scale
camera_height = 480*camera_scale
camera1 = pygame.Rect((screen_width-(camera_width*2))//3, (800-camera_height)/2, camera_width, camera_height)
camera1_text = Header_Font.render("Camera 1", True, (0,0,0))
camera2 = pygame.Rect(screen_width - (screen_width-(camera_width*2))//3 - camera_width, (800-camera_height)/2, camera_width, camera_height)
camera2_text = Header_Font.render("Camera 2", True, (0,0,0))

line_width = 8
column1_rect = pygame.Rect(0, Groundbreaker_Panel.top, 800+line_width, screen_height-Groundbreaker_Panel.top)
column2_rect = pygame.Rect(800, Groundbreaker_Panel.top, 325, screen_height-Groundbreaker_Panel.top)
#column3_rect = pygame.Rect(column2_rect.right-line_width, Groundbreaker_Panel.top, 1428-column2_rect.right+line_width, screen_height-Groundbreaker_Panel.top)

gyro_plot = pyc.Figure(screen, column2_rect.right, Groundbreaker_Panel.top, screen_width-column2_rect.right, screen_height-Groundbreaker_Panel.top,bg_color=panel_color)
gyro_plot_Rect = pygame.Rect(column2_rect.right, Groundbreaker_Panel.top, screen_width-column2_rect.right, screen_height-Groundbreaker_Panel.top)

last_5_packets = []
edit_layout_mode = False
average_values = True

class Data:
    def __init__(self, value):
        self.value = value
        self.text = ""

def addGenericValues():
    altitude.value = 10000.00
    velocity.value = 400.00
    velocity_vector.value = [0.00, 400.00, 0.00]
    temperature.value = 69
    acceleration.value = [0.0, -32.2, 0.0]
    gyro.value = [0.012, 0.032, 0.058]
    mag.value = [0.036, 0.048, 0.061]
    signal_strength.value = -90

def updateDataText():
    altitude.text = Data_Font.render("Altitude: " + str(altitude.value) + " ft" + " ("+str(round(altitude.value * 0.3048, 2))+" m)", True, text_color)
    velocity.text = Data_Font.render("Speed: " + str(velocity.value) + " ft/s" + " ("+str(round(velocity.value*0.681818,2))+" mph)", True, text_color)
    temperature.text = Data_Font.render("Tempurature: " + str(temperature.value) + "°F" + " ("+str(round((temperature.value-32)*(5/9), 2))+"°C)", True, text_color)

    acceleration.text = Small_Data_Font.render("("+str(acceleration.value[0])+", " + str(acceleration.value[1])+ ", " + str(acceleration.value[2])+ ")", True, text_color)
    velocity_vector.text = Small_Data_Font.render("("+str(velocity_vector.value[0])+", " + str(velocity_vector.value[1])+ ", " + str(velocity_vector.value[2])+ ")", True, text_color)
    gyro.text = Small_Data_Font.render("("+str(gyro.value[0])+", " + str(gyro.value[1])+ ", " + str(gyro.value[2])+ ")", True, text_color)
    mag.text = Small_Data_Font.render("("+str(mag.value[0])+", " + str(mag.value[1])+ ", " + str(mag.value[2])+ ")", True, text_color)

    signal_strength.text = Small_Data_Font.render("Telemetry Signal Strength: "+str(signal_strength.value)+" dBm", True, text_color)
    drogue.text = Chute_Font.render("Drogue: "+ drogue.value, True, text_color)
    main.text = Chute_Font.render("Main: "+ main.value, True, text_color)

def displayHeaderText():
    screen.blit(title_text,(screen_width/2 - title_text.get_width()//2, 25))
    screen.blit(camera1_text,(camera1.center[0]-camera1_text.get_width()//2,camera1.center[1]-camera1_text.get_height()//2))
    screen.blit(camera2_text,(camera2.center[0]-camera2_text.get_width()//2,camera2.center[1]-camera2_text.get_height()//2))

    # Column 2: (Center Indented)
    screen.blit(acceleration_header,(column2_rect.center[0] - (acceleration_header.get_width()//2), Groundbreaker_Panel.top + line_width))
    screen.blit(velocity_header,(column2_rect.center[0] - (velocity_header.get_width()//2), Groundbreaker_Panel.top + (column2_rect.height*0.25 +line_width)))
    screen.blit(gyro_header,(column2_rect.center[0] - (gyro_header.get_width()//2), Groundbreaker_Panel.top + (column2_rect.height*0.5 +line_width)))
    screen.blit(mag_header,(column2_rect.center[0] - (mag_header.get_width()//2), Groundbreaker_Panel.top + (column2_rect.height*0.75 +line_width)))

def displayDataText():
    screen.blit(altitude.text,(20, Groundbreaker_Panel.top+line_width))
    screen.blit(velocity.text,(20, Groundbreaker_Panel.top+60+line_width))
    screen.blit(temperature.text,(20, Groundbreaker_Panel.top+120+line_width))
    screen.blit(signal_strength.text,(20, Groundbreaker_Panel.top+190+line_width))
    
    screen.blit(acceleration.text,(column2_rect.center[0] - acceleration.text.get_width()//2, Groundbreaker_Panel.top + column2_rect.height*(1/8)))
    screen.blit(velocity_vector.text,(column2_rect.center[0] - velocity_vector.text.get_width()//2, Groundbreaker_Panel.top + column2_rect.height*(3/8)))
    screen.blit(gyro.text,(column2_rect.center[0] - gyro.text.get_width()//2, Groundbreaker_Panel.top + column2_rect.height*(5/8)))
    screen.blit(mag.text,(column2_rect.center[0] - mag.text.get_width()//2, Groundbreaker_Panel.top + column2_rect.height*(7/8)))

    #screen.blit(drogue.text,(column3_rect.center[0] - drogue.text.get_width()//2, Groundbreaker_Panel.top+35))
    #screen.blit(main.text,(column3_rect.center[0] - main.text.get_width()//2, Groundbreaker_Panel.top+75))
    
def makeRectBorder(rect=pygame.Rect):
    pygame.draw.rect(screen, panel_color, pygame.Rect(rect.left+line_width, rect.top+line_width, rect.width-line_width*2, rect.height-line_width*2))

def displayRects():
    pygame.draw.rect(screen, panel_color, Groundbreaker_Panel)
    pygame.draw.rect(screen, (255,255,255), camera1)
    pygame.draw.rect(screen, (255,255,255), camera2)

    pygame.draw.rect(screen, (0,61,165), column1_rect)
    makeRectBorder(column1_rect)
    pygame.draw.rect(screen, (0,61,165), column2_rect)
    makeRectBorder(column2_rect)
    #pygame.draw.rect(screen, (0,61,165), column3_rect)
    #makeRectBorder(column3_rect)

    pygame.draw.line(screen, (0,61,165), (0,Groundbreaker_Panel.top+180+line_width),(column1_rect.right-line_width/2,Groundbreaker_Panel.top+180+line_width),line_width)
    pygame.draw.line(screen, (0,61,165), (column2_rect.left,Groundbreaker_Panel.top),(column2_rect.right-line_width/2,Groundbreaker_Panel.top),line_width)
    pygame.draw.line(screen, (0,61,165), (column2_rect.left,Groundbreaker_Panel.top + column2_rect.height*1/4),(column2_rect.right-line_width/2,Groundbreaker_Panel.top + column2_rect.height*1/4),line_width)
    pygame.draw.line(screen, (0,61,165), (column2_rect.left,Groundbreaker_Panel.top + column2_rect.height*1/2),(column2_rect.right-line_width/2,Groundbreaker_Panel.top + column2_rect.height*1/2),line_width)
    pygame.draw.line(screen, (0,61,165), (column2_rect.left,Groundbreaker_Panel.top + column2_rect.height*3/4),(column2_rect.right-line_width/2,Groundbreaker_Panel.top + column2_rect.height*3/4),line_width)
    pygame.draw.line(screen, (0,61,165), (column2_rect.left,Groundbreaker_Panel.top + column2_rect.height),(column2_rect.right-line_width/2,Groundbreaker_Panel.top + column2_rect.height),line_width)

def getTelemetry(packet, lastReceive):    
    variables=[]
    packet_text = str(packet, 'ascii')
    for var in packet_text.split(','):
        if var == '\n':
            continue
        variables.append(round(float(var),2))

    
    last_5_packets.append(variables)
    if len(last_5_packets) > 40:
        last_5_packets.pop(0)
        if average_values:
            variables = [ round(sum(x)/len(last_5_packets) ,2) for x in zip(*last_5_packets) ]

    time_av = variables[0]
    acceleration.value = [round(variables[1]*3.28084,2), round(variables[2]*3.28084,2), round(variables[3]*3.28084,2)]
    mag.value = [variables[4], variables[5], variables[6]]
    gyro.value = [variables[7], variables[8], variables[9]]
    temperature.value = round(variables[10] * (9/5) + 32,2)
    humidity.value = variables[11]
    pressure.value = variables[12]
    altitude.value = round(variables[13]*3.28084,2)

    velocity_vector.value = [round(acceleration.value[0]*(time.time()-lastReceive),2), round((32.2+acceleration.value[1])*(time.time()-lastReceive),2), round(acceleration.value[2]*(time.time()-lastReceive),2)]
    velocity.value = round(math.sqrt((velocity_vector.value[0]*velocity_vector.value[0]) + (velocity_vector.value[1]*velocity_vector.value[1]) + (velocity_vector.value[2]*velocity_vector.value[2])),2)
    signal_strength.value = rfm9x.last_rssi       

def guiloop():
    lastReceive = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        
        drogue.value = "Deployed"
        main.value = "Stowed"
        packet = rfm9x.receive()  
        if packet is not None:
            if time.time()-lastReceive >= 0.05:
                getTelemetry(packet, lastReceive)      
                lastReceive = time.time()  
                
        else:
            addGenericValues()



        screen.fill(background_color)
        if edit_layout_mode:
            addGenericValues()


        if len(last_5_packets) > 1:
            variables_last_5_packets = [ x for x in zip(*last_5_packets) ]
            gyro_plot.add_legend()
            gyro_plot.add_gridlines()
            gyro_plot.add_title("Raw Gyro")
            gyro_plot.line('Gyro_x', list(variables_last_5_packets[0]),list(variables_last_5_packets[7]),200)
            gyro_plot.line('Gyro_y', list(variables_last_5_packets[0]),list(variables_last_5_packets[8]),line_width=8)
            gyro_plot.line('Gyro_z', list(variables_last_5_packets[0]),list(variables_last_5_packets[9]),line_width=8)
            gyro_plot.draw()  
        displayRects()
        displayHeaderText()
        updateDataText()
        displayDataText()
        hour, minute, second = time.strftime('%H'), time.strftime('%M'), time.strftime('%S')
        timeString = str(int(hour)+6)+":"+str(minute)+":"+str(second) +" CDT"
        screen.blit(Data_Font.render(timeString, True, (255, 255, 255)),(5,Groundbreaker_Panel.top-40))

        

        pygame.display.flip()
        clock.tick(60)  # limits FPS to 60
        

        # Display on LCD:
        mylcd.lcd_display_string_pos("A:{}".format(altitude.value), 1, 0)
        mylcd.lcd_display_string_pos("S:{}".format(rfm9x.last_rssi), 1, 11)
        mylcd.lcd_display_string_pos("T:{}".format(temperature.value), 2, 0)
        mylcd.lcd_display_string_pos("V:{}".format(velocity.value), 2, 8)


    
altitude = Data(0)
velocity = Data(0)
velocity_vector = Data([0,0,0])
mach = Data(0)
temperature = Data(0)

acceleration = Data([0,0,0])
gyro = Data([0,0,0])
mag = Data([0,0,0])
humidity = Data(0)
pressure = Data(0)
signal_strength = Data(0)

drogue = Data("Stowed")
main = Data("Stowed")
guiloop()
pygame.quit()
