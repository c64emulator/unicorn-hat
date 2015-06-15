#! /usr/bin/env python

from flask import Flask, render_template
import datetime
import os

app = Flask(__name__)

@app.route("/")
def hello():

   if os.path.exists('/tmp/.hamster_disco'):
      message='Looks like hamster is having a disco' # - <a href="/kill_hamster_disco">Break it up</a>'
   else:
      message="Nothing happening"
   now = datetime.datetime.now()
   timeString = now.strftime("%Y-%m-%d %H:%M:%S")
   templateData = {
      'title' : "Hamster disco monitor",
      'message' : message,
      'time': timeString
      }
   return render_template('main.html', **templateData)

@app.route("/kill_hamster_disco")
def kill_hamster_disco():
   try:
      os.remove('/tmp/.hamster_disco')
      return "Bye, bye hamster disco"
   except:
      return "The party was already over"

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=True)
