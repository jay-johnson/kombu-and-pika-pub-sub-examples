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
        queue_name,
        method_frame,
        header_frame,
        body):
    """
    handle_message

    :param channel: pika channel
    :param queue_name: name of the queue
    :param method_frame: message object
    :param header_frame: header object
    :param body: message contents
    """
    print(("{} - consumed message queue={} delivery_tag={} "
           "delivery_mode={} body={}")
          .format(
            datetime.datetime.now().strftime(
                "%Y-%m-%d %H-%M-%S"),
            queue_name,
            method_frame.delivery_tag,
            header_frame.delivery_mode,
            body.decode("utf-8")))
    channel.basic_ack(method_frame.delivery_tag)
# end of on_message


not_done = True
while not_done:
    for queue_node in queues:
        queue_name = queue_node["name"]

        # noqa https://pika.readthedocs.io/en/0.11.2/examples/blocking_basic_get.html
        (method_frame,
         header_frame,
         body) = channel.basic_get(
                    queue=queue_name)
        if method_frame:
            handle_message(
                channel,
                queue_name,
                method_frame,
                header_frame,
                body)
        # end of if there is a message to process
    # end of for all queues
# end of consuming

print("shutting down")
channel.close()
connection.close()
