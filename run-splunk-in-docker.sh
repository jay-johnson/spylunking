#!/bin/bash

# docker run -d -e "SPLUNK_START_ARGS=--accept-license" -e "SPLUNK_USER=root" -p "11000:8000" splunk/splunk
docker stop splunk >> /dev/null 2>&1
docker rm splunk >> /dev/null 2>&1
echo "Starting docker container"
docker-compose -f docker-compose.yml up -d
