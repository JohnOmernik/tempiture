#!/usr/bin/python
import time
from datetime import datetime
import threading
from flask import Flask, Response, jsonify
import requests

import os
import math
import sys

import busio
import digitalio
import board

from collections import OrderedDict
import json
import graphyte

# Adafruit Modules
# MCP 3008
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
# Servo Hat
import adafruit_pca9685
from adafruit_motor import servo
#from adafruit_servokit import ServoKit

###############
# Begin ENV Load
try:
    temp_debug = bool(int(os.environ["APP_TEMP_DEBUG"]))
except:
    print("APP_TEMP_DEBUG either not provided or not 0 or 1, defaulting to 0 (false)")
    temp_debug = False
try:
    tmp_spi_clock = os.environ["APP_SPI_CLOCK"]
    spi_clock = eval(tmp_spi_clock)
except:
    print("APP_SPI_CLOCK not provided, using board.SCK")
    spi_clock = eval("board.SCK")
try:
    tmp_spi_miso = os.environ["APP_SPI_MISO"]
    spi_miso = eval(tmp_spi_miso)
except:
    print("APP_SPI_MISO not provided, using board.MISO")
    spi_miso = eval("board.MISO")
try:
    tmp_spi_mosi = os.environ["APP_SPI_MOSI"]
    spi_mosi = eval(tmp_spi_mosi)
except:
    print("APP_SPI_MOSI not provided, using board.MOSI")
    spi_mosi = eval("board.MOSI")
try:
    tmp_spi_cs = os.environ["APP_SPI_CS"]
    spi_cs = eval(tmp_spi_cs)
except:
    print("APP_SPI_CS not provided, using board.CE0")
    spi_cs = eval("board.CE0")

# Begin ENV Load
try:
    gas_debug = bool(int(os.environ["APP_GAS_DEBUG"]))
except:
    print("APP_GAS_DEBUG either not provided or not 0 or 1, defaulting to 0 (false)")
    gas_debug = False
try:
    tmp_servo_hat_clock = os.environ["APP_SERVO_HAT_CLOCK"]
    servo_hat_clock = eval(tmp_servo_hat_clock)
except:
    print("APP_SERVO_HAT_CLOCK not provided, using board.SCL")
    servo_hat_clock = eval("board.SCL")
try:
    tmp_servo_hat_data = os.environ["APP_SERVO_HAT_DATA"]
    servo_hat_data = eval(tmp_servo_hat_data)
except:
    print("APP_SERVO_HAT_CLOCK not provided, using board.SDA")
    servo_hat_data = eval("board.SDA")
try:
    servo_hat_freq = int(os.environ["APP_SERVO_HAT_FREQ"])
except:
    print("APP_SERVO_HAT_FREQ not probided or not valid integer - Defaulting to 200")
    servo_hat_freq = 200
try:
    servo_hat_chan = int(os.environ["APP_SERVO_HAT_CHAN"])
except:
    print("APP_SERVO_HAT_CHAN not provided or not a valid integer - Defaulting to 0")
    servo_hat_chan = 0
try:
    servo_min = int(os.environ["APP_SERVO_MIN"])
except:
    print("APP_SERVO_MIN not prvided using somewhat sane default of 600")
    servo_min = 600
try:
    servo_max = int(os.environ["APP_SERVO_MAX"])
except:
    print("APP_SERVO_MIN not prvided using somewhat sane default of 1305")
    servo_max = 1850


try:
    probe_file = os.environ["APP_PROBE_FILE"]
except:
    print("APP_PROBE_FILE not provided, using /app/data/myprobes.json as default")
    probe_file = "/app/data/myprobes.json"

try:
    NUM_SAMPLES = int(os.environ["APP_NUM_SAMPLES"])
except:
    print("APP_NUM_SAMPLES not provided or not a valid integer - using 100 as default")
    NUM_SAMPLES = 100
try:
    SAMPLE_DELAY = float(os.environ["APP_SAMPLE_DELAY"])
except:
    print("APP_SAMPLE_DELAY not provided or is not a valid number - Using 0.01 as default")
    SAMPLE_DELAY = 0.01
try:
    PROBE_DELAY = float(os.environ["APP_PROBE_DELAY"])
except:
    print("APP_PROBE_DELAY not provided or is not valid number - Using 0.2 as default")
    PROBE_DELAY = 0.2
try:
    READ_DELAY = float(os.environ["APP_READ_DELAY"])
except:
    print("APP_READ_DELAY not provided or is not a valid number - Using 3.0 as default")
    READ_DELAY = 3.0

try:
    LOG_DIR = os.environ["APP_LOG_DIR"]
except:
    print("APP_LOG_DIR not provided - Using /app/data/logs")
    LOG_DIR = "/app/data/logs"

try:
    tempiture_port = int(os.environ["APP_TEMPITURE_PORT"])
except:
    print("APP_TEMPITURE_PORT not provided or not a valid int - Defaulting to 5000")
    tempiture_port = 5000

try:
    log_console = bool(int(os.environ["APP_LOG_CONSOLE"]))
except:
    print("APP_LOG_CONSOLE not provided or not valid int (0 or 1) - Defaulting to 1 (True)")
    log_console = True
try:
    log_graphite = bool(int(os.environ["APP_LOG_GRAPHITE"]))
except:
    print("APP_LOG_GRAPHITE not provided or not valid int (0 or 1) - Defaulting to 0 (False)")
    log_graphite = False
try:
    log_json = bool(int(os.environ["APP_LOG_JSON"]))
except:
    print("APP_LOG_JSON not provided or not valid int (0 or 1) - Defaulting to 1 (True)")
    log_json = True

# Hardware SPI configuration: (Do not Modify)
####################
# create the spi bus
spi = busio.SPI(clock=spi_clock, MISO=spi_miso, MOSI=spi_mosi)
# create the cs (chip select)
cs = digitalio.DigitalInOut(spi_cs)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)
CHANNELS = []

CHANNELS.append(AnalogIn(mcp, MCP.P0))
CHANNELS.append(AnalogIn(mcp, MCP.P1))
CHANNELS.append(AnalogIn(mcp, MCP.P2))
CHANNELS.append(AnalogIn(mcp, MCP.P3))


# Servo Hat Setup
# This assumes you are using the Adafruit 16 channel Raspberry PI Servo Hat and this Servo:
# Servo: https://www.amazon.com/gp/product/B000BOGI7E/
# If you are using something different you may need to rework this stuff

i2c = busio.I2C(servo_hat_clock, servo_hat_data)
hat = adafruit_pca9685.PCA9685(i2c)


i2c = busio.I2C(servo_hat_clock, servo_hat_data)
hat = adafruit_pca9685.PCA9685(i2c)

hat.frequency = servo_hat_freq
GAS_SERVO = servo.Servo(hat.channels[0], min_pulse=servo_min, max_pulse=servo_max)

GAS_SERVO.set_pulse_width_range(servo_min, servo_max)
GAS_SERVO.actuation_range = 100


# Smoking Globals
TEMP_MODE=0
AUTO_PROBES=""
TARGET_MIN = 0
TARGET_MAX = 400
CHAMBER_TARGET = 190.0
CHAMBER_AVG=0.0
GASVAL = 0
SMOKE_NOTES = []
curdate = datetime.today().strftime('%Y-%m-%d')
CURLABEL="Smoke_%s" % curdate  # A Label to tag data in for LAter Analysis
bDebug = True

app = Flask(__name__)
#app.debug = True
app.use_reloader=False
app.debug=False

CURPROBES = ""



if not os.path.isfile(probe_file):
    print("Probe file: %s not found - exiting" % probe_file)
    sys.exit(1)
f = open(probe_file, "rb")
raw_probe = f.read().decode('utf-8')
f.close()
PROBES = json.loads(raw_probe)

if log_graphite:
    gSend = graphyte.Sender('graphite')

FLOG = None


def main():
    global CURPROBES
    global GASVAL
    global CHAMBER_AVG
    global CHAMBER_TARGET
    global FLOG

    print("Init of probe data")
    getSH(0)
    getSH(1)
    getSH(2)
    getSH(3)
    print("")
    print("Setting Gas Level to 0")
    setPerc(0)

    if log_json:
        print("Setting up Logging")
        if not os.path.isdir(LOG_DIR):
            os.mkdir(LOG_DIR)
        curdate = datetime.today().strftime('%Y-%m-%d')
        FLOG = open("%s/temp_readings_%s.json" % (LOG_DIR, curdate), "a")
    tmpprobes = ""
    print("Starting sensing")

    while True:
        chkdate = datetime.today().strftime('%Y-%m-%d')
        if curdate != chkdate and log_json:
            curdate = chkdate
            FLOG.close()
            FLOG = open("%s/temp_readings_%s.json" % (LOG_DIR, curdate), "a")

        print("")
        print("----------------------------")
        CURPROBES = tmpprobes
        tmpprobes = ""
        curEpoch = int(time.time())
        mytime = datetime.fromtimestamp(curEpoch).strftime("%Y-%m-%d %H:%M:%S")
        tmpprobes = "<H1>Probe Readings</H1><BR>Time: %s<BR>" % mytime
        chamber_avg = 0.0
        # Send the Gas Level and current mode once for each probe reading
        myReadings = []
        for x in range(len(PROBES)):
            F, C, K, ADC, R = tempFromADC(x)
            pName = PROBES[x]['name']
            if pName.find("chamber") >= 0:
                chamber_avg += F
            myReadings.append({"probe": x, "probe_name": pName, "adc_value": ADC, "resistance": R, "tempF": F, "tempC": C, "tempK": K})

        chamber_avg = chamber_avg / 2
        CHAMBER_AVG = chamber_avg

        jsonRec = OrderedDict()
        tmpLog = {}
        jsonRec['ts'] = curEpoch
        jsonRec['smoke_label'] = CURLABEL
        jsonRec['gas_level'] = GASVAL
        jsonRec['gas_mode'] = TEMP_MODE
        jsonRec['chamber_avg'] = CHAMBER_AVG
        jsonRec['chamber_target'] = CHAMBER_TARGET
        tmpLog["data.gas.level"] = GASVAL
        tmpLog["data.gas.mode"] = TEMP_MODE
        tmpLog['data.chamber_avg.temperature'] = CHAMBER_AVG
        tmpLog['data.chamber_avg.target'] = CHAMBER_TARGET
        if TEMP_MODE == 0:
            strmode = "Manual"
        else:
            strmode = "Auto"
        tmpprobes = tmpprobes + "Smoke Label: %s<BR>Epoch Time: %s<BR>Gas Value: %s<BR>Gas Mode: %s<BR>Chamber Average: %s<BR>Chamber Target: %s<BR>" % (CURLABEL, curEpoch, GASVAL, strmode, CHAMBER_AVG, CHAMBER_TARGET)

        for x in myReadings:
            pName = x['probe_name']
            tmpLog["data.%s.adc_value" % pName] = x['adc_value']
            tmpLog["data.%s.resistance" % pName] = x['resistance']
            tmpLog["data.%s.temperature" % pName] = x['tempF']
            jsonRec["%s_adc_value" % pName] = x['adc_value']
            jsonRec["%s_resistance" % pName] = x['resistance']
            jsonRec["%s_tempF" % pName] = x['tempF']
            jsonRec["%s_tempC" % pName] = x['tempC']
            jsonRec["%s_tempK" % pName] = x['tempK']
            tmpprobes = tmpprobes + "Probe Number: %s - %s: TempF: %s ADC: %s Res: %s<BR>" % (x['probe'], pName, x['tempF'], x['adc_value'], x['resistance'])

        CURPROBES = tmpprobes
      # Log to Graphyte
        if log_graphite:
            print("Sending to Graphite")
            for y in tmpLog.keys():
                gSend.send(y, tmpLog[y], curEpoch)
      # Log to file
        if log_json:
            strjson = json.dumps(jsonRec)
            FLOG.write(strjson + "\n")
            FLOG.flush()
        if log_console:
            strOut = tmpprobes.replace("<H1>", "").replace("</H1>", "").replace("<BR>", "\n")
            print(strOut)

            time.sleep(PROBE_DELAY)
        time.sleep(READ_DELAY)

@app.route('/current', methods=['GET'])
def current():
    return CURPROBES, 200

@app.route('/getlabel', methods=['GET'])
def getlabel():
    retmsg = "<BR><CENTER><H1 style=\"color:white\">" + CURLABEL + "</H1></CENTER>"
    return retmsg, 200

@app.route('/setlabel/<newlabel>', methods=['GET'])
def setlabel(newlabel):
    global CURLABEL
    CURLABEL = newlabel
    return CURLABEL, 200

@app.route('/getnotes', methods=['GET'])
def getnotes():
    notecnt = 10
    retmsg = "<TABLE style=\"color:white\"><TR><TD width=\"200\">Time</TD><TD width=\"200\">Label</TD><TD>Note</TD></TR>\n"
    curcnt = 0
    for note in SMOKE_NOTES[::-1]:
        retmsg = retmsg + "<TR><TD>%s</TD><TD>%s</TD><TD>%s</TD></TR>\n" % (note['ts'], note['label'], note['note'])
        curcnt += 1
        if curcnt >= notecnt:
            break
    retmsg = retmsg + "</TABLE>"
    return retmsg, 200

@app.route('/savenote/<note>', methods=['GET'])
def savenote(note):
    global SMOKE_NOTES

    anEpoch = int(time.time())
    aTime = datetime.fromtimestamp(anEpoch).strftime("%Y-%m-%d %H:%M:%S")
    aLabel = CURLABEL
    sn = OrderedDict()
    sn['epoch'] = anEpoch
    sn['ts'] = aTime
    sn['label'] = aLabel
    sn['note'] = note

    SMOKE_NOTES.append(sn)

    if log_json:
        strjson = json.dumps(sn)
        FLOG.write(strjson + "\n")
        FLOG.flush()

    return "OK", 200

@app.route('/getgas', methods=['GET'])
def getgas():
    return jsonify(gasval=GASVAL), 200

@app.route('/movetarget/<value>', methods=['GET'])
def movetarget(value):
    global CHAMBER_TARGET
    try:
        myval = int(value)
    except:
        retmsg = "Non Valid Number, must be integer"
        return retmsg, 500
    tvalue = CHAMBER_TARGET + myval
    if tvalue < TARGET_MIN:
        tvalue = TARGET_MIN
    elif tvalue > TARGET_MAX:
        tvalue = TARGET_MAX
    CHAMBER_TARGET = tvalue
    retmsg = "CHAMBER TARGET moved %s to %s" % (myval, CHAMBER_TARGET)
    return retmsg, 200

@app.route('/setauto', methods=['GET'])
def setauto():
    global TEMP_MODE
    if TEMP_MODE != 1:
        TEMP_MODE = 1
    return "ok", 200

@app.route('/movegas/<value>', methods=['GET'])
def movegas(value):
    global TEMP_MODE
    if TEMP_MODE != 0: # We setting the gas manually, thus if we are in Auto Mode, move to Manual
        TEMP_MODE = 0
    try:
        myval = int(value)
    except:
        retmsg = "Non valid number, must be integer between -100 and 100"
        return retmsg, 500
    tvalue = GASVAL + myval
    if tvalue < 0:
        tvalue = 0
    elif tvalue > 100:
        tvalue = 100
    setPerc(tvalue)
    retmsg = "Setting to %s" % tvalue
    return retmsg, 200

@app.route('/settarget/<value>', methods=['GET'])
def settarget(value):
    global CHAMBER_TARGET
    try:
        myval = int(value)
    except:
        retmsg = "Non valid Target temp, must be int number between %s and %s" % (TARGET_MIN, TARGET_MAX)
        return retmsg, 500
    if myval >= TARGET_MIN and myval <= TARGET_MAX:
        CHAMBER_TARGET = myval
        retmsg = "Chamber target set to %s" % myval
        retcode = 200
    else:
        retmsg = "Target temp must be an int between %s and % - Not setting" % (TARGET_MIN, TARGET_MAX)
        retcode = 500
    return retmsg, retcode

@app.route('/setgas/<perc>', methods=['GET'])
def setgas(perc):
    global TEMP_MODE
    if TEMP_MODE != 0: # We setting the gas manually, thus if we are in Auto Mode, move to Manual
        TEMP_MODE = 0
    try:
        myval = int(perc)
    except:
        retmsg = "Non valid number, must be integer between 0 and 100"
        return retmsg, 500
    if myval >= 0 and myval <= 100:
        setPerc(myval)
        retmsg = "Setting to %s" % myval
        retcode = 200
    else:
        retmsg = "Non valid number, must be into between 0 and 100"
        retcode = 500

    return retmsg, retcode




########################## Servo setting functions
def setPerc(setPerc):
    global GASVAL
    global GAS_SERVO
    #setVal = (setPerc * (SRVMAX - SRVMIN) / 100) + SRVMIN
    GASVAL = setPerc
    GAS_SERVO.angle = setPerc
    if setPerc <= 3 or setPerc >= 97:
        # If things are near the boundarys, set a release
        time.sleep(4)
        GAS_SERVO.angle = None

########################### The following are probe functions

def getSH(probe):
    probeRead = avgReadings(PROBES[probe]['readings'])
    for y in probeRead:
        y['R'] = getR(y['value'])
    if temp_debug:
        print("")
        print("--------------------")
        print("Average readings for probe %s: " % probe)
        print(probeRead)
        print("")
    L1 = math.log(probeRead[0]['R'])
    L2 = math.log(probeRead[1]['R'])
    L3 = math.log(probeRead[2]['R'])
    Y1 = 1 / probeRead[0]['tempK']
    Y2 = 1 / probeRead[1]['tempK']
    Y3 = 1 / probeRead[2]['tempK']
    gma2 = (Y2-Y1)/(L2-L1)
    gma3 = (Y3-Y1)/(L3-L1)

    C = ( (gma3-gma2) / (L3-L2)) * math.pow((L1+L2+L3), -1)
    B = gma2 - C * ( math.pow(L1, 2) + L1 * L2 + math.pow(L2, 2) )
    A = Y1 - (B + math.pow(L1, 2) * C) * L1
    PROBES[probe]['A'] = A
    PROBES[probe]['B'] = B
    PROBES[probe]['C'] = C
    if temp_debug:
        print("Probe %s" % probe)
        print("A: %s" % A)
        print("B: %s" % B)
        print("C: %s" % C)

def tempFromADC(probe):
    global CHANNELS
    adc_readings = []
    for x in range(NUM_SAMPLES):
        #adc = mcp.read_adc(probe)
        adc = CHANNELS[probe].value
        adc_readings.append(adc)
        time.sleep(SAMPLE_DELAY)
    avg_adc = sum(adc_readings) / NUM_SAMPLES
    curR = getR(avg_adc)
    retTempK = tempKFromR(curR, probe)
    retTempC = K2C(retTempK)
    retTempF = C2F(retTempC)
    return round(retTempF, 2), round(retTempC, 2), round(retTempK, 2), round(avg_adc, 2), round(curR, 2)

def tempKFromR(R, probe):
    A = PROBES[probe]['A']
    B = PROBES[probe]['B']
    C = PROBES[probe]['C']

    tmpOut = 1 / ( A + B * math.log(R) + C * math.pow(math.log(R), 3) )
    return tmpOut


def K2C(tempK):
    tempC = tempK - 273.15
    tempC = round(tempC*10, 2) / 10
    return tempC

def C2F(tempC):
    tempF = (tempC * 1.8) + 32
    tempF = round(tempF * 10, 2) /10
    return tempF
def avgReadings(readings):
    tmpRead = {}
    outRead = []

    for x in readings:
        if x['temp'] in tmpRead:
            tmpRead[x['temp']].append(x['value'])
        else:
            tmpRead[x['temp']] = [x['value']]
    for y in tmpRead.keys():
        t = {'tempF': y, 'tempK': F2K(y), 'value': sum(tmpRead[y]) / len(tmpRead[y])}
        outRead.append(t)
    return outRead


def F2K(F): 
    return 273.5 + ((F - 32.0) * (5.0/9.0))


def getR(adc):
#    adc_bit = 1023.0 # Original Python2 Adafruit MCP 3008 library
    adc_bit = 65535.0 # Circuit Python Python3 Adafruit MCP 3008 Library

    myadc = adc * 1.0
    DROP_R = 100000
    out_R = DROP_R / (( adc_bit / myadc) - 1)
    return out_R

#def getR(adc):
#    return adc

if __name__ == "__main__":
    print("Starting Main Loop")
    thread = threading.Thread(target=main)
    thread.start()
  # Starting Server
    print("Starting Webserver")
    app.run(host="0.0.0.0", port=tempiture_port)
