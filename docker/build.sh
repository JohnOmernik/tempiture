#!/bin/bash
. ../env.list


# COPY current code for build
cp ../*.py ./
sudo docker build -t $APP_IMG .
rm ./*.py
