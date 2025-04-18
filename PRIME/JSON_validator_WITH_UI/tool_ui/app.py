from flask import Flask, render_template, request, jsonify
import json
from tool import validateData

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

if __name__ == '__main__':
    app.run(host="192.168.0.109", port=5000, debug=True)
