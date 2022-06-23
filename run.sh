#!/usr/bin/env bash
echo "y" | docker system prune 

docker-compose down
docker-compose up -d