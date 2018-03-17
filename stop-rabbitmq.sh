#!/bin/bash

echo ""
echo "Stopping RabbitMQ"
echo ""
docker-compose -f rabbitmq.yml stop
echo ""
docker rm rabbit >> /dev/null 2>&1
docker ps
