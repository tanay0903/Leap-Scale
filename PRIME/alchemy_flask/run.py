from app import alchemy_app
from waitress import serve

app = alchemy_app()

@app.route("/")
def index():
    return "IoT Service is Running!"

@app.route("/status")
def status():
    return {"status": "running", "mqtt": True}, 200

serve(app, host='192.168.0.104', port=8000)

#if __name__ == '__main__':
    #app.run(host='192.168.0.104', port=5000, debug=False)
