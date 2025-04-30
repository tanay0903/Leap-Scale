from flask import Flask, render_template, request, jsonify
import json
from tool import validateData
import time
import threading
import os 
import signal

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate():
    try:
        json_data = request.get_json()
        raw_data = json.dumps(json_data, indent=4)
        result = validateData(json_data, raw_data)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"result": f"Error: {str(e)}"})

# 🔁 Background thread to simulate crash
def simulate_crash():
    time.sleep(20)
    print("⚠️ Simulated crash triggered.")
    os.kill(os.getpid(), signal.SIGINT)

if __name__ == '__main__':
    threading.Thread(target=simulate_crash).start()
    app.run(debug=True,  use_reloader=False)
