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
        if (!err) {
            console.log(`Subscribed to topic: ${topic}`);
        }
    });
});

function formatOutputData(normalizedData) {
    return {
        mfg: normalizedData.manufacturer || "Unknown",
        deviceList: normalizedData.device_list?.map(device => ({
            deviceId: device.device_id || "Unknown",
            deviceType: device.device_type || "Unknown",
            mode: device.operation_mode || "Unknown",
            timestamp: device.timestamp || null,
            createdTime: device.createdTime || null,
            status: device.state || "Unknown",
            measurements: device.metric?.map(measurement => ({
                paramName: measurement.metric_name || "Unknown",
                value: measurement.metric_value || "Unknown",
                multiplier: 1, 
                unit: measurement.unit || "Unknown"
            })) || []
        })) || []
    };
}

client.on("message", (topic, message) => {
    console.log("\n Received Message on", topic);
    const rawData = JSON.parse(message.toString());

    const normalizedData = normalizeJson(rawData);
    const formattedData = formatOutputData(normalizedData);
    
    console.log("RAW INPUT DATA:", JSON.stringify(rawData, null, 2));
    console.log("\n Normalized Data:", JSON.stringify(normalizedData, null, 2));
    // console.log("Normalized Data:",JSON.stringify(formattedData));
});

module.exports = { client };
