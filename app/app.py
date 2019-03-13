#!/usr/bin/env python
import pika
import json
from flask import Flask, render_template
# import MySQLdb
# import random

app = Flask(__name__)

credentials = pika.PlainCredentials('NickLai','rmq12490')
parameters = pika.ConnectionParameters('192.168.1.6', '5672', 'Theta', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

@app.route('/publish')
def publish():

	obj = {
		'yeet': 'yuh'
	}


	channel.queue_declare(queue='object')

	channel.basic_publish(exchange='',
                      routing_key='object',
                      body=json.dumps(obj, ensure_ascii=False)) # <--- must be string or unicode, not object

	print(" [x] Sent object")

	connection.close()
	# return render_template("index.html")
	return "Hello"

@app.route('/consume')
def consume():

	channel.queue_declare(queue='object')

	def callback(ch, method, properties, body):
	    print(" [x] Received %r" % body)

	channel.basic_consume(callback,
	                      queue='object',
	                      no_ack=True)

	print('Waiting for messages...')
	channel.start_consuming()
	return "Hello"

if __name__ == '__main__':
	app.run(host='0.0.0.0')