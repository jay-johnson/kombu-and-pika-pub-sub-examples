#!/usr/bin/env python


import os
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

queues = [
    {
        "name": "us.east.charlotte",
        "durable": True
    },
    {
        "name": "us.east.newyork",
        "durable": False
    }
]


def handle_message(
        channel,
        method_frame,
        header_frame,
        body):
    """
    handle_message

    :param channel: pika channel
    :param method_frame: message object
    :param header_frame: header object
    :param body: message contents
    """
    print(("{} - Blocked Pika - consumed message delivery_tag={} "
           "delivery_mode={} body={}")
          .format(
            datetime.datetime.now().strftime(
                "%Y-%m-%d %H-%M-%S"),
            method_frame.delivery_tag,
            header_frame.delivery_mode,
            body.decode("utf-8")))
    channel.basic_ack(method_frame.delivery_tag)
# end of on_message


all_queues = []
for queue_node in queues:
    print(("starting basic_consume queue={}")
          .format(
            queue_node["name"]))

    channel.basic_consume(
        handle_message,
        queue=queue_node["name"])
    all_queues.append(
        queue_node["name"])
# for all queues to consume

try:
    print(("starting channel consume queues={}")
          .format(
            all_queues))
    channel.start_consuming()
except Exception as e:
    print(("stopping consuming with ex={}")
          .format(
            e))
    if channel:
        channel.stop_consuming()
# end try/ex

print("shutting down")
channel.close()
connection.close()
