require("dotenv").config();
const mqtt = require("mqtt");
const { saveToDatabase } = require("./db");

const MQTT_BROKER = process.env.MQTT_BROKER || "mqtt://localhost";
const MQTT_TOPIC_SUB = "sensor/data"; 
const MQTT_TOPIC_PUB = "sensor/normalized"; 

const client = mqtt.connect(MQTT_BROKER);

client.on("connect", () => {
    console.log(`✅ Connected to MQTT broker at ${MQTT_BROKER}`);
    client.subscribe(MQTT_TOPIC_SUB, (err) => {
        if (!err) {
            console.log(`📡 Subscribed to topic: ${MQTT_TOPIC_SUB}`);
        }
    });
});

client.on("message", async (topic, message) => {
    console.log(`📥 Received Data: ${message.toString()}`);
    try {
        const inputData = JSON.parse(message.toString());
        const normalizedData = normalizeData(inputData);

        // Store in MySQL
        await saveToDatabase(
            normalizedData.deviceId,
            normalizedData.temperature,
            normalizedData.unit,
            normalizedData.timestamp
        );

        // Publish normalized data
        client.publish(MQTT_TOPIC_PUB, JSON.stringify(normalizedData));
        console.log(`🚀 Published Normalized Data:`, normalizedData);
    } catch (error) {
        console.error(`❌ Error: ${error.message}`);
    }
});


// convert To Celsius 
function convertToCelsius(value, unit) {
    if (unit === "F") return (value - 32) * (5 / 9);
    if (unit === "K") return value - 273.15;
    return value;
}


// normalize Data4
function normalizeData(input) {
    if (!input.deviceId || !input.temperature || !input.unit || !input.timestamp) {
        throw new Error("Missing required fields: deviceId, temperature, unit, timestamp");
    }

    return {
        deviceId: input.deviceId,
        temperature: parseFloat(convertToCelsius(input.temperature, input.unit).toFixed(2)),
        unit: "C",
        timestamp: new Date(input.timestamp).toISOString().slice(0, 19).replace("T", " "),
    };
}
