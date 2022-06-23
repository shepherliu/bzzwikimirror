#!/usr/bin/env bash

#build httpserver
cd httpserver

npm install && npm run build 

docker build -t bzzwikimirror/httpserver:latest .

#run docker-compose
echo "y" | docker system prune 
docker-compose down
docker-compose up -d