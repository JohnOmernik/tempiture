# Basic Image for Python 3
FROM raspbian/stretch

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y git python3 python3-pip python3-setuptools build-essential gcc python-smbus i2c-tools
RUN pip3 install --upgrade setuptools
RUN pip3 install RPI.GPIO
RUN pip3 install adafruit-blinka
RUN pip3 install adafruit-circuitpython-lis3dh
RUN pip3 install adafruit-circuitpython-mcp3xxx
RUN pip3 install adafruit-circuitpython-servokit
RUN pip3 install requests
RUN pip3 install graphyte
RUN pip3 install flask
RUN mkdir /app
RUN pip3 install git+https://github.com/adafruit/Adafruit_CircuitPython_Motor#egg=adafruit_motor
#RUN git clone https://github.com/adafruit/Adafruit_CircuitPython_Motor && cd Adafruit_CircuitPython_Motor && python3 setup.py install && cd .. 
COPY ./calibration.py /app/
COPY ./gas.py /app/
COPY ./tempiture.py /app/
CMD ["/bin/sh"]
