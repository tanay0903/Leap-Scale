import json
import paho.mqtt.client as mqtt
from senso_data_norm import senso_normalise_json
import requests

# MQTT config
# MQTT_BROKER = "ronny.iotclay.net" 
# MQTT_PORT = 1883
# MQTT_USERNAME = "ronnyiotMQTT"  
# MQTT_PASSWORD = "Iot@MQTT"  
# MQTT_PUBLISH_TOPIC = "DataCollection/test"

MQTT_BROKER = "sparrow.sensoyo.io" 
MQTT_PORT = 1883
MQTT_USERNAME = "squmr0w"  
MQTT_PASSWORD = "SparrowIOT@123"  
MQTT_SUBSCRIBE_TOPIC = "sensoyo/data"

# URL for HTTP requests
# url = "https://ronny.iotclay.net/DataCollection/test"
url = "https://sparrow.sensoyo.io/DataCollection/test"
headers = {"Content-Type": "application/json"}

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe(MQTT_SUBSCRIBE_TOPIC)
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    print("📩 Received MQTT Message:", msg.payload.decode())

    try:
        raw_data = json.loads(msg.payload.decode())
        normalized_data = senso_normalise_json(raw_data)

        if normalized_data:
            normalized_json = json.dumps(normalized_data, indent=2)
            print("🔄 Normalized Data:", normalized_json)

            # client.publish(MQTT_PUBLISH_TOPIC, normalized_json)
            # print(f"✅ Published normalized data to {MQTT_PUBLISH_TOPIC}")

            # Send HTTP request
            response = requests.post(url, data=normalized_json, headers=headers)
            print(f"🌐 HTTP Response: {response.status_code}")
            print(f"{response.text}\n")
        else:
            print("❌ Data normalization failed.")

    except json.JSONDecodeError:
        print("❌ JSON Decode Error: Invalid JSON received.")
    except Exception as e:
        print("❌ General Error:", e)

client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)  
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 120)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("🛑 MQTT Subscriber Stopped.")
except Exception as e:
    print("❌ MQTT Loop Error:", e)
