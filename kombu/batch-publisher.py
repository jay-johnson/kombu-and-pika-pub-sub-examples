#!/usr/bin/env python


import os
import datetime
from kombu import Connection
from kombu import Exchange
from kombu import Queue
from kombu import Producer


auth_url = os.getenv(
    "BROKER_URL",
    "amqp://rabbitmq:rabbitmq@localhost:5672/")
transport_options = {}

print("getting connection")
connection = Connection(
    auth_url,
    heartbeat=60,
    transport_options=transport_options)

# noqa http://docs.celeryproject.org/projects/kombu/en/latest/userguide/producers.html
print("getting channel")
channel = connection.channel()

exchange_type = "topic"
exchange = Exchange(
    "east-coast",
    type=exchange_type,
    durable=True)

print("creating producer")
producer = Producer(
    channel=channel,
    auto_declare=True,
    serializer="json")

print("declaring producer")
producer.declare()

print(("declaring exchange={}")
      .format(
        exchange.name))

# noqa http://docs.celeryproject.org/projects/kombu/en/latest/reference/kombu.html#queue
queues = [
    Queue(
        "us.east.charlotte",
        exchange,
        routing_key="us.east.charlotte",
        durable=True),
    Queue(
        "us.east.newyork",
        exchange,
        routing_key="us.east.newyork",
        durable=False)
]

NOT_PERSISTENT = 1
PERSISTENT = 2

messages = [
    {
        "routing_key": queues[0].routing_key,
        "delivery_mode": PERSISTENT,
        "body": ("Kombu sent a Persistent Message - 1 - {}").format(
            datetime.datetime.now().strftime(
                "%Y-%m-%d-%H-%M-%S"))
    },
    {
        "routing_key": queues[1].routing_key,
        "delivery_mode": PERSISTENT,
        "body": ("Kombu sent a Persistent Message - 2 - {}").format(
            datetime.datetime.now().strftime(
                "%Y-%m-%d-%H-%M-%S"))
    },
    {
        "routing_key": queues[0].routing_key,
        "delivery_mode": NOT_PERSISTENT,
        "body": ("Kombu sent a NOT-Persistent - {} "
                 "Message - 3 - {}").format(
            queues[0].name,
            datetime.datetime.now().strftime(
                "%Y-%m-%d-%H-%M-%S"))
    },
    {
        "routing_key": queues[1].routing_key,
        "delivery_mode": NOT_PERSISTENT,
        "body": ("Kombu sent a NOT-Persistent - {} "
                 "Message - 4 - {}").format(
            queues[1].name,
            datetime.datetime.now().strftime(
                "%Y-%m-%d-%H-%M-%S"))
    }
]


for qidx, queue_obj in enumerate(queues):

    try:
        queue_name = queue_obj.name
        durable = queue_obj.durable

        print(("binding queue={} ex={}->{} queue={}")
              .format(
                (qidx + 1),
                exchange.name,
                exchange_type,
                queue_name))
        queue_obj.maybe_bind(connection)
        queue_obj.declare()

    except Exception as e:
        print(("failed creating queue={} queue_declare queue={} hit ex={}")
              .format(
                qidx,
                queue_name,
                e))
    # end of try/ex
# for all queues

num_msgs = 0
num_batch = 100
for bidx in range(0, num_batch):
    for midx, msg_node in enumerate(messages):

        body = msg_node["body"]
        routing_key = msg_node["routing_key"]
        delivery_mode = msg_node["delivery_mode"]

        print(("batch={} publishing={} exchange={} routing_key={} "
               "persist={} msg={}")
              .format(
                (bidx + 1),
                (midx + 1),
                exchange.name,
                routing_key,
                delivery_mode,
                body))
        producer.publish(
            body=body,
            exchange=exchange.name,
            routing_key=routing_key,
            auto_declare=True,
            serializer="json",
            delivery_mode=delivery_mode)
        num_msgs += 1
    # end of for all messages
# end for all batches

print(("done sending batches={} total_messages={}")
      .format(
        num_batch,
        num_msgs))

print("shutting down")
connection.close()
