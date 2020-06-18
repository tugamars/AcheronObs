import cv2
import numpy as np
import time
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
ultimate_status = []
team1side = "defense"
team2side = "attack"
pytesseract.pytesseract.tesseract_cmd = r'E:\Program Files\Tesseract-OCR\tesseract.exe'
apiurl = 'http://localhost:6543/api/123'
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

template = cv2.imread('spiketemplate.png', cv2.IMREAD_UNCHANGED)
template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

try:
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
except:
    print("Something went wrong with the capture (Error 3003)")

def cleanFrameRed(frame):
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
    frame = cv2.medianBlur(frame,5)
    frame = cv2.threshold(frame, 15, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((5,5),np.uint8)
    frame = cv2.dilate(frame, kernel, iterations = 2)
    frame = cv2.erode(frame, kernel, iterations = 2)
    frame = cv2.morphologyEx(frame, cv2.MORPH_OPEN, kernel)
    #frame = cv2.Canny(frame, 100, 200)

    return frame

def cleanFrameWhite(frame):
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
    frame = cv2.medianBlur(frame,5)
    frame = cv2.threshold(frame, 200, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((4,4),np.uint8)
    frame = cv2.dilate(frame, kernel, iterations = 2)
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

def grabUltimateBar(left):
    width  = 40
    height = 6
    startY = 20
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

def grabSpikeStatus():
    width = 89
    height = 80
    startY = 15
    left = 916
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

def oldgetRoundTimer():
    frame = grabRoundTimer()
    framecleanwhite = cleanFrameWhite(frame)
    framecleanred = cleanFrameRed(frame)

    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789:." '
    roundtime = pytesseract.image_to_string(framecleanwhite, config=custom_config)
    print("Round time framecleanwhite : " + str(roundtime))
    if not roundtime:
        roundtime = pytesseract.image_to_string(framecleanred, config=custom_config)
        print("Round time framecleanred : " + str(roundtime))
        if not roundtime:
            roundtime = "SPIKE PLANTED"

    if VERBOSETESSERACT == True:
        print("Round time: " + str(roundtime))

    if DISPLAYROUNDTIME == True :
        cv2.imshow(str("Round Time"),framecleanwhite)
        cv2.imshow(str("Round Time 2"),framecleanred)
        cv2.waitKey(0)

    return roundtime

def getSpikeStatus():
    image = grabSpikeStatus()
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    w, h = template.shape[::-1]
    method = cv2.TM_CCOEFF_NORMED
    res = cv2.matchTemplate(image, template, method)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    max_val_ncc = '{:.3f}'.format(max_val)
    Flag = False
    if float(max_val_ncc) > 0.6:
        Flag = True

    return Flag

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
        cv2.imshow(str("Score"),frame)
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

def getUltimateStatus(playerultimate):
    ultimateBar = grabUltimateBar(playerultimate)
    ultimate_Bar = getBuffer(ultimateBar)
    ultimate_Bar = cv2.cvtColor(ultimate_Bar, cv2.COLOR_BGR2GRAY)

    ultpixels = ultimate_Bar.reshape(-1,1)
    pv = 0
    ultimatestatus = False

    for ultpixel in ultpixels:
        if ultpixel[0] >= 90:
           pv += 1
           if pv >= 20:
            ultimatestatus = True
            
    if DISPLAYSCORE == True :
        dim = (400, 60)
        ultimate_Bar = cv2.resize(ultimate_Bar, dim, interpolation = cv2.INTER_AREA)
        cv2.imshow(str("Ultimate"),ultimate_Bar)
        cv2.waitKey(0)

    return ultimatestatus

def fixHalfTime(scoreLeft,scoreRight):
    if int(scoreLeft) + int(scoreRight) >= 12:
        scoreLeft, scoreRight = scoreRight, scoreLeft

    return scoreLeft,scoreRight

def getSide(scoreLeft,scoreRight):
    global team1side, team2side
    if int(scoreLeft) + int(scoreRight) >= 12:
        team1side = "attack"
        team2side = "defense"
    else:
        team1side = "defense"
        team2side = "attack"
    return team1side,team2side

def postHealthDetection(pv_player):
    try:
        with requests.get(apiurl) as api:
            data = api.json()
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

            response = requests.post(apiurl, json=data)
            print("Status code: ", response.status_code)
    except:
        print("API not responding (Error 3006) [Health Detection Thread]")

def postTextDetection(scoreLeft,scoreRight,spikeStatus,team1side,team2side):
    try:
        with requests.get(apiurl) as api:
            data = api.json()
            data["roundtime"] = str(spikeStatus)
            data["team1"]["roundscore"] = str(scoreLeft)
            data["team2"]["roundscore"] = str(scoreRight)
            data["team1"]["side"] = team1side
            data["team2"]["side"] = team2side

            response = requests.post(apiurl, json=data)
            print("Status code: ", response.status_code)
    except:
        print("API not responding (Error 3006) [Text Detection Thread]")

def postUltimateDetection(ultimate_status):
    try:
        with requests.get(apiurl) as api:
            data = api.json()
            data["team1"]["players"][0]["ult"] = str(ultimate_status[0])
            data["team1"]["players"][1]["ult"] = str(ultimate_status[1])
            data["team1"]["players"][2]["ult"] = str(ultimate_status[2])
            data["team1"]["players"][3]["ult"] = str(ultimate_status[3])
            data["team1"]["players"][4]["ult"] = str(ultimate_status[4])
            data["team2"]["players"][0]["ult"] = str(ultimate_status[5])
            data["team2"]["players"][1]["ult"] = str(ultimate_status[6])
            data["team2"]["players"][2]["ult"] = str(ultimate_status[7])
            data["team2"]["players"][3]["ult"] = str(ultimate_status[8])
            data["team2"]["players"][4]["ult"] = str(ultimate_status[9])

            response = requests.post(apiurl, json=data)
            print("Status code: ", response.status_code)
    except:
        print("API not responding (Error 3006) [Ultimate Detection Thread]")

def textDetection():
    while ENABLEDETECTION == True:

        spikeStatus = getSpikeStatus()
        scoreLeft = getScore(teamleftScore)
        scoreRight = getScore(teamrightScore)
        getSide(scoreLeft,scoreRight)

        if POST == True:
            postTextDetection(scoreLeft,scoreRight,spikeStatus,team1side,team2side)

def healthDetection():

    global pv_player
    while ENABLEDETECTION == True:
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

        if POST == True:
            postHealthDetection(pv_player)
        # Reseting list to avoid memory leak
        pv_player = []

def ultimateDetection():
    global ultimate_status
    while ENABLEDETECTION == True:

        ultimate_status.append(getUltimateStatus(player1))
        ultimate_status.append(getUltimateStatus(player2))
        ultimate_status.append(getUltimateStatus(player3))
        ultimate_status.append(getUltimateStatus(player4))
        ultimate_status.append(getUltimateStatus(player5))
        ultimate_status.append(getUltimateStatus(player6))
        ultimate_status.append(getUltimateStatus(player7))
        ultimate_status.append(getUltimateStatus(player8))
        ultimate_status.append(getUltimateStatus(player9))
        ultimate_status.append(getUltimateStatus(player0))

        if POST == True:
            postUltimateDetection(ultimate_status)
        # Reseting list to avoid memory leak
        ultimate_status = []

class healthWorker(QRunnable):
    @Slot()
    def run(self):
        healthDetection()

class textWorker(QRunnable):
    @Slot()
    def run(self):
        textDetection()

class ultimateWorker(QRunnable):
    @Slot()
    def run(self):
        ultimateDetection()

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
        self.edit_apiurl = QLineEdit("http://localhost/api/123")
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
        textworker = textWorker()
        healthworker = healthWorker()
        ultworker = ultimateWorker()
        self.threadpool.start(healthworker)
        self.threadpool.start(textworker)
        self.threadpool.start(ultworker)
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