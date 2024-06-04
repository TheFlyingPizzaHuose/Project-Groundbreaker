import pygame
import board
import busio
import digitalio
import adafruit_rfm9x
import time
import RPi_I2C_driver
import math
import pygame_chart as pyc

# pygame setup
pygame.init()
screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode((screen_width, screen_height), flags=pygame.FULLSCREEN | pygame.SCALED)
clock = pygame.time.Clock()

# Colors:
slu_blue = (0,61,165)
background_color = (0,59,92)
panel_color = (200,201,199)
text_color = (0,0,0)

mylcd = RPi_I2C_driver.lcd()

# LoFa Radio Setup:
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.CE1)
reset = digitalio.DigitalInOut(board.D25)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 433.0)

# Images
slurpl_logo = pygame.image.load("slurpl logo white.png")
slurpl_logo = pygame.transform.scale(slurpl_logo, (slurpl_logo.get_width()*.175, slurpl_logo.get_height()*.175))
slu_logo = pygame.image.load("slu-2-left-white-rgb.png")
slu_logo = pygame.transform.scale(slu_logo, (slu_logo.get_width()*.5, slu_logo.get_height()*.5))

# Fonts
Title_Font = pygame.font.SysFont("calibri",45, True)
Header_Font = pygame.font.SysFont("calibri", 50,True)
Subheader_Font = pygame.font.SysFont("calibri", 30,True)
Data_Font = pygame.font.SysFont("calibri", 50,True)
Small_Data_Font = pygame.font.SysFont("calibri", 30,True)
Chute_Font = pygame.font.SysFont("calibri", 35,True)
Clock_Font = pygame.font.SysFont("calibri", 40,True)

# Title and header text (aren't dynamic)
title_text = Title_Font.render("PROJECT GROUNDBREAKER", True, (255, 255, 255))
gndbkr_text = Header_Font.render("Groundbreaker", True, (255, 255, 255))
parachute_text = Subheader_Font.render("Parachutes", True, text_color)
velocity_header = Subheader_Font.render("Velocity", True, text_color)
acceleration_header = Subheader_Font.render("Accelerometer", True, text_color)
gyro_header = Subheader_Font.render("Gyro", True, text_color)
mag_header = Subheader_Font.render("Magnometer", True, text_color)

# Rectangles
Groundbreaker_Panel = pygame.Rect(0, 760, 1125, screen_height/3)
Ground_Station_Panel = pygame.Rect(screen_width*(3/4) + 12, 760, screen_width/4, screen_height/3)
border_width = 8
camera_scale = 1.2
camera_width = 640*camera_scale
camera_height = 480*camera_scale
camera1 = pygame.Rect((screen_width-(camera_width*2))//3, 130, camera_width, camera_height)
camera1_text = Header_Font.render("Camera 1", True, (0,0,0))
camera2 = pygame.Rect(screen_width - (screen_width-(camera_width*2))//3 - camera_width, 130, camera_width, camera_height)
camera2_text = Header_Font.render("Camera 2", True, (0,0,0))
column1_rect = pygame.Rect(0, Groundbreaker_Panel.top, 665+border_width, screen_height-Groundbreaker_Panel.top)
column2_rect = pygame.Rect(column1_rect.right-border_width, Groundbreaker_Panel.top, 275+border_width, screen_height-Groundbreaker_Panel.top)
column3_rect = pygame.Rect(column2_rect.right-border_width, Groundbreaker_Panel.top, 325+border_width, screen_height-Groundbreaker_Panel.top)
#column3_rect = pygame.Rect(column3_rect.right-border_width, Groundbreaker_Panel.top, 1428-column3_rect.right+border_width, screen_height-Groundbreaker_Panel.top)
gyro_plot = pyc.Figure(screen, column3_rect.right, Groundbreaker_Panel.top, screen_width-column3_rect.right, screen_height-Groundbreaker_Panel.top,bg_color=panel_color)
gyro_plot_Rect = pygame.Rect(column3_rect.right, Groundbreaker_Panel.top, screen_width-column3_rect.right, screen_height-Groundbreaker_Panel.top)

# Settings
timeStart = time.time()
last_5_packets = []
edit_layout_mode = False
average_values = False

class Data:
    def __init__(self, value):
        self.value = value
        self.text = ""
        self.color = text_color
        self.time = 0
        
class FlightEvents:
    def __init__(self) -> None:
        self.liftoff = Data(False)
        self.burnout = Data(False)
        self.apogee = Data(False)
        self.main = Data(False)
        self.touchdown = Data(False)

def addGenericValues():
    altitude.value = 10000.00
    velocity.value = 400.00
    velocity_vector.value = [0.00, 400.00, 0.00]
    temperature.value = 69
    acceleration.value = [0.0, -32.2, 0.0]
    gyro.value = [0.012, 0.032, 0.058]
    mag.value = [0.036, 0.048, 0.061]
    signal_strength.value = -90
    if time.time()-timeStart > 2:
        flt_events.liftoff.value = True
    if time.time()-timeStart > 4:
        flt_events.burnout.value = True
    if time.time()-timeStart > 6:
        flt_events.apogee.value = True
    if time.time()-timeStart > 8:
        flt_events.main.value = True
    if time.time()-timeStart > 10:
        flt_events.touchdown.value = True

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
    
    flt_events.liftoff.text = Small_Data_Font.render("Liftoff: " + str(flt_events.liftoff.value) + ", " + str(flt_events.liftoff.time), True, flt_events.liftoff.color)
    flt_events.burnout.text = Small_Data_Font.render("Burnout: " + str(flt_events.burnout.value) + ", " + str(flt_events.burnout.time), True, flt_events.burnout.color)
    flt_events.apogee.text = Small_Data_Font.render("Apogee: " + str(flt_events.apogee.value) + ", " + str(flt_events.apogee.time), True, flt_events.apogee.color)
    flt_events.main.text = Small_Data_Font.render("Main: " + str(flt_events.main.value) + ", " + str(flt_events.main.time), True, flt_events.main.color)
    flt_events.touchdown.text = Small_Data_Font.render("Landed: " + str(flt_events.touchdown.value) + ", " + str(flt_events.touchdown.time), True, flt_events.touchdown.color)

def displayHeaderText():
    screen.blit(title_text,(screen_width/2 - title_text.get_width()//2, 40))
    screen.blit(camera1_text,(camera1.center[0]-camera1_text.get_width()//2,camera1.center[1]-camera1_text.get_height()//2))
    screen.blit(camera2_text,(camera2.center[0]-camera2_text.get_width()//2,camera2.center[1]-camera2_text.get_height()//2))

    # Column 2: (Center Indented)
    screen.blit(acceleration_header,(column3_rect.center[0] - (acceleration_header.get_width()//2), Groundbreaker_Panel.top + border_width))
    screen.blit(velocity_header,(column3_rect.center[0] - (velocity_header.get_width()//2), Groundbreaker_Panel.top + (column3_rect.height*0.25 +border_width)))
    screen.blit(gyro_header,(column3_rect.center[0] - (gyro_header.get_width()//2), Groundbreaker_Panel.top + (column3_rect.height*0.5 +border_width)))
    screen.blit(mag_header,(column3_rect.center[0] - (mag_header.get_width()//2), Groundbreaker_Panel.top + (column3_rect.height*0.75 +border_width)))
    
    # SLU and SLURPL Images in the top corners:
    screen.blit(slurpl_logo, (screen_width-slurpl_logo.get_width(),-90))
    screen.blit(slu_logo, (20,10))

def displayDataText():
    # Column 1
    screen.blit(altitude.text,(20, Groundbreaker_Panel.top+border_width+5))
    screen.blit(velocity.text,(20, Groundbreaker_Panel.top+65+border_width))
    screen.blit(temperature.text,(20, Groundbreaker_Panel.top+125+border_width))
    screen.blit(signal_strength.text,(20, Groundbreaker_Panel.top+190+border_width))
    #screen.blit(drogue.text,(539, Groundbreaker_Panel.top+190))
    #screen.blit(main.text,(539, Groundbreaker_Panel.top+230))
    
    # Column2 
    screen.blit(flt_events.liftoff.text, (column2_rect.centerx - flt_events.liftoff.text.get_width()//2 ,column2_rect.top+20))
    screen.blit(flt_events.burnout.text, (column2_rect.centerx - flt_events.burnout.text.get_width()//2 ,column2_rect.top+50))
    screen.blit(flt_events.apogee.text, (column2_rect.centerx - flt_events.apogee.text.get_width()//2 ,column2_rect.top+80))
    screen.blit(flt_events.main.text, (column2_rect.centerx - flt_events.main.text.get_width()//2 ,column2_rect.top+110))
    screen.blit(flt_events.touchdown.text, (column2_rect.centerx - flt_events.touchdown.text.get_width()//2 ,column2_rect.top+140))
    
    # Column 3
    screen.blit(acceleration.text,(column3_rect.center[0] - acceleration.text.get_width()//2, Groundbreaker_Panel.top + column3_rect.height*(1/8)))
    screen.blit(velocity_vector.text,(column3_rect.center[0] - velocity_vector.text.get_width()//2, Groundbreaker_Panel.top + column3_rect.height*(3/8)))
    screen.blit(gyro.text,(column3_rect.center[0] - gyro.text.get_width()//2, Groundbreaker_Panel.top + column3_rect.height*(5/8)))
    screen.blit(mag.text,(column3_rect.center[0] - mag.text.get_width()//2, Groundbreaker_Panel.top + column3_rect.height*(7/8)))

    # Real time clock ========================================================================================
    hour, minute, second = time.strftime('%H'), time.strftime('%M'), time.strftime('%S')
    time_text = Data_Font.render(str(int(hour))+":"+str(minute)+":"+str(second) +" CDT", True, (255, 255, 255))
    screen.blit(time_text,(screen_width//2-time_text.get_width()//2,Groundbreaker_Panel.top-40))
    
def makeRectBorder(rect=pygame.Rect):
    pygame.draw.rect(screen, panel_color, pygame.Rect(rect.left+border_width, rect.top+border_width, rect.width-border_width*2, rect.height-border_width*2))

def displayRects():
    pygame.draw.rect(screen, panel_color, Groundbreaker_Panel)
    pygame.draw.rect(screen, (255,255,255), camera1)
    pygame.draw.rect(screen, (255,255,255), camera2)

    pygame.draw.rect(screen, slu_blue, column1_rect)
    makeRectBorder(column1_rect)
    pygame.draw.rect(screen, slu_blue, column2_rect)
    makeRectBorder(column2_rect)
    pygame.draw.rect(screen, slu_blue, column3_rect)
    makeRectBorder(column3_rect)

    pygame.draw.line(screen, slu_blue, (0,Groundbreaker_Panel.top+180+border_width),(column2_rect.right-border_width/2,Groundbreaker_Panel.top+180+border_width),border_width)
    pygame.draw.line(screen, slu_blue, (column3_rect.left,Groundbreaker_Panel.top),(column3_rect.right-border_width/2,Groundbreaker_Panel.top),border_width)
    pygame.draw.line(screen, slu_blue, (column3_rect.left,Groundbreaker_Panel.top + column3_rect.height*1/4),(column3_rect.right-border_width/2,Groundbreaker_Panel.top + column3_rect.height*1/4),border_width)
    pygame.draw.line(screen, slu_blue, (column3_rect.left,Groundbreaker_Panel.top + column3_rect.height*1/2),(column3_rect.right-border_width/2,Groundbreaker_Panel.top + column3_rect.height*1/2),border_width)
    pygame.draw.line(screen, slu_blue, (column3_rect.left,Groundbreaker_Panel.top + column3_rect.height*3/4),(column3_rect.right-border_width/2,Groundbreaker_Panel.top + column3_rect.height*3/4),border_width)
    pygame.draw.line(screen, slu_blue, (column3_rect.left,Groundbreaker_Panel.top + column3_rect.height),(column3_rect.right-border_width/2,Groundbreaker_Panel.top + column3_rect.height),border_width)

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

def getEvents():
    # Liftoff
    if not flt_events.liftoff.value:
        if acceleration.value[1] > 32.2*1.5:
            flt_events.liftoff = True
    
    if flt_events.liftoff.value:
        flt_events.liftoff.color = (0,190,0)
        if flt_events.liftoff.time == 0:
            flt_events.liftoff.time = round(time.time() - timeStart,2)
    if flt_events.burnout.value:
        flt_events.burnout.color = (0,190,0)
        if flt_events.burnout.time == 0:
            flt_events.burnout.time = round(time.time() - timeStart,2)
    if flt_events.apogee.value:
        flt_events.apogee.color = (0,190,0)
        if flt_events.apogee.time == 0:
            flt_events.apogee.time = round(time.time() - timeStart,2)
    if flt_events.main.value:
        flt_events.main.color = (0,190,0)
        if flt_events.main.time == 0:
            flt_events.main.time = round(time.time() - timeStart,2)
    if flt_events.touchdown.value:
        flt_events.touchdown.color = (0,190,0)
        if flt_events.touchdown.time == 0:
            flt_events.touchdown.time = round(time.time() - timeStart,2)

def guiloop():
    lastReceive = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        getEvents()
        
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

max_altitude = Data(-math.inf)
max_velocity = Data(-math.inf)
max_acceleration = Data(-math.inf)

flt_events = FlightEvents()

guiloop()
pygame.quit()
