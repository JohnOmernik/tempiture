#!/bin/bash
. ./env.list

# Read the env.list and create the env.list.docker to use.
env|sort|grep -P "^APP_" > ./env.list.docker



sudo docker-compose -f ./docker/docker-compose.yml -p tempiture down
