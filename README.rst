Kombu and Pika Publisher and Subscriber Examples
================================================

Simple publisher and subscriber examples for Kombu and Pika with a RabbitMQ broker.

How do I get started?
-------------------

#.  Setup the virtual environment

    If you want to use python 2:

    ::

        virtualenv venv && source venv/bin/activate && pip install -r ./requirements.txt && pip list --format=columns

    If you want to use python 3:

    ::

        virtualenv -p python3 venv && source venv/bin/activate && pip install -r ./requirements.txt && pip list --format=columns

#.  Start the RabbitMQ container

    ::

        ./start-rabbitmq.sh 

        Starting RabbitMQ

        Starting rabbit ... done

        CONTAINER ID        IMAGE                       COMMAND                  CREATED             STATUS              PORTS                                                                                                       NAMES
        121597ed8489        rabbitmq:3.6.6-management   "docker-entrypoint.s…"   58 seconds ago      Up 2 seconds        4369/tcp, 5671/tcp, 0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp, 15671/tcp, 0.0.0.0:25672->25672/tcp   rabbit

#.  List the Exchanges

    ::

        ./list-exchanges.sh 

        Listing Exchanges broker=localhost:15672

        +--------------------+---------+---------+-------------+
        |        name        |  type   | durable | auto_delete |
        +--------------------+---------+---------+-------------+
        |                    | direct  | True    | False       |
        | amq.direct         | direct  | True    | False       |
        | amq.fanout         | fanout  | True    | False       |
        | amq.headers        | headers | True    | False       |
        | amq.match          | headers | True    | False       |
        | amq.rabbitmq.log   | topic   | True    | False       |
        | amq.rabbitmq.trace | topic   | True    | False       |
        | amq.topic          | topic   | True    | False       |
        +--------------------+---------+---------+-------------+

#.  List the Queues

    ::

        ./list-queues.sh 

        Listing Queues broker=localhost:15672

        No items

RabbitMQ Durable + Persistence - Exploring What Survives a Broker Failure
-------------------------------------------------------------------------

#.  Run Kombu Publisher

    This step will create 1 exchange, 2 queues and 2 bindings in the RabbitMQ broker. It will also publish 1 persistent message to each of the 2 queues and 1 non-persistent message to each of the 2 queues.

    ::

        ./kombu/publisher.py 
        getting connection
        getting channel
        creating producer
        declaring producer
        declaring exchange=east-coast
        binding queue=1 ex=east-coast->topic queue=us.east.charlotte
        binding queue=2 ex=east-coast->topic queue=us.east.newyork
        publishing=1 exchange=east-coast routing_key=us.east.charlotte persist=2 msg=Kombu sent a Persistent Message - 1 - 2018-03-17-08-24-51
        publishing=2 exchange=east-coast routing_key=us.east.newyork persist=2 msg=Kombu sent a Persistent Message - 2 - 2018-03-17-08-24-51
        publishing=3 exchange=east-coast routing_key=us.east.charlotte persist=1 msg=Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-24-51
        publishing=4 exchange=east-coast routing_key=us.east.newyork persist=1 msg=Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-24-51
        shutting down

#.  Check the exchange for the new ``east-coast`` exchange

    ::

        ./list-exchanges.sh 

        Listing Exchanges broker=localhost:15672

        +--------------------+---------+---------+-------------+
        |        name        |  type   | durable | auto_delete |
        +--------------------+---------+---------+-------------+
        |                    | direct  | True    | False       |
        | amq.direct         | direct  | True    | False       |
        | amq.fanout         | fanout  | True    | False       |
        | amq.headers        | headers | True    | False       |
        | amq.match          | headers | True    | False       |
        | amq.rabbitmq.log   | topic   | True    | False       |
        | amq.rabbitmq.trace | topic   | True    | False       |
        | amq.topic          | topic   | True    | False       |
        | east-coast         | topic   | True    | False       |
        +--------------------+---------+---------+-------------+

#.  Check the queue for the new queues

    Notice there are 2 messages in each of the new queues ``us.east.charlotte`` and ``us.east.newyork``. Verify the ``us.east.newyork`` queue has a durable value of ``False``. This means the ``us.east.newyork`` queue will not be restored automatically if the broker restarts and any messages not-consumed before a broker failure will be lost. 

    Additionally, any messages not flagged with ``delivery_mode = 2`` will be lost even if the queue has ``durable`` set to ``True``. Here's some more reading on how the ``delivery_mode`` property ``2`` works to enable persistence. Under the hood the message is written into the Erlang Mnesia database which is usually written to disk. Depending on a cluster configuration, messages can also be stored in memory when a broker node is in RAM mode. This type of RAM configuration can lose persistence messages as well if that node fails (hopefully the entire cluster does not crash in this case).

    - https://www.rabbitmq.com/releases/rabbitmq-java-client/v3.5.4/rabbitmq-java-client-javadoc-3.5.4/com/rabbitmq/client/MessageProperties.html
    - https://stackoverflow.com/questions/2344022/what-is-the-delivery-mode-in-amqp
    - https://www.rabbitmq.com/clustering.html#overview-node-types
    - https://lists.rabbitmq.com/pipermail/rabbitmq-discuss/2011-September/014878.html

    ::

        ./list-queues.sh 

        Listing Queues broker=localhost:15672

        +-------------------+---------+-------------+-----------+----------+----------------+-------------------------+
        |       name        | durable | auto_delete | consumers | messages | messages_ready | messages_unacknowledged |
        +-------------------+---------+-------------+-----------+----------+----------------+-------------------------+
        | us.east.charlotte | True    | False       | 0         | 2        | 2              | 0                       |
        | us.east.newyork   | False   | False       | 0         | 2        | 2              | 0                       |
        +-------------------+---------+-------------+-----------+----------+----------------+-------------------------+

#.  Simulate a Broker Failure

    ::

        ./stop-rabbitmq.sh

#.  Start the Broker

    ::

        ./start-rabbitmq.sh

#.  Verify the ``us.east.charlotte`` Queue and Message are there

    Make sure to wait at least 10 seconds for the broker to start up.

    Verify that the ``us.east.charlotte`` queue was recreated automatically but not the ``us.east.newyork`` queue. Also verify that there is only 1 message in the ``us.east.charlotte`` queue.

    ::

        ./list-queues.sh 

        Listing Queues broker=localhost:15672

        +-------------------+---------+-------------+-----------+----------+----------------+-------------------------+
        |       name        | durable | auto_delete | consumers | messages | messages_ready | messages_unacknowledged |
        +-------------------+---------+-------------+-----------+----------+----------------+-------------------------+
        | us.east.charlotte | True    | False       | 0         | 1        | 1              | 0                       |
        +-------------------+---------+-------------+-----------+----------+----------------+-------------------------+

Publisher Subscriber Examples
=============================

Start a Kombu Publisher
-----------------------

In a new window, source the virtual environment ``venv`` to activate the runtime:

::

    source venv/bin/activate

Run:

::

    ./kombu/publisher.py 
    getting connection
    getting channel
    creating producer
    declaring producer
    declaring exchange=east-coast
    binding queue=1 ex=east-coast->topic queue=us.east.charlotte
    binding queue=2 ex=east-coast->topic queue=us.east.newyork
    publishing=1 exchange=east-coast routing_key=us.east.charlotte persist=2 msg=Kombu sent a Persistent Message - 1 - 2018-03-17-08-27-17
    publishing=2 exchange=east-coast routing_key=us.east.newyork persist=2 msg=Kombu sent a Persistent Message - 2 - 2018-03-17-08-27-17
    publishing=3 exchange=east-coast routing_key=us.east.charlotte persist=1 msg=Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-27-17
    publishing=4 exchange=east-coast routing_key=us.east.newyork persist=1 msg=Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-27-17
    shutting down

Start a Pika Publisher
---------------------

In a new window, source the virtual environment ``venv`` to activate the runtime:

::

    source venv/bin/activate

Run:

::

    ./pika/publisher.py 
    building parameters
    building blocking connection
    getting channel
    creating exchange=east-coast
    creating queue=1 queue=us.east.charlotte
    binding queue=1 ex=east-coast->topic queue=us.east.charlotte
    creating queue=2 queue=us.east.newyork
    binding queue=2 ex=east-coast->topic queue=us.east.newyork
    publishing=1 exchange=east-coast routing_key=us.east.charlotte persist=2 msg={'value': 'Pika sent a Persistent Message - 1 - 2018-03-17-08-27-30'}
    publishing=2 exchange=east-coast routing_key=us.east.newyork persist=2 msg={'value': 'Pika sent a Persistent Message - 2 - 2018-03-17-08-27-30'}
    publishing=3 exchange=east-coast routing_key=us.east.charlotte persist=1 msg={'value': 'Pika sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-27-30'}
    publishing=4 exchange=east-coast routing_key=us.east.newyork persist=1 msg={'value': 'Pika sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-27-30'}
    shutting down

List the Queues
---------------

Note the 1 persistent message that started in the durable ``us.east.charlotte`` queue is still there for a total of ``5`` messages.

::

    ./list-queues.sh 

    Listing Queues broker=localhost:15672

    +-------------------+---------+-------------+-----------+----------+----------------+-------------------------+
    |       name        | durable | auto_delete | consumers | messages | messages_ready | messages_unacknowledged |
    +-------------------+---------+-------------+-----------+----------+----------------+-------------------------+
    | us.east.charlotte | True    | False       | 0         | 5        | 5              | 0                       |
    | us.east.newyork   | False   | False       | 0         | 4        | 4              | 0                       |
    +-------------------+---------+-------------+-----------+----------+----------------+-------------------------+

Start the Kombu Consumer
------------------------

In a new window, source the virtual environment ``venv`` to activate the runtime:

::

    source venv/bin/activate

This will consume all the messages found in both the ``us.east.charlotte`` and ``us.east.newyork`` queues. Note the first message was the one that was able to persist beyond the broker restart.

Run:

::

    ./kombu/consumer.py 
    getting connection
    getting channel
    binding queue=0 ex=east-coast->topic queue=us.east.charlotte
    binding queue=1 ex=east-coast->topic queue=us.east.newyork
    creating consumer
    callback received msg routing_key=us.east.charlotte body=Kombu sent a Persistent Message - 1 - 2018-03-17-08-24-51
    callback received msg routing_key=us.east.charlotte body=Kombu sent a Persistent Message - 1 - 2018-03-17-08-27-17
    callback received msg routing_key=us.east.charlotte body=Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-27-17
    callback received msg routing_key=us.east.charlotte body={'value': 'Pika sent a Persistent Message - 1 - 2018-03-17-08-27-30'}
    callback received msg routing_key=us.east.charlotte body={'value': 'Pika sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-27-30'}
    callback received msg routing_key=us.east.newyork body=Kombu sent a Persistent Message - 2 - 2018-03-17-08-27-17
    callback received msg routing_key=us.east.newyork body=Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-27-17
    callback received msg routing_key=us.east.newyork body={'value': 'Pika sent a Persistent Message - 2 - 2018-03-17-08-27-30'}
    callback received msg routing_key=us.east.newyork body={'value': 'Pika sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-27-30'}

Start a Pika Consumer
---------------------

In a new window, source the virtual environment ``venv`` to activate the runtime:

::

    source venv/bin/activate

Run:

::

    ./pika/consumer.py 
    building parameters
    building blocking connection
    getting channel

Publish New Messages with the Pika Publisher
--------------------------------------------

In a new window, source the virtual environment ``venv`` to activate the runtime:

::

    source venv/bin/activate

Run:

::

    ./pika/publisher.py 
    building parameters
    building blocking connection
    getting channel
    creating exchange=east-coast
    creating queue=1 queue=us.east.charlotte
    binding queue=1 ex=east-coast->topic queue=us.east.charlotte
    creating queue=2 queue=us.east.newyork
    binding queue=2 ex=east-coast->topic queue=us.east.newyork
    publishing=1 exchange=east-coast routing_key=us.east.charlotte persist=2 msg={'value': 'Pika sent a Persistent Message - 1 - 2018-03-17-08-30-06'}
    publishing=2 exchange=east-coast routing_key=us.east.newyork persist=2 msg={'value': 'Pika sent a Persistent Message - 2 - 2018-03-17-08-30-06'}
    publishing=3 exchange=east-coast routing_key=us.east.charlotte persist=1 msg={'value': 'Pika sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-30-06'}
    publishing=4 exchange=east-coast routing_key=us.east.newyork persist=1 msg={'value': 'Pika sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-30-06'}
    shutting down

Verify the Consumers Consumed the Messages
------------------------------------------

It might just be my vm, but it looks like the Kombu consumer is always consuming the messages with logs:

::

    callback received msg routing_key=us.east.charlotte body={'value': 'Pika sent a Persistent Message - 1 - 2018-03-17-08-30-06'}
    callback received msg routing_key=us.east.newyork body={'value': 'Pika sent a Persistent Message - 2 - 2018-03-17-08-30-06'}
    callback received msg routing_key=us.east.newyork body={'value': 'Pika sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-30-06'}
    callback received msg routing_key=us.east.charlotte body={'value': 'Pika sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-30-06'}

Stop the Kombu Consumer
-----------------------

Use ``ctrl + c`` to stop the Kombu consumer.

Publish Messages with the Pika Publisher
----------------------------------------

::

    ./pika/publisher.py 
    building parameters
    building blocking connection
    getting channel
    creating exchange=east-coast
    creating queue=0 queue=us.east.charlotte
    binding queue=0 ex=east-coast->topic queue=us.east.charlotte
    creating queue=1 queue=us.east.newyork
    binding queue=1 ex=east-coast->topic queue=us.east.newyork
    publishing=0 exchange=east-coast routing_key=us.east.* persist=2 msg={'value': 'Pika sent a Persistent Message - 1 - 2018-03-17-08-03-22'}
    publishing=1 exchange=east-coast routing_key=us.east.* persist=2 msg={'value': 'Pika sent a Persistent Message - 2 - 2018-03-17-08-03-22'}
    publishing=2 exchange=east-coast routing_key=us.east.charlotte persist=1 msg={'value': 'Pika sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-03-22'}
    publishing=3 exchange=east-coast routing_key=us.east.newyork persist=1 msg={'value': 'Pika sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-03-22'}
    shutting down

Verify the Pika Consumer Consumed the Messages
----------------------------------------------

::

    2018-03-17-08-30-55 - consumed message queue=us.east.charlotte delivery_tag=1 delivery_mode=2 body={"value": "Pika sent a Persistent Message - 1 - 2018-03-17-08-30-55"}
    2018-03-17-08-30-55 - consumed message queue=us.east.newyork delivery_tag=2 delivery_mode=2 body={"value": "Pika sent a Persistent Message - 2 - 2018-03-17-08-30-55"}
    2018-03-17-08-30-55 - consumed message queue=us.east.charlotte delivery_tag=3 delivery_mode=1 body={"value": "Pika sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-30-55"}
    2018-03-17-08-30-55 - consumed message queue=us.east.newyork delivery_tag=4 delivery_mode=1 body={"value": "Pika sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-30-55"}

Start the Kombu Consumer Again
------------------------------

::

    ./kombu/consumer.py 
    getting connection
    getting channel
    binding queue=0 ex=east-coast->topic queue=us.east.charlotte
    binding queue=1 ex=east-coast->topic queue=us.east.newyork
    creating consumer

Send a Large Batch of Messages
------------------------------

::

    ./kombu/batch_publisher.py

    ...

    
    batch=99 publishing=3 exchange=east-coast routing_key=us.east.charlotte persist=1 msg=Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-31-46
    batch=99 publishing=4 exchange=east-coast routing_key=us.east.newyork persist=1 msg=Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-31-46
    batch=100 publishing=1 exchange=east-coast routing_key=us.east.charlotte persist=2 msg=Kombu sent a Persistent Message - 1 - 2018-03-17-08-31-46
    batch=100 publishing=2 exchange=east-coast routing_key=us.east.newyork persist=2 msg=Kombu sent a Persistent Message - 2 - 2018-03-17-08-31-46
    batch=100 publishing=3 exchange=east-coast routing_key=us.east.charlotte persist=1 msg=Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-31-46
    batch=100 publishing=4 exchange=east-coast routing_key=us.east.newyork persist=1 msg=Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-31-46
    done sending batches=100 total_messages=400
    shutting down

Verify all Messages are Consumed by One of the Consumers
--------------------------------------------------------

Note: mine were all consumed by the Kombu consumer

::

    callback received msg routing_key=us.east.charlotte body=Kombu sent a Persistent Message - 1 - 2018-03-17-08-31-46
    callback received msg routing_key=us.east.newyork body=Kombu sent a Persistent Message - 2 - 2018-03-17-08-31-46
    callback received msg routing_key=us.east.charlotte body=Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-31-46
    callback received msg routing_key=us.east.newyork body=Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-31-46
    callback received msg routing_key=us.east.charlotte body=Kombu sent a Persistent Message - 1 - 2018-03-17-08-31-46
    callback received msg routing_key=us.east.newyork body=Kombu sent a Persistent Message - 2 - 2018-03-17-08-31-46
    callback received msg routing_key=us.east.charlotte body=Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-31-46
    callback received msg routing_key=us.east.newyork body=Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-31-46

Shutdown the Pika Consumer
--------------------------

Use ``ctrl + c`` to stop the consumer

Start the Blocked Pika Consumer 
-------------------------------

This uses the same pika ``BlockingConnection`` channel to subscribe to the 2 queues with ``basic_consume`` and then calls ``start_consuming`` to block the process. The process will then wait to consume any messages on the 2 queues.

::

    ./pika/blocked-consumer.py
    building parameters
    building blocking connection
    getting channel
    starting basic_consume queue=us.east.charlotte
    starting basic_consume queue=us.east.newyork
    starting channel consume queues=['us.east.charlotte', 'us.east.newyork']

Publish Messages with the Pika Publisher
----------------------------------------

::

    ./pika/publisher.py 
    building parameters
    building blocking connection
    getting channel
    creating exchange=east-coast
    creating queue=1 queue=us.east.charlotte
    binding queue=1 ex=east-coast->topic queue=us.east.charlotte
    creating queue=2 queue=us.east.newyork
    binding queue=2 ex=east-coast->topic queue=us.east.newyork
    publishing=1 exchange=east-coast routing_key=us.east.charlotte persist=2 msg={'value': 'Pika sent a Persistent Message - 1 - 2018-03-17-08-33-14'}
    publishing=2 exchange=east-coast routing_key=us.east.newyork persist=2 msg={'value': 'Pika sent a Persistent Message - 2 - 2018-03-17-08-33-14'}
    publishing=3 exchange=east-coast routing_key=us.east.charlotte persist=1 msg={'value': 'Pika sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-33-14'}
    publishing=4 exchange=east-coast routing_key=us.east.newyork persist=1 msg={'value': 'Pika sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-33-14'}
    shutting down

Verify Messages are Consumed by the Kombu Consumer and the Pika Blocked Consumer
--------------------------------------------------------------------------------

Kombu consumer logs from this example:

::

    callback received msg routing_key=us.east.charlotte body={'value': 'Pika sent a Persistent Message - 1 - 2018-03-17-08-33-14'}
    callback received msg routing_key=us.east.newyork body={'value': 'Pika sent a Persistent Message - 2 - 2018-03-17-08-33-14'}

Pika Blocked consumer logs from this example:

::

    2018-03-17-08-33-14 - Blocked Pika - consumed message delivery_tag=1 delivery_mode=1 body={"value": "Pika sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-33-14"}
    2018-03-17-08-33-14 - Blocked Pika - consumed message delivery_tag=2 delivery_mode=1 body={"value": "Pika sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-33-14"}

Publish using the Kombu Publisher
---------------------------------

::

    ./kombu/publisher.py 
    getting connection
    getting channel
    creating producer
    declaring producer
    declaring exchange=east-coast
    binding queue=1 ex=east-coast->topic queue=us.east.charlotte
    binding queue=2 ex=east-coast->topic queue=us.east.newyork
    publishing=1 exchange=east-coast routing_key=us.east.charlotte persist=2 msg=Kombu sent a Persistent Message - 1 - 2018-03-17-08-37-14
    publishing=2 exchange=east-coast routing_key=us.east.newyork persist=2 msg=Kombu sent a Persistent Message - 2 - 2018-03-17-08-37-14
    publishing=3 exchange=east-coast routing_key=us.east.charlotte persist=1 msg=Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-37-14
    publishing=4 exchange=east-coast routing_key=us.east.newyork persist=1 msg=Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-37-14
    shutting down

Verify Messages were Consumed by Both Consumers
-----------------------------------------------

Kombu consumer:

::

    callback received msg routing_key=us.east.charlotte body=Kombu sent a Persistent Message - 1 - 2018-03-17-08-37-14
    callback received msg routing_key=us.east.newyork body=Kombu sent a Persistent Message - 2 - 2018-03-17-08-37-14

Blocked Pika consumer:

::

    2018-03-17-08-37-14 - Blocked Pika - consumed message delivery_tag=205 delivery_mode=1 body="Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-37-14"
    2018-03-17-08-37-14 - Blocked Pika - consumed message delivery_tag=206 delivery_mode=1 body="Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-37-14"

Publish a Batch of Messages
---------------------------

::

    ./kombu/batch-publisher.py

    ...

    batch=99 publishing=1 exchange=east-coast routing_key=us.east.charlotte persist=2 msg=Kombu sent a Persistent Message - 1 - 2018-03-17-08-34-43
    batch=99 publishing=2 exchange=east-coast routing_key=us.east.newyork persist=2 msg=Kombu sent a Persistent Message - 2 - 2018-03-17-08-34-43
    batch=99 publishing=3 exchange=east-coast routing_key=us.east.charlotte persist=1 msg=Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-34-43
    batch=99 publishing=4 exchange=east-coast routing_key=us.east.newyork persist=1 msg=Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-34-43
    batch=100 publishing=1 exchange=east-coast routing_key=us.east.charlotte persist=2 msg=Kombu sent a Persistent Message - 1 - 2018-03-17-08-34-43
    batch=100 publishing=2 exchange=east-coast routing_key=us.east.newyork persist=2 msg=Kombu sent a Persistent Message - 2 - 2018-03-17-08-34-43
    batch=100 publishing=3 exchange=east-coast routing_key=us.east.charlotte persist=1 msg=Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-34-43
    batch=100 publishing=4 exchange=east-coast routing_key=us.east.newyork persist=1 msg=Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-34-43
    done sending batches=100 total_messages=400
    shutting down

Verify Messages were Consumed by Both Consumers
-----------------------------------------------

Kombu consumer:

::

    callback received msg routing_key=us.east.newyork body=Kombu sent a Persistent Message - 2 - 2018-03-17-08-34-43
    callback received msg routing_key=us.east.newyork body=Kombu sent a Persistent Message - 2 - 2018-03-17-08-34-43
    callback received msg routing_key=us.east.newyork body=Kombu sent a Persistent Message - 2 - 2018-03-17-08-34-43
    callback received msg routing_key=us.east.charlotte body=Kombu sent a Persistent Message - 1 - 2018-03-17-08-34-43
    callback received msg routing_key=us.east.charlotte body=Kombu sent a Persistent Message - 1 - 2018-03-17-08-34-43
    callback received msg routing_key=us.east.charlotte body=Kombu sent a Persistent Message - 1 - 2018-03-17-08-34-43
    callback received msg routing_key=us.east.charlotte body=Kombu sent a Persistent Message - 1 - 2018-03-17-08-34-43
    callback received msg routing_key=us.east.charlotte body=Kombu sent a Persistent Message - 1 - 2018-03-17-08-34-43
    callback received msg routing_key=us.east.charlotte body=Kombu sent a Persistent Message - 1 - 2018-03-17-08-34-43

Blocked Pika consumer:

::

    2018-03-17-08-34-43 - Blocked Pika - consumed message delivery_tag=195 delivery_mode=1 body="Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-34-43"
    2018-03-17-08-34-43 - Blocked Pika - consumed message delivery_tag=196 delivery_mode=1 body="Kombu sent a NOT-Persistent - us.east.newyork Message - 4 - 2018-03-17-08-34-43"
    2018-03-17-08-34-43 - Blocked Pika - consumed message delivery_tag=197 delivery_mode=1 body="Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-34-43"
    2018-03-17-08-34-43 - Blocked Pika - consumed message delivery_tag=198 delivery_mode=1 body="Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-34-43"
    2018-03-17-08-34-43 - Blocked Pika - consumed message delivery_tag=199 delivery_mode=1 body="Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-34-43"
    2018-03-17-08-34-43 - Blocked Pika - consumed message delivery_tag=200 delivery_mode=1 body="Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-34-43"
    2018-03-17-08-34-43 - Blocked Pika - consumed message delivery_tag=201 delivery_mode=1 body="Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-34-43"
    2018-03-17-08-34-43 - Blocked Pika - consumed message delivery_tag=202 delivery_mode=1 body="Kombu sent a NOT-Persistent - us.east.charlotte Message - 3 - 2018-03-17-08-34-43"

Shutting Down
=============

Stop All Consumers
------------------

From the kombu and pika consumer windows use ``ctrl + c`` to stop them.

Deleting the RabbitMQ database
------------------------------

Docker is mounting a host directory as a volume into the container for saving the Erlang Mnesia database to disk. This can be deleted by:

::

    ./stop-rabbitmq.sh 
    sudo rm -rf ./rabbitmq/data/*

How to Stop the RabbitMQ Container
----------------------------------

::

    ./stop-rabbitmq.sh

License
-------

Apache 2.0 - Please refer to the LICENSE_ for more details

.. _License: https://github.com/jay-johnson/kombu-and-pika-pub-sub-examples/blob/master/LICENSE
