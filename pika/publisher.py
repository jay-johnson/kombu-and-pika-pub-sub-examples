#!/usr/bin/env python


import os
import sys
import json
import datetime
import pika


auth_url = os.getenv(
    "BROKER_URL",
    "amqp://rabbitmq:rabbitmq@localhost:5672/")

print("building parameters")
params = pika.URLParameters(auth_url)
print("building blocking connection")
connection = pika.BlockingConnection(
    params)

# https://pika.readthedocs.io/en/0.11.2/modules/channel.html
print("getting channel")
channel = connection.channel()

exchange_name = "east-coast"
exchange_type = "topic"
queues = [
    {
        "name": "us.east.charlotte",
        "routing_key": "us.east.charlotte",
        "durable": True
    },
    {
        "name": "us.east.newyork",
        "routing_key": "us.east.newyork",
        "durable": False
    }
]

NOT_PERSISTENT = 1
PERSISTENT = 2

messages = [
    {
        "routing_key": queues[0]["routing_key"],
        "delivery_mode": PERSISTENT,
        "body": {
            "value": ("Pika sent a Persistent Message - 1 - {}").format(
                datetime.datetime.now().strftime(
                    "%Y-%m-%d-%H-%M-%S"))}
    },
    {
        "routing_key": queues[1]["routing_key"],
        "delivery_mode": PERSISTENT,
        "body": {
            "value": ("Pika sent a Persistent Message - 2 - {}").format(
                datetime.datetime.now().strftime(
                    "%Y-%m-%d-%H-%M-%S"))}
    },
    {
        "routing_key": queues[0]["routing_key"],
        "delivery_mode": NOT_PERSISTENT,
        "body": {
            "value": ("Pika sent a NOT-Persistent - {} "
                      "Message - 3 - {}").format(
                queues[0]["name"],
                datetime.datetime.now().strftime(
                    "%Y-%m-%d-%H-%M-%S"))}
    },
    {
        "routing_key": queues[1]["routing_key"],
        "delivery_mode": NOT_PERSISTENT,
        "body": {
            "value": ("Pika sent a NOT-Persistent - {} "
                      "Message - 4 - {}").format(
                queues[1]["name"],
                datetime.datetime.now().strftime(
                    "%Y-%m-%d-%H-%M-%S"))}
    }
]

try:
    print(("creating exchange={}")
          .format(
            exchange_name))
    channel.exchange_declare(
        exchange=exchange_name,
        exchange_type=exchange_type,
        durable=True)
except Exception as e:
    print(("exchange_declare exchange={} hit ex={}")
          .format(
            exchange_name,
            e))
    sys.exit(1)
# end of try/ex

for qidx, queue_node in enumerate(queues):

    queue_name = queue_node["name"]
    durable = queue_node["durable"]
    routing_key = queue_node["routing_key"]

    try:
        print(("creating queue={} queue={}")
              .format(
                (qidx + 1),
                queue_name))
        result = channel.queue_declare(
            queue=queue_name,
            durable=durable)
        print(("binding queue={} ex={}->{} queue={}")
              .format(
                (qidx + 1),
                exchange_name,
                exchange_type,
                queue_name))
        channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name,
            routing_key=routing_key)
    except Exception as e:
        print(("failed creating queue={} queue_declare queue={} hit ex={}")
              .format(
                (qidx + 1),
                queue_name,
                e))
    # end of try/ex
# for all queues

for midx, msg_node in enumerate(messages):

    body = msg_node["body"]
    routing_key = msg_node["routing_key"]
    delivery_mode = msg_node["delivery_mode"]

    persistence_props = pika.BasicProperties(
        content_type="application/json",
        delivery_mode=delivery_mode)

    print(("publishing={} exchange={} routing_key={} persist={} msg={}")
          .format(
            (midx + 1),
            exchange_name,
            routing_key,
            delivery_mode,
            body))
    channel.basic_publish(
        exchange=exchange_name,
        routing_key=routing_key,
        body=json.dumps(body),
        properties=persistence_props)
# end of for all messages

print("shutting down")
connection.close()
