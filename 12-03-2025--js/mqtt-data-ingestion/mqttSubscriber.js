require("dotenv").config();
const mqtt = require("mqtt");
const { normalizeData, storeDataInMySQL } = require("./dataProcessor");

// Choose the broker ("hivemq" or "mosquitto")
const brokerChoice = process.env.MQTT_BROKER_CHOICE || "mosquitto";

const brokers = {
    hivemq: "mqtt://broker.hivemq.com:1883",
    mosquitto: "mqtt://test.mosquitto.org:1883"
};

const brokerUrl = brokers[brokerChoice] || brokers.mosquitto;
const topic = process.env.MQTT_TOPIC || "iot/sensor/data";

const client = mqtt.connect(brokerUrl);

client.on("connect", () => {
    console.log(`Connected to MQTT broker at ${brokerUrl}`);
    client.subscribe(topic, (err) => {
        if (!err) {
            console.log(`Subscribed to topic: ${topic}`);
        }
    });
});

client.on("message", async (topic, message) => {
    try {
        console.log("Received raw message:", message.toString());
        const rawMessage = message.toString();
        const normalizedData = normalizeData(message.toString());
        console.log("🛠️ Debugging: Data before inserting into MySQL:", {...normalizedData, rawData: rawMessage});
        await storeDataInMySQL(normalizedData, rawMessage);
    } catch (error) {
        console.error("Error processing message:", error);
    }
});
