#!/usr/bin/env python
import pika
import json
from flask import Flask, request, render_template
from flask.json import jsonify
import requests
import sys
# import MySQLdb
# import random

app = Flask(__name__)

queueBody=''
ip = '192.168.2.174'
if len(sys.argv) > 1:
	ip = str(sys.argv[1])

credentials = pika.PlainCredentials('NickLai','rmq12490')
parameters = pika.ConnectionParameters(ip, '5672', 'Theta', credentials)

##################################################### PUBLISH #####################################################

# You can run the following command to from a terminal send this publish request:
# curl -X POST -H "Accept: application/json" -H "Content-Type: application/json" 
# -d '{"key","value"}' 0.0.0.0:5000/publish/{name-of-queue}

@app.route('/publish/<queue>', methods=['POST'])
def publish(queue):

	connection = pika.BlockingConnection(parameters)
	channel = connection.channel()

	jsonBody = request.get_json()

	channel.queue_declare(queue=queue)

	channel.basic_publish(exchange='',
                      routing_key=queue,
                      body=json.dumps(jsonBody, ensure_ascii=False))

	print(" [x] Sent object")

	channel.close()
	connection.close()

	return "HTTP Request Successful (200)\n"

##################################################### CONSUME #####################################################

# You can run the following command from a terminal to send this consume request:
# curl 0.0.0.0:5000/consume/{name-of-queue}

# You sould see a print out of whatever data was sent via the publish route
# in the python debug console which runs this file

@app.route('/consume/<queue>', methods=['GET'])
def consume(queue):

	global queueBody
	connection = pika.BlockingConnection(parameters)
	channel = connection.channel()

	channel.queue_declare(queue=queue)

	def callback(ch, method, properties, body):
		global queueBody
		queueBody = json.loads(body) # convert string to json
		print(" [x] Received %r" % body)
		channel.stop_consuming()
		channel.close()
		connection.close()

	channel.basic_consume(callback,
	                      queue=queue,
	                      no_ack=True)

	print('Waiting for messages...')
	
	channel.start_consuming()

	# Code for DMZ script; comment out if you're not using a DMZ server

	# API data to be inserted into the API URL
	# e.g queueBody = {"id": "123", "route-primary": "artist", "route-secondary": "performances"}

	default_api_DOMAIN = 'secondhandsongs.com'
	default_publish_to_queue = 'api'

	queue_to_publish = queueBody["queue_to_publish"] if "queue_to_publish" in queueBody else default_publish_to_queue # desired queue to later consume from

	api_DOMAIN = queueBody["api_domain"] if "api_domain" in queueBody else default_api_DOMAIN # the domain of which the api is resolved from
	api_ID = queueBody["id"] # an ID that is used to identify entities within the API
	api_ROUTE_Primary = queueBody["route_primary"] # a string used to identify the primary root route structure (e.g. "artist")
	api_ROUTE_Secondary = queueBody["route_secondary"] # a string used to identify a secondary route structure (e.g. artist/123/performances)
	api_PARAMS = 'format=json' # necessary URL query string(s) to make the API function or return certain data (SHS API requires 'format=json' for JSON responses)

	apiURL = 'https://' + api_DOMAIN + '/' + api_ROUTE_Primary + '/' + api_ID + '/' + api_ROUTE_Secondary + '?' + api_PARAMS

	apiResponse = requests.get(url=apiURL)

	# Publish API data to RabbitMQ
	if apiResponse.ok:
		# Code for posting API data to RabbitMQ for consumption by non-DMZ servers
		flaskURL = 'http://0.0.0.0:5000/publish/' + queue_to_publish
		flaskResponse = requests.post(
				url=flaskURL, 
				data=json.dumps(apiResponse.json()), 
				headers={'Content-Type': 'application/json'})

		if flaskResponse.ok:
		    # return json.dumps(flaskResponse)
		    return "HTTP Request Successful (200)\n"
		else:
			return "Internal server error (500) while accessing " + flaskURL + "\n"

	# - END DMZ SCRIPT -

	return "HTTP Request Successful (200)\n"

if __name__ == '__main__':
	app.run(host='0.0.0.0')

# Pika code that seemed interesting:

	# # Get ten messages and break out
	# for method_frame, properties, body in channel.consume(queue):

	#     # Display the message parts
	#     print method_frame
	#     print properties
	#     print body
	#     queueBody = body
	#     # Acknowledge the message
	#     channel.basic_ack(method_frame.delivery_tag)

	#     # Escape out of the loop after 10 messages
	#     if method_frame.delivery_tag == 10:
	#     	break

	# # Cancel the consumer and return any pending messages
	# requeued_messages = channel.cancel()
	# print 'Requeued %i messages' % requeued_messages

	# # Close the channel and the connection
	# channel.close()
	# connection.close()