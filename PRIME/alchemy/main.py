import os
import json
import paho.mqtt.client as mqtt
from senso_data_norm2 import senso_normalise_json
import requests
from dotenv import load_dotenv

load_dotenv()

BROKERS = {
    "hivemq": "broker.hivemq.com",
    "mosquitto": "test.mosquitto.org",
    "sparrow": "sparrow.sensoyo.io"
}

BROKER_CHOICE = os.getenv("MQTT_BROKER_CHOICE", "mosquitto")
BROKER_HOST = BROKERS.get(BROKER_CHOICE, "test.mosquitto.org")
PORT = 1883
USERNAME = "squmr0w"  
PASSWORD = "SparrowIOT@123"  
TOPIC = os.getenv("MQTT_TOPIC", "iot/sensor/data")

TARGET_URL = "https://sparrow.sensoyo.io/DataCollection/test"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker ({BROKER_HOST})")
        client.subscribe(TOPIC)
        print(f"Subscribed to topic: {TOPIC}")
        print("Waiting for incoming messages...")
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        raw_payload = msg.payload.decode("utf-8")
        print(f"\n Received raw message:\n{raw_payload}")

        raw_data = json.loads(raw_payload)
        print("JSON is valid.")

        normalized_data = senso_normalise_json(raw_data)

        if normalized_data:
            print(f"Normalized Data:\n{json.dumps(normalized_data, indent=2)}")
            send_data_to_api(normalized_data)
        else:
            print("Normalization failed, skipping...")

    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Check the JSON structure of the received message.")
    except ValueError as e:
        print(f"Value Error: {e}")
    except Exception as e:
        print(f"Error processing message: {e}")


def send_data_to_api(data):
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(TARGET_URL, json=data, headers=headers, timeout=10)

        if response.status_code == 200:
            print(f"Successfully sent data to API: {TARGET_URL}")
        else:
            print(f"API Response {response.status_code}: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to send data to API: {e}")

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)  
client.enable_logger()
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to MQTT Broker: {BROKER_HOST}")
client.connect(BROKER_HOST, PORT, keepalive=120)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n Exit")