#!/bin/bash

echo ""
echo "Starting RabbitMQ"
echo ""
docker-compose -f rabbitmq.yml up -d
echo ""
docker ps
