#! /usr/bin/env python

from flask import Flask, render_template, redirect, request
import datetime
import os
import sys
import subprocess

app = Flask(__name__)

def kill_disco():
   try:
      os.remove('/tmp/.christmas')
      time.sleep(5)
   except:
      pass

@app.route("/", methods=['GET', 'POST'])
def hello():

   if request.method == 'POST':
      data=request.form

   templateData = {
      'title' : "Hamster disco monitor",
      'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      'running': os.path.exists('/tmp/.christmas'),
      }
   return render_template('main.html', **templateData)

@app.route("/kill_christmas")
def kill_hamster_disco():
   kill_disco()
   return redirect("/")

def shutdown_server():
    func=request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route("/shutdown_server")
def shutdown_server():
   shutdown_server()
   return redirect("/")

@app.route("/shutdown")
def shutdown_pi():
   kill_disco()
   subprocess.call(['sudo', 'halt'])
   return redirect("/")

@app.route("/reboot")
def reboot_pi():
   subprocess.call(['sudo', 'reboot'])
   return redirect("/")
   
if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=True)
