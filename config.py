import os
from flask import Flask

def create_app():
    app=Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"]=8*1024*1024
    os.makedirs("data",exist_ok=True)
    os.makedirs("data/uploads",exist_ok=True)
    return app
