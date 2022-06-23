#!/usr/bin/env bash

currentPath=$(pwd)

#build trigger
cd $currentPath
cd trigger

docker build -t bzzwikimirror/trigger:latest .

#build downloader
cd $currentPath
cd downloader

docker build -t bzzwikimirror/downloader:latest .

#build extractor
cd $currentPath
cd extractor

docker build -t bzzwikimirror/extractor:latest .

#build uploader
cd $currentPath
cd uploader

docker build -t bzzwikimirror/uploader:latest .

#run docker-compose
cd $currentPath

echo "y" | docker system prune 
docker-compose down
docker-compose up -d
