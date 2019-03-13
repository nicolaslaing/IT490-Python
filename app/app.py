#!/usr/bin/env python
import pika
import json
from flask import Flask, request, render_template
import sys
# import MySQLdb
# import random

app = Flask(__name__)

ip = '192.168.2.174'
if len(sys.argv) > 1:
	ip = str(sys.argv[1])

credentials = pika.PlainCredentials('NickLai','rmq12490')
parameters = pika.ConnectionParameters(ip, '5672', 'Theta', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

##################################################### PUBLISH #####################################################

# You can run the following command to from a terminal send this publish request:
# curl -X POST -H "Accept: application/json" -H "Content-Type: application/json" 
# -d '{"key","value"}' 0.0.0.0:5000/publish/{name-of-queue}

@app.route('/publish/<queue>', methods=['POST'])
def publish(queue):

	content = request.get_json()
	
	channel.queue_declare(queue=queue)

	channel.basic_publish(exchange='',
                      routing_key=queue,
                      body=json.dumps(content, ensure_ascii=False))

	print(" [x] Sent object")

	# connection.close()
	return str(200)

##################################################### CONSUME #####################################################

# You can run the following command from a terminal to send this consume request:
# curl 0.0.0.0:5000/consume/{name-of-queue}

# You sould see a print out of whatever data was sent via the publish route
# in the python debug console which runs this file

@app.route('/consume/<queue>', methods=['GET'])
def consume(queue):

	channel.queue_declare(queue=queue)

	def callback(ch, method, properties, body):
	    print(" [x] Received %r" % body)

	channel.basic_consume(callback,
	                      queue=queue,
	                      no_ack=True)


	# response = curl(url)
	# post('/publish', response, 'response1')

	print('Waiting for messages...')
	channel.start_consuming()
	return str(200)

if __name__ == '__main__':
	app.run(host='0.0.0.0')