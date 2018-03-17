#!/usr/bin/env python


import os
import time
import socket
from kombu import Connection
from kombu import Exchange
from kombu import Queue
from kombu import Consumer


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

for qidx, queue_obj in enumerate(queues):

    try:
        queue_name = queue_obj.name
        durable = queue_obj.durable

        print(("binding queue={} ex={}->{} queue={}")
              .format(
                qidx,
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


def handle_message(
        body,
        message):
    """handle_message

    :param body: contents of the message
    :param message: message object
    """
    print(("callback received msg routing_key={} "
           "body={}")
          .format(
            message.delivery_info["routing_key"],
            body))
    message.ack()
# end of handle_message


print("creating consumer")
consumer = Consumer(
    connection,
    queues=queues,
    auto_declare=True,
    callbacks=[handle_message],
    accept=["json"])

not_done = True
time_to_wait = 0.1
while not_done:
    not_done = True
    try:
        consumer.consume()
        connection.drain_events(
            timeout=time_to_wait)
        success = True
    except socket.timeout as t:
        connection.heartbeat_check()
        time.sleep(0.1)
# while not done consuming

print("shutting down")
connection.close()
