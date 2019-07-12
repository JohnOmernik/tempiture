#!/bin/bash
. ./env.list

#APP_CMD="/bin/bash"
export APP_CMD="python3 /app/calibration.py"
export APP_VOLS="-v=/home/pi/tempiture/data:/app/data:rw"

# Read the env.list and create the env.list.docker to use.
env|sort|grep -P "^APP_" > ./env.list.docker


sudo docker run --privileged --device /dev/spidev0.0 --device /dev/spidev0.1 --device /dev/mem  --device /dev/i2c-1 --env-file ./env.list.docker -it $APP_VOLS $APP_IMG $APP_CMD







