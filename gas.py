#!/usr/bin/python3

# Import the PCA9685 module.
import time
import sys
import json
# Initialise the PCA9685 using the default address (0x40).
#from adafruit_servokit import ServoKit
#from adafuit_motor import servo
from adafruit_motor import servo
import os
import board
import busio
import adafruit_pca9685

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
    servo_max = 1305

#### END ENV Load

i2c = busio.I2C(servo_hat_clock, servo_hat_data)
hat = adafruit_pca9685.PCA9685(i2c)

hat.frequency = servo_hat_freq
GAS_SERVO = servo.Servo(hat.channels[0], min_pulse=servo_min, max_pulse=servo_max)

#kit = ServoKit(channels=16)
#GAS_SERVO.set_pulse_width_range(servo_min, servo_max)
#GAS_SERVO.actuation_range = 100

def main():
    cur_perc = 0
    initial_min = servo_min
    initial_max = servo_max
    cur_min = servo_min
    cur_max = servo_max
    GAS_SERVO.set_pulse_width_range(cur_min, cur_max)
    while True:
        print("Current min_pulse: %s - Current max_pulse: %s" % (cur_min, cur_max))
        tval = input("Set percentage, u to set max pulse, d to set min pulse, or q to quit (Currently: %s Percent): " % cur_perc)
        if tval == "q":
            print("Quiting, have a nice day!")
            GAS_SERVO.angle = None
            time.sleep(1)
            sys.exit(0)
        elif tval == "u" or tval == "d":
            if tval == "u":
                sval = "max"
            else:
                sval = "min"

            pval = input("Set %s pulse value: " % sval)
            try:
                pval = int(pval)
            except:
                print("Value must be integer")
                continue
            if tval == "u":
                cur_max = pval
            else:
                cur_min = pval
            GAS_SERVO.set_pulse_width_range(cur_min, cur_max)
        else:
            try:
                myval = int(tval)
            except:
                print("Non int value sent")
                continue
            cur_perc = myval
            GAS_SERVO.angle = myval
            if myval <= 2 or myval >= 98:
                time.sleep(4)
                GAS_SERVO.angle = None
if __name__ == "__main__":
    main()
