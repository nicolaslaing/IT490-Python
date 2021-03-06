#!/usr/bin/env python
import pika
import json
from flask import Flask, request, render_template
from flask.json import jsonify
import requests
import sys
# import MySQLdb
# import random

# To run this app in the background, you can add '&' at the end of the terminal command
	#i.e. >python app.py &
# Then, you can just exit (Ctrl+C) and continue with whatever you need to do; the program is running in the background
# To restart, you'll need to lookup the process ID (PID) via the command: 
	# ps ax | grep app.py
# Then, kill the process via "kill <PID>"

# Instantiate the flask RESTful app
app = Flask(__name__)
run_on_host = '0.0.0.0'

# Miscellaneous variables
isDMZ = False # Set to False if the network is LAN and not connected to the internet
queueBody = '' # Used by DMZ server for accessing API via a JSON object with the config variables

# Default configuration
amqpUsername = 'NickLai'
amqpPassword = 'rmq12490'
amqpIP = '127.0.0.1'
amqpPort = '5672'
amqpVHost = 'Theta'

# Arguments (python app.py -arg1 -arg2 -arg3 ...):
# -ip: Change the RabbitMQ IP
# -dmz: Indicate you are the DMZ server
if len(sys.argv) > 1:
	if str(sys.argv[1]) == "-ip" and str(sys.argv[3]) == "-dmz":
		amqpIP = str(sys.argv[2])
		isDMZ = True
		print("\n*** Running RabbitMQ on (" + amqpIP + ")\n*** Server is DMZ\n")
	elif str(sys.argv[1]) == "-ip":
		amqpIP = str(sys.argv[2])
		print("\n*** Running RabbitMQ on (" + amqpIP + ")\n*** Server is not DMZ\n")
	elif str(sys.argv[1]) == "-dmz":
		isDMZ = True
		print("\n*** Running RabbitMQ on (" + amqpIP + ")\n*** Server is DMZ\n")
	else:
		print("\n*** Running RabbitMQ on (" + amqpIP + ")\n*** Server is not DMZ\n")
else:
	print("\n*** No arguments detected\n*** Running RabbitMQ on (" + amqpIP + ")\n*** Server is not DMZ\n")

# Connection variables used to connect to RabbitMQ via AMQ Protocol
credentials = pika.PlainCredentials(amqpUsername, amqpPassword)
parameters = pika.ConnectionParameters(amqpIP, amqpPort, amqpVHost, credentials)

##################################################### PUBLISH #####################################################

# You can run the following command to from a terminal send this publish request:
# curl -X POST -H "Accept: application/json" -H "Content-Type: application/json" 
# -d '{"key","value"}' 0.0.0.0:5000/publish/{name-of-queue}

@app.route('/publish/<queue>', methods=['POST'])
def publish(queue):

	# Create the connection
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
# in the python debug console which runs this file (i.e. after doing 'python app.py' in terminal)

@app.route('/consume/<queue>', methods=['GET'])
def consume(queue):

	global queueBody

	# Create the connection
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

	if isDMZ:
		getAPI()

	return json.dumps(queueBody) + "\n"
	# return "HTTP Request Successful (200)\n"

# Only the DMZ server is allowed to call this function
# To enable, send the flag "-dmz" when starting the app.py (i.e. "python app.py -dmz")
def getAPI():
	# The following variables are API data points to be inserted into the API URL
		# i.e. 
		#	queueBody = { 
		#			"queue_to_publish": "performances", 
		#			"api_route": "artist/123/performances, 
		#	}

	# To obtain API from a different source, add these keys to the object:
		# "api_PROTOCOL": "http OR https",    <--- The site's http protocol
		# "api_DOMAIN": "site.com"

	default_queue_to_publish = 'api'
	default_api_PROTOCOL = "https"
	default_api_DOMAIN = 'secondhandsongs.com'
	default_api_ROUTE = ''
	default_api_PARAMS = "format=json" # SecondHandSongs API requires 'format=json' for JSON responses

	queue_to_publish = queueBody["queue_to_publish"] if "queue_to_publish" in queueBody else default_queue_to_publish # desired queue to later consume from

	api_PROTOCOL = queueBody["api_protocol"] if "api_protocol" in queueBody else default_api_PROTOCOL # 'http' or 'https'
	api_DOMAIN = queueBody["api_domain"] if "api_domain" in queueBody else default_api_DOMAIN # the domain of which the api is resolved from
	api_ROUTE = queueBody["api_route"] if "api_route" in queueBody else default_api_ROUTE # a string used to identify the route structure (e.g. "artist/123/performance")
	api_PARAMS = queueBody["api_params"] if "api_params" in queueBody else default_api_PARAMS # necessary URL query string(s) to make the API function or return certain data

	api_URL = api_PROTOCOL + '://' + api_DOMAIN + '/' + api_ROUTE + '?' + api_PARAMS

	# Send the GET request
	apiResponse = requests.get(url=api_URL)

	# Publish API data to RabbitMQ
	if apiResponse.ok:

		flaskURL = 'http://0.0.0.0:5000/publish/' + queue_to_publish

		# Send the POST request
		flaskResponse = requests.post(
				url=flaskURL, 
				data=json.dumps(apiResponse.json()), 
				headers={'Content-Type': 'application/json'})

		if flaskResponse.ok:
		    return json.dumps(flaskResponse)
		    # return "HTTP Request Successful (200)\n"
		else:
			return "Internal server error (500) while accessing " + flaskURL + "\n"


if __name__ == '__main__':
	app.run(host=run_on_host)

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