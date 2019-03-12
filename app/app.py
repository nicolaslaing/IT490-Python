from flask import Flask, render_template
# import MySQLdb
# import random

app = Flask(__name__)

@app.route('/test')
def index():
	# return render_template("index.html")
	return "Hello"

if __name__ == '__main__':
	app.run(host='0.0.0.0')