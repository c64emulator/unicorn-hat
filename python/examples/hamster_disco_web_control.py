#! /usr/bin/env python

from flask import Flask, render_template, redirect, request
import datetime
import os
import sys

app = Flask(__name__)

@app.route("/")
def hello():
   templateData = {
      'title' : "Hamster disco monitor",
      'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      'running': os.path.exists('/tmp/.hamster_disco'),
      }
   return render_template('main.html', **templateData)

@app.route("/kill_hamster_disco")
def kill_hamster_disco():
   try:
      os.remove('/tmp/.hamster_disco')
      #return "Bye, bye hamster disco"
   finally:
      return redirect("/")
      #return "The party was already over"

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route("/kill_hamster_disco_server")
def kill_hamster_disco_server():
   shutdown_server()
   return redirect("/")
   #return 'Server shutting down...'

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=True)
