# Copyright (c) General Electric Company, 2017.  All rights reserved.

import pika, json
from rt106SpecificAdaptorCode import *

messageBody = {
    "header":
        {
            "messageId":"4a29b700-536c-11e6-b9eb-97e10e9139f4",
            "executionId":"187ca59b-efce-4b49-abf4-1866aacdc6a3",
            "creationTime":1469563524692
        },
    "analyticId":
        {
            "name":analytic_name_string,
            "version":analytic_version_string
        },
    "context":[
        {
            "input":{"value":"pat002/studyB/breast_G13-0056_series13_PURE","type":"String"}
        }
    ]
}

messageHeader = {
        "deliveryMode":2,
        "content_type":"application/json",
        "reply_to":"ccffffc172d18d0d1",
        "correlation_id":"187ca59b-efce-4b49-abf4-1866aacdc6a3"
    }

connection = pika.BlockingConnection(pika.ConnectionParameters (host='localhost'))
channel = connection.channel()
channel.queue_declare(queue=analytic_queue_string)
channel.basic_publish(exchange='',
                      routing_key=analytic_queue_string,
                      body=json.dumps(messageBody),
                      properties=pika.BasicProperties(reply_to='responeQueueName'))
print(" [x] Sent " + json.dumps(messageBody))
connection.close()
