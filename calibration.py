#!/usr/bin/python3
import time
import sys
import json
import os
import busio
import digitalio
import board
import shutil

import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

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
####################

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

# Load Probe data - If no probe data file already exists, copy a template
if not os.path.isfile(probe_file):
    if os.path.isfile("/app/data/myprobes.json.template"):
        shutil.copyfile("/app/data/myprobes.json.template", probe_file)
    else:
        print("No probe_file found at %s and no template found at /app/data/myprobes.json.template - exiting" % probe_file)
        sys.exit(1)

f = open(probe_file, "rb")
raw_probe = f.read().decode('utf-8')
f.close()
print(raw_probe)
PROBES = json.loads(raw_probe)

def main():
    global CHANNELS
    curProbe = ""
    print("This script helps to create an output file called myprobes.json. This process will ensure you get good readings from the temp probes")
    while curProbe != "q":
        curProbe = input("Please enter the probe number to gather readings from (q to output, save, and quit): ")
        if curProbe == "q":
            myOut = json.dumps(PROBES, sort_keys=True, indent=4)
            for x in PROBES:
                print(x)
            print("")
            print(myOut)
            f = open(probe_file, "w")
            f.write(myOut)
            f.close()
            sys.exit(0)
        try:
            curProbe = int(curProbe)
            curName = PROBES[curProbe]['name']
        except:
            print("Probe number %s doesn't exist in probes: Try again")
            continue
        print("")
        print("----------------")
        print("Gathering readings for probe %s (%s)" % (curProbe, curName))
        print("Please enter the temp for the reading (n to get new reading without temp, q to save and quit getting readings for this probe)")
        curReadings = []
        curTemp = ""
        while curTemp != "q":
            myreads = []
            myvolts = []
            for x in range(NUM_SAMPLES):
                myreads.append(CHANNELS[curProbe].value)
                myvolts.append(CHANNELS[curProbe].voltage)
                time.sleep(SAMPLE_DELAY)
            curReading = sum(myreads) / NUM_SAMPLES
            curVolts = sum(myvolts) / NUM_SAMPLES
            curTemp = input("Current Reading from %s is %s (%s volts): Please enter Temp (or n or q): " % (curProbe,curReading, curVolts))
            if curTemp == "n":
                print("Discarding current reading and getting new reading")
                continue
            elif curTemp == "q":
                print("Saving current readings")
                PROBES[curProbe]["readings"] = PROBES[curProbe]["readings"] + curReadings
            else:
                try:
                    fltTemp = float(curTemp)
                    curReadings.append({"value": curReading, "temp": fltTemp})
                except:
                    print("Current temp provided is not an number, skipping and getting a new reading")
                    continue
 
if __name__ == "__main__":
    main()

