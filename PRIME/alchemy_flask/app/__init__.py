import os
from flask import Flask
from app.senso_mqtt import start_mqtt  # Just import and run

def alchemy_app():
    app = Flask(__name__)
    if not os.environ.get("FLASK_RUN_FROM_CLI") or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_mqtt()
    return app
