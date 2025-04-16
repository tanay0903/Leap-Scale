import json
from collections import OrderedDict
from rapidfuzz import process
from datetime import datetime, timezone
import pytz
from email.utils import parsedate_to_datetime

def senso_load_field_map(file_path="senso_config.json"):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {
    "mfg": ["manufacture", "mgf", "production", "manf", "man","manu", "maker", "prod_maker"],
    "deviceList": ["devices", "devList", "list", "dev_list","d_list", "devices", "dev_arr"],
    "deviceId": ["sensorId", "id", "d_id", "device_id", "sensor","deviceID", "uid"],
    "deviceType" : ["type", "dType", "device_tp", "d_t", "devType"],
    "mode": ["mode", "Mode", "mo", "md", "operationMode", "functionMode","opMode"],
    "timestamp": ["time", "ts", "utc", "utcTime", "rfc","epoch"],
    "createdTime": ["create", "created", "created_at", "creationTime", "generatedTime"],
    "status": ["state", "deviceStatus", "currentState", "device_state","state_dev", "devState"],
    "measurements": ["measures", "sensorData", "readings", "metrics", "observations","meas"],
    "paramName": ["parameter", "param_name", "name", "attribute","name_para", "param", "parameter_name", "paramName", "param_name"],
    "value": ["reading", "val", "data", "amount", "number","readValue"],
    "multiplier": ["mult", "factor","scale", "multiplication_factor", "conversion"],
    "unit": ["units", "paramUnit", "parameter_unit", "unit_name", "unitType","unit_para", "unitType", "uniType"]
}

field_map = senso_load_field_map()

def senso_find_best_match(field_name):
    for canonical_field, synonyms in field_map.items():
        if field_name in synonyms:
            return canonical_field
        match, score, _ = process.extractOne(field_name, synonyms)
        if score > 75:
            return canonical_field
    return field_name

def senso_convert_temp_unit(value, unit):
    if not unit:
        raise ValueError("Unit is missing. Conversion cannot proceed.")
    unit = unit.lower()

    try:
        value = float(value) 
    except ValueError:
        raise ValueError("Invalid value for temperature. Conversion cannot proceed.")

    if unit in ["f", "fahrenheit"]:  
        return round((value - 32) * 5/9, 2), "celsius"
    elif unit in ["k", "kelvin"]:  
        return round(value - 273.15, 2), "celsius"
    elif unit in ["c", "celsius"]:
        return value, "celsius"
    raise ValueError(f"Unrecognized unit: {unit}")

def senso_convert_timestamp(value):  
    try:
        if value is None:
            return int(datetime.now(timezone.utc).timestamp()) * 1000

        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            value = int(value)
            return value * 1000 if len(str(value)) < 13 else value

        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return int(dt.timestamp()) * 1000
        except ValueError:
            pass

        try:
            dt = parsedate_to_datetime(value)
            return int(dt.timestamp()) * 1000
        except Exception:
            pass

        custom_formats = ["%Y/%m/%d %H:%M:%S", "%d-%m-%Y %H:%M", "%m-%d-%Y %H:%M:%S"]
        for fmt in custom_formats:
            try:
                dt = datetime.strptime(value, fmt).replace(tzinfo=pytz.UTC)
                return int(dt.timestamp()) * 1000
            except ValueError:
                continue

    except Exception:
        return int(datetime.now(timezone.utc).timestamp()) * 1000


def senso_normalise_json(input_json):
    # Initialize normalized data
    normalized_data = {
        "mfg": input_json.get("manufacturer", "Unknown Manufacturer"),
        "deviceList": []
    }

    # Detect input format and normalize
    if "device_id" in input_json and "device_type" in input_json:
        # Type 1 Format
        device = {
            "deviceId": input_json.get("device_id", "Unknown Device"),
            "deviceType": input_json.get("device_type", "Unknown Type"),
            "mode": "Auto",  # Default
            "timestamp": senso_convert_timestamp(input_json.get("timestamp")),
            "createdTime": senso_convert_timestamp(input_json.get("timestamp")),
            "status": "Okay",  # Default
            "measurements": []
        }

        # Normalize measurements
        if "temperature" in input_json:
            temp_value, temp_unit = senso_convert_temp_unit(
                input_json["temperature"], input_json["temperature_unit"]
            )
            device["measurements"].append({
                "paramName": "Temperature",
                "value": temp_value,
                "multiplier": 1,
                "unit": temp_unit
            })

        if "humidity" in input_json:
            device["measurements"].append({
                "paramName": "Humidity",
                "value": input_json["humidity"],
                "multiplier": 1,
                "unit": input_json["humidity_unit"]
            })

        normalized_data["deviceList"].append(device)

    elif "deviceList" in input_json:
        # Type 2 Format
        normalized_data["mfg"] = input_json.get("mfg", "Unknown Manufacturer")
        for device in input_json.get("deviceList", []):
            normalized_device = {
                "deviceId": device.get("deviceId", "Unknown Device"),
                "deviceType": device.get("deviceType", "Unknown Type"),
                "mode": device.get("mode", "Auto"),
                "timestamp": device.get("timestamp", senso_convert_timestamp(None)),
                "createdTime": device.get("createdTime", senso_convert_timestamp(None)),
                "status": device.get("status", "Okay"),
                "measurements": []
            }

            # Normalize measurements
            for measurement in device.get("measurements", []):
                normalized_device["measurements"].append({
                    "paramName": measurement.get("paramName", "Unknown Parameter"),
                    "value": measurement.get("value", 0),
                    "multiplier": measurement.get("multiplier", 1),
                    "unit": measurement.get("unit", "unknown")
                })

            normalized_data["deviceList"].append(normalized_device)

    else:
        print("Unrecognized input format. Skipping normalization.")
        return None

    return normalized_data

