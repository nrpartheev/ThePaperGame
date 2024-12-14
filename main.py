from flask import Flask
import subprocess
import os


app = Flask(__name__) 

@app.route('/admin')
def home():
    return "APP : HEALTHY"

subprocess.Popen(["python3", "subred.py"])

if __name__ == "__main__":
    app.run(host="0.0.0.0")
