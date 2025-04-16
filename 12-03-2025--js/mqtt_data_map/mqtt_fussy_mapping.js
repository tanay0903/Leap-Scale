require("dotenv").config();
const mqtt = require('mqtt');
const Fuse = require('fuse.js');

const brokerChoice = process.env.MQTT_BROKER_CHOICE || "mosquitto";

const brokers = {
    hivemq: "mqtt://broker.hivemq.com:1883",
    mosquitto: "mqtt://test.mosquitto.org:1883"
};

const brokerUrl = brokers[brokerChoice] || brokers.mosquitto;
const topic = process.env.MQTT_TOPIC || "iot/sensor/data";

const client = mqtt.connect(brokerUrl);

const fieldMappings = {
    "mfg": ["manufacture", "mgf", "production", "manf", "man","manu", "maker", "prod_maker"],
    "deviceList": ["devices", "devList", "list", "dev_list","d_list", "devices", "dev_arr"],
    "deviceId": ["sensorId", "id", "d_id", "device_id", "sensor","deviceID", "uid"],
    "deviceType" : ["type", "dType", "device_tp", "d_t", "devType"],
    "mode": ["mode", "Mode", "mo", "md","me","m","operationMode", "functionMode","opMode"],
    "timestamp": ["time", "ts", "utc", "utcTime", "rfc","epoch"],
    "createdTime": ["create", "created", "created_at", "creationTime", "generatedTime"],
    "status": ["state", "deviceStatus", "currentState", "device_state","state_dev", "devState"],
    "measurements": ["measures", "sensorData", "readings", "metrics", "observations","meas"],
    "paramName": ["parameter", "param_name", "name", "attribute","name_para", "param", "parameter_name", "paramName", "param_name"],
    "value": ["reading", "val", "data", "amount", "number","readValue", "readUnit"],
    "multiplier": ["mult","factor","scale", "multiplication_factor", "conversion","multiplier","multiplier_factor","multiplierValue","mul"],
    "unit":["units", "paramUnit", "parameter_unit", "unit_name", "unitType","unit_para", "unitType", "uniType"]
};


function mapKey(key) {
    for (const standardKey in fieldMappings) {
        if (fieldMappings[standardKey].includes(key)) {
            return standardKey;
        }
    }
    return key;
}


function processParameters(obj) {
    let paramStorage = {};
    Object.keys(obj).forEach(key => {
        let mappedKey = mapKey(key);
        paramStorage[mappedKey] = obj[key];
    });
    return paramStorage;
}


function processMeasurements(measurements) {
    return measurements.map(measurement => processParameters(measurement));
}


function assembleData(rawData) {
    let processedData = processParameters(rawData);
    
    if (processedData.deviceList) {
        processedData.deviceList = processedData.deviceList.map(device => {
            let processedDevice = processParameters(device);
            if (processedDevice.measurements) {
                processedDevice.measurements = processMeasurements(processedDevice.measurements);
            }
            return processedDevice;
        });
    }
    return processedData;
}



client.on("connect", () => {
    console.log(`Connected to MQTT broker at ${brokerUrl}`);
    client.subscribe(topic, (err) => {
        if (!err) {
            console.log(`Subscribed to topic: ${topic}`);
        }
    });
});

client.on('message', (topic, message) => {
    try {
        const rawData = JSON.parse(message.toString());
        const standardizedData = assembleData(rawData);

        
        console.log("Raw Data:", JSON.stringify(rawData, null, 2));
        console.log("Standardized Data:", JSON.stringify(standardizedData, null, 2));
    } catch (error) {
        console.error("Error processing MQTT message:", error);
    }
});
