import os
import json
import paho.mqtt.client as mqtt
from senso_data_norm_ECE import senso_normalise_json
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ENABLE_API_FORWARDING = os.getenv("ENABLE_API_FORWARDING", "False").lower() == "true"

BROKERS = {
    "hivemq": "broker.hivemq.com",
    "mosquitto": "test.mosquitto.org",
    "sparrow": "sparrow.sensoyo.io",
    "ronnyiot": "ronny.iotclay.net"
}

BROKER_CHOICE = os.getenv("MQTT_BROKER_CHOICE", "mosquitto")
BROKER_HOST = BROKERS.get(BROKER_CHOICE, "test.mosquitto.org")
PORT = 1883
USERNAME = os.getenv("MQTT_USERNAME", "ronnyiotMQTT")
PASSWORD = os.getenv("MQTT_PASSWORD", "Iot@MQTT")
TOPIC = os.getenv("MQTT_TOPIC", "iot/sensor/data")

# TARGET_URL = os.getenv("TARGET_URL", "https://ronny.iotclay.net/DataCollection/test")
TARGET_URL = os.getenv("TARGET_URL", "https://sparrow.sensoyo.io/DataCollection/test")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"Connected to MQTT Broker: {BROKER_HOST}")
        client.subscribe(TOPIC)
        logging.info(f"Subscribed to topic: {TOPIC}")
        logging.info("Waiting for incoming messages...")
    else:
        logging.error(f"Connection failed with code {rc}")


def on_message(client, userdata, msg):
    try:
        raw_payload = msg.payload.decode("utf-8")
        logging.info(f"Received raw message: {raw_payload}")

        raw_data = json.loads(raw_payload)
        logging.info("JSON is valid.")

        normalized_data = senso_normalise_json(raw_data)

        if normalized_data:
            logging.info(f"Normalized Data:\n{json.dumps(normalized_data, indent=2)}")
            if ENABLE_API_FORWARDING:
                send_data_to_api(normalized_data)
            else:
                logging.info("API forwarding is disabled.")
        else:
            logging.warning("Normalization failed. Skipping message.")

    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error: {e}")
    except ValueError as e:
        logging.error(f"Value Error: {e}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")


def send_data_to_api(data):
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(TARGET_URL, json=data, headers=headers, timeout=10)

        if response.status_code == 200:
            logging.info(f"Successfully sent data to API: {TARGET_URL}")
        else:
            logging.error(f"Failed to send data to API. Status code: {response.status_code}, Response: {response.text}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending data to API: {e}")


if __name__ == "__main__":
    client = mqtt.Client()
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    logging.info(f"Connecting to MQTT Broker: {BROKER_HOST}")
    try:
        client.connect(BROKER_HOST, PORT, keepalive=120)
        client.loop_forever()
    except KeyboardInterrupt:
        logging.info("Exiting gracefully...")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

