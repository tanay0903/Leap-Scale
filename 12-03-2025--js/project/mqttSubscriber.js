require("dotenv").config();
const mqtt = require("mqtt");
const { normalizeJson } = require("./normalizeData");


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
        if (!err) console.log(`Subscribed to topic: ${topic}`);
    });
});


function formatOutputData(normalizedData) {
    return {
        mfg: normalizedData.mfg || "Unknown",
        deviceList: (normalizedData.deviceList || []).map(device => ({
            deviceId: device.deviceId || "Unknown",
            deviceType: device.deviceType || "Unknown",
            mode: device.mode || "Unknown",
            timestamp: device.timestamp || null,
            createdTime: device.createdTime || null,
            status: device.status || "Unknown",
            measurements: (device.measurements || []).map(measurement => ({
                paramName: measurement.paramName || "Unknown",
                value: measurement.value || "Unknown",
                multiplier: measurement.multiplier || 1,
                unit: measurement.unit || "Unknown"
            }))
        }))
    };
}

// MQTT Message Handler
client.on("message", (topic, message) => {
    console.log("\n📩 Received Message on", topic);
    try {
        const rawData = JSON.parse(message.toString());
        const normalizedData = normalizeJson(rawData);
        const formattedData = formatOutputData(normalizedData);

        console.log(" RAW INPUT DATA:", JSON.stringify(rawData, null, 2));
        console.log(" Normalized Data:", JSON.stringify(normalizedData, null, 2));
        console.log(" Final Formatted Data:", JSON.stringify(formattedData, null, 2));
    } catch (error) {
        console.error(" Error processing message:", error);
    }
});

module.exports = { client };
