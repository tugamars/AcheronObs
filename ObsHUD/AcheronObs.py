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

# Globals
health_percentage = 100
maxvalue = 76
pytesseract.pytesseract.tesseract_cmd = r'E:\Program Files\Tesseract-OCR\tesseract.exe'
apiurl="http://localhost:7000/api/123"
# TEAM1 LEFT POSITION VALUES (1920*1080)
player1 = 443+3
player2 = 509+3
player3 = 575+3
player4 = 641+3
player5 = 707+3
# TEAM2 LEFT POSITION VALUES (1920*1080)
player6 = 1168+3
player7 = 1234+3
player8 = 1300+3
player9 = 1366+3
player0 = 1432+3
teamleftScore = 796
teamrightScore = 1087
# SETTINGS
ENABLEDETECTION=True
VERBOSE = False
VERBOSETESSERACT = True
DISPLAY = False
DISPLAYHEALTH = False
DISPLAYSCORE = False
DISPLAYROUNDTIME = False
POST=False
# Starting capture
camera_index = 0

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
        cv2.imshow("lol",frame)
        roundtime = pytesseract.image_to_string(frame, config=custom_config)
        if not roundtime:
            roundtime = "00:00"

    if VERBOSETESSERACT == True:
        print("Round time: " + str(roundtime))

    cv2.imshow("lol2",frame1)
    cv2.waitKey(0)

    return roundtime

    if POST == True:
        postRoundTime(roundtime)

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

    #cv2.imshow("lol5",frame)
    #cv2.waitKey(0)

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

        if DISPLAY == True :
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

def postDetection(pv_player,scoreLeft,scoreRight):
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
            data["team1"]["roundscore"] = str(scoreLeft)
            data["team2"]["roundscore"] = str(scoreRight)

            response = requests.post('http://localhost:7000/api/123', json=data)
            toc2 = time.perf_counter()
            print(f"Total execution time (with POST) : {toc2 - tic:0.4f} seconds")
            print("Status code: ", response.status_code)
    except:
        print("API not responding (Error 3006)")

def postRoundTime(roundtime):
    try:
        with requests.get(apiurl) as api:
            data = api.json()
            data["roundtime"] = str(roundtime)
            response = requests.post('http://localhost:7000/api/123', json=data)
            print("Status code: ", response.status_code)
    except:
        print("API not responding (Error 3006)")

def startDetection(ENABLEDETECTION):
    while ENABLEDETECTION == True:
        tic = time.perf_counter()
        getRoundTimer()
        pv_player = []
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

        toc1 = time.perf_counter()
        print(f"Total execution time : {toc1 - tic:0.4f} seconds")
        if POST == True:
            postDetection(pv_player,scoreLeft,scoreRight)

startDetection(ENABLEDETECTION=True)