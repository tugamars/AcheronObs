import cv2
import numpy as np
import time
from collections import defaultdict 
import sys
import json
import requests
from collections import deque
from termcolor import colored
import pytesseract
from pytesseract import Output
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *

with open('config.json') as config_file:
    archconfig = json.load(config_file)
# Globals
health_percentage = archconfig['health_percentage']
maxvalue = archconfig['maxvalue']
pv_player = []
pytesseract.pytesseract.tesseract_cmd = r'E:\Program Files\Tesseract-OCR\tesseract.exe'
apiurl = 'http://localhost:7000/api/123'
camera_index = archconfig['camera_index']
player1 = archconfig['player1']+3
player2 = archconfig['player2']+3
player3 = archconfig['player3']+3
player4 = archconfig['player4']+3
player5 = archconfig['player5']+3
player6 = archconfig['player6']+3
player7 = archconfig['player7']+3
player8 = archconfig['player8']+3
player9 = archconfig['player9']+3
player0 = archconfig['player0']+3
teamleftScore = archconfig['teamleftScore']
teamrightScore = archconfig['teamrightScore']
ENABLEDETECTION = True
VERBOSE = False
VERBOSETESSERACT = False
DISPLAYHEALTH = False
DISPLAYSCORE = False
DISPLAYROUNDTIME = False
POST = True

try:
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
except:
    print("Something went wrong with the capture (Error 3003)")

def cleanFrameRed(frame):
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    #frame = cv2.medianBlur(frame,5)
    frame = cv2.threshold(frame, 50, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    kernel = np.ones((3,3),np.uint8)
    frame = cv2.dilate(frame, kernel, iterations = 1)
    frame = cv2.erode(frame, kernel, iterations = 1)
    frame = cv2.morphologyEx(frame, cv2.MORPH_OPEN, kernel)
    #frame = cv2.Canny(frame, 100, 200)

    return frame

def cleanFrameWhite(frame):
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    #frame = cv2.medianBlur(frame,5)
    frame = cv2.threshold(frame, 255, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    kernel = np.ones((2,2),np.uint8)
    frame = cv2.dilate(frame, kernel, iterations = 1)
    frame = cv2.erode(frame, kernel, iterations = 1)
    frame = cv2.morphologyEx(frame, cv2.MORPH_CLOSE, kernel)
    #frame = cv2.Canny(frame, 100, 200)

    return frame

def cleanFrameScore(frame):
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
    frame = cv2.bilateralFilter(frame,9,75,75)
    frame = cv2.threshold(frame, 240, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    kernel = np.ones((4,4),np.uint8)
    frame = cv2.dilate(frame, kernel, iterations = 1)
    frame = cv2.erode(frame, kernel, iterations = 1)
    frame = cv2.morphologyEx(frame, cv2.MORPH_CLOSE, kernel)
    #frame = cv2.Canny(frame, 50, 100)

    return frame

def grabHealthBar(left):
    width  = 40
    height = 2
    startY = 78
    endY = startY + height
    startX = left
    endX = left + width

    ret, frame = cap.read()
    frame = frame[startY:endY,startX:endX]

    return cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

def grabRoundTimer():
    width = 90
    height = 60
    startY = 20
    left = 920
    endY = startY + height
    startX = left
    endX = left + width

    ret, frame = cap.read()
    frame = frame[startY:endY,startX:endX]
    
    return cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

def grabTeamScore(left):
    width = 46
    height = 43
    startY = 30
    endY = startY + height
    startX = left
    endX = left + width

    ret, frame = cap.read()
    frame = frame[startY:endY,startX:endX]

    return cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

def getBuffer(healthbar):
    frame_ring_buffer = deque([], 3)
    frame_ring_buffer.append(healthbar)
    time.sleep(0.001)
    frame_ring_buffer.append(healthbar)
    time.sleep(0.001)
    frame_ring_buffer.append(healthbar)
    time.sleep(0.001)

    frame1 = cv2.cvtColor(np.array(frame_ring_buffer[0]), cv2.COLOR_RGB2BGR)

    if(len(frame_ring_buffer) == 3):
        frame2 = cv2.cvtColor(np.array(frame_ring_buffer[1]), cv2.COLOR_RGB2BGR)
        frame3 = cv2.cvtColor(np.array(frame_ring_buffer[2]), cv2.COLOR_RGB2BGR)
        frame2 = cv2.max(frame1, frame2)
        health_bar = cv2.max(frame2, frame3)
    else:
        print(colored("WARNING: Frame buffer < 3", "yellow"))
        health_bar = frame1

    return health_bar

def getRoundTimer():
    frame = grabRoundTimer()
    frame1 = cleanFrameWhite(frame)

    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789:.'
    roundtime = pytesseract.image_to_string(frame1, config=custom_config)
    if not roundtime:
        frame = cleanFrameRed(frame)
        roundtime = pytesseract.image_to_string(frame, config=custom_config)
        if not roundtime:
            roundtime = "00:00"

    if VERBOSETESSERACT == True:
        print("Round time: " + str(roundtime))

    if DISPLAYROUNDTIME == True :
        cv2.imshow(str("Round Time"),hsvBar)
        cv2.waitKey(0)

    return roundtime

def getScore(team):
    frame = grabTeamScore(team)
    frame = cleanFrameScore(frame)

    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789 outputbase digit'
    score = pytesseract.image_to_string(frame, config=custom_config)
    if not score:
        score = "0"
        print("Warning ! Score not detected")

    if VERBOSETESSERACT == True:
        print("Score: " + str(score))

    if DISPLAYSCORE == True :
        cv2.imshow(str("Score"),hsvBar)
        cv2.waitKey(0)

    return score

def getHealthBar(player):
        healthBar = grabHealthBar(player)
        health_bar = getBuffer(healthBar)

        # Masque blanc
        mask1 = cv2.inRange(health_bar, np.array([240, 240, 240]), np.array([255, 255, 255]))

        # Conversion bgr => hsv
        health_bar_hsv = cv2.cvtColor(health_bar, cv2.COLOR_BGR2HSV)

        lower_red1 = np.array([170, 110, 85])
        upper_red1 = np.array([180, 255, 255])
        lower_red2 = np.array([0, 110, 85])
        upper_red2 = np.array([20, 255, 255])

        # Masques rouge
        mask2 = cv2.inRange(health_bar_hsv, lower_red1, upper_red1)
        mask3 = cv2.inRange(health_bar_hsv, lower_red2, upper_red2)

        # Je cherche sur mon masque et par sur mon image parce que ça marche bien
        hsvBar = cv2.bitwise_or(mask2, mask3)

        health_bar = cv2.bitwise_and(health_bar, health_bar, mask = mask1)
        health_bar = cv2.cvtColor(health_bar, cv2.COLOR_BGR2GRAY)
        hbpixels = health_bar.reshape(-1,1)
        lhbpixels = hsvBar.reshape(-1,1)
        pv = 0
        foundpixels = False

        for hbpixel in hbpixels:
            if hbpixel[0] >= 240:
               pv += 1
               foundpixels = True

        for lhbpixel in lhbpixels:
            if (foundpixels == False): 
                    if lhbpixel[0] >= 240:
                        pv += 1
        health_percent = pv/maxvalue * 100
        if (health_percent > 100):
            health_percent = 100

        # Buffer de 3 mesures
        health_percent_buffer = deque([], 3)

        health_percent_buffer.append(health_percent)
        health_percent_buffer.append(health_percent)
        health_percent_buffer.append(health_percent)

        health_percent = round(np.mean(health_percent_buffer))

        if VERBOSE == True:
            print('Detected health : ' + str(round(health_percent,-1)))

        if DISPLAYHEALTH == True :
            screengrab = cv2.resize(screengrab, (460, 120))
            cv2.imshow(str(player + 2),screengrab)
            health_bar = cv2.resize(health_bar, (460, 120))
            cv2.imshow(str(player),health_bar)
            hsvBar = cv2.resize(hsvBar, (460, 120))
            cv2.imshow(str(player + 1),hsvBar)
            cv2.waitKey(0)

        return health_percent

def fixHalfTime(scoreLeft,scoreRight):
    if int(scoreLeft) + int(scoreRight) >= 12:
        scoreLeft, scoreRight = scoreRight, scoreLeft

    return scoreLeft,scoreRight

def postDetection(pv_player,scoreLeft,scoreRight,roundtime):
    try:
        with requests.get(apiurl) as api:
            data = api.json()
            data["roundtime"] = str(roundtime)
            data["team1"]["players"][0]["hp"] = str(pv_player[0])
            data["team1"]["players"][1]["hp"] = str(pv_player[1])
            data["team1"]["players"][2]["hp"] = str(pv_player[2])
            data["team1"]["players"][3]["hp"] = str(pv_player[3])
            data["team1"]["players"][4]["hp"] = str(pv_player[4])
            data["team2"]["players"][0]["hp"] = str(pv_player[5])
            data["team2"]["players"][1]["hp"] = str(pv_player[6])
            data["team2"]["players"][2]["hp"] = str(pv_player[7])
            data["team2"]["players"][3]["hp"] = str(pv_player[8])
            data["team2"]["players"][4]["hp"] = str(pv_player[9])
            data["team1"]["roundscore"] = str(scoreLeft)
            data["team2"]["roundscore"] = str(scoreRight)

            response = requests.post(apiurl, json=data)
            print("Status code: ", response.status_code)
    except:
        print("API not responding (Error 3006)")

def startDetection():
    global pv_player
    while ENABLEDETECTION == True:
        roundtime = getRoundTimer()
        pv_player.append(getHealthBar(player1))
        pv_player.append(getHealthBar(player2))
        pv_player.append(getHealthBar(player3))
        pv_player.append(getHealthBar(player4))
        pv_player.append(getHealthBar(player5))
        pv_player.append(getHealthBar(player6))
        pv_player.append(getHealthBar(player7))
        pv_player.append(getHealthBar(player8))
        pv_player.append(getHealthBar(player9))
        pv_player.append(getHealthBar(player0))
        scoreLeft = getScore(teamleftScore)
        scoreRight = getScore(teamrightScore)

        ## FIX FOR THE HUD RITO PLEASE FIX
        fixHalfTime(scoreLeft,scoreRight)

        if POST == True:
            postDetection(pv_player,scoreLeft,scoreRight,roundtime)
        pv_player = []

class Worker(QRunnable):
    @Slot()
    def run(self):
        startDetection()

class Widget(QWidget):
    def __init__(self):
        self.threadpool = QThreadPool()
        QWidget.__init__(self)
        
        self.logo = QPixmap('acheronlogo.png')
        self.enablepost = QPushButton("Enable POST")
        self.quit = QPushButton("Quit")
        self.startdetection = QPushButton("Start Detection")
        self.enabledetection = QPushButton("Stop Detection")
        self.label = QLabel()
        self.label.setPixmap(self.logo)
        self.edit_apiurl = QLineEdit("http://localhost:7000/api/123")
        self.button_apiurl = QPushButton("Set API Url")
        self.right = QVBoxLayout()
        self.right.setMargin(10)

        #RIGHT
        self.right.addWidget(self.label)
        self.right.addWidget(self.edit_apiurl)
        self.right.addWidget(self.button_apiurl)
        self.right.addWidget(self.enablepost)
        self.right.addWidget(self.enabledetection)
        self.right.addWidget(self.startdetection)
        self.right.addWidget(self.quit)

        self.layout = QHBoxLayout()

        #LEFT
        #...

        self.layout.addLayout(self.right)

        self.setLayout(self.layout)

        #Connect Actions
        self.quit.clicked.connect(self.quit_application)
        self.startdetection.clicked.connect(self.startdetect)
        self.enablepost.clicked.connect(self.enablePost)
        self.enabledetection.clicked.connect(self.enableDetection)
        self.button_apiurl.clicked.connect(self.defineApiUrl)

    @Slot()
    def quit_application(self):
        QApplication.quit()

    def startdetect(self):
        worker = Worker()
        self.threadpool.start(worker)
        self.logo = QPixmap('acheronlogo_red.png')
        self.label.setPixmap(self.logo)

    def defineApiUrl(self):
        global apiurl
        apiurl = self.edit_apiurl.text()
        print(apiurl)

    def enablePost(self):
        global POST
        if POST == False:
            POST = True

    def enableDetection(self):
        global ENABLEDETECTION
        if ENABLEDETECTION == True:
            ENABLEDETECTION = False
        time.sleep(1)
        ENABLEDETECTION = True
        self.logo = QPixmap('acheronlogo.png')
        self.label.setPixmap(self.logo)

class MainWindow(QMainWindow):
    def __init__(self, widget):
        QMainWindow.__init__(self)
        self.setWindowTitle("Acheron Conduit")
        self.icon = QIcon("icon.png")
        self.setWindowIcon(self.icon)
        # Menu
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")

        # Exit QAction
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_app)

        self.file_menu.addAction(exit_action)
        self.setCentralWidget(widget)

    @Slot()
    def exit_app(self, checked):
        QApplication.quit()

if __name__ == '__main__':
    # Qt Application
    app = QApplication([])
    widget = Widget()
    window = MainWindow(widget)
    window.resize(300, 300)
    window.show()

    # Execute application
    sys.exit(app.exec_())