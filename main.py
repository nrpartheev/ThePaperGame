from flask import Flask
import subprocess
import os
from dotenv import load_dotenv

app = Flask(__name__) 

@app.route('/admin')
def home():
    return "APP : HEALTHY"

subprocess.Popen(["python3", "reddit.py"])

if __name__ == "__main__":
    load_dotenv(dotenv_path=".env")
    app.run(host="0.0.0.0")
