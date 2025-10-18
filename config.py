import os
from flask import Flask

def create_app():
    app=Flask(__name__)
    os.makedirs("data",exist_ok=True)
    os.makedirs("data/uploads",exist_ok=True)
    return app
