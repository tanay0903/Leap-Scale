import json
import time
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
            "mfg": ["manufacture", "mgf", "production", "manf", "manu"],
            "deviceList": ["devices", "devList", "list", "dev_list", "d_list"],
            "deviceId": ["sensorId", "id", "d_id", "device_id", "sensor"],
            "deviceType": ["type", "dType", "device_tp", "d_t", "devType"],
            "mode": ["mode", "Mode", "mo", "md", "operationMode", "functionMode"],
            "timestamp": ["time", "ts", "utc", "utcTime", "rfc"],
            "createdTime": ["create", "created", "created_at", "creationTime", "generatedTime"],
            "status": ["state", "deviceStatus", "currentState", "device_state"],
            "measurements": ["measures", "sensorData", "readings", "metrics", "observations"],
            "paramName": ["parameter", "param_name", "name", "attribute"],
            "value": ["reading", "val", "data", "amount", "number"],
            "multiplier": ["mult", "factor", "scale", "multiplication_factor", "conversion"],
            "unit": ["units", "paramUnit", "parameter_unit", "unit_name", "unitType"]
        }

field_map = senso_load_field_map()

def senso_find_best_match(field_name):
    best_match = None
    highest_score = 0

    for canonical_field, synonyms in field_map.items():
        if field_name in synonyms:
            return canonical_field
        match, score, _ = process.extractOne(field_name, synonyms)
        if score > 80 and score > highest_score:
            best_match = canonical_field
            highest_score = score

    return best_match

def senso_convert_temp_unit(value, unit):
    if not unit or unit.lower() not in ["f", "fahrenheit", "k", "kelvin", "c", "celsius"]:
        unit = "celsius" 

    if unit.lower() in ["f", "fahrenheit"]:
        converted_val = round((value - 32) * 5/9, 2)
        return converted_val, "celsius"
    elif unit.lower() in ["k", "kelvin"]:
        converted_val = round(value - 273.15, 2)
        return converted_val, "celsius"
    else:  
        return value, "celsius"

def senso_convert_pressure_unit(value, unit):
    if not unit or unit.lower() not in ["bar", "psi", "atm", "pa", "pascal", "kpa", "mmhg", "inhg"]:
        unit = "Pa" 
    
    unit = unit.lower().strip()
    conversion_map = {
        "bar": 100000,
        "psi": 6894.757,
        "atm": 101325,
        "pa": 1,
        "pascal": 1,
        "kpa": 1000,
        "mmhg": 133.322,
        "inhg": 3386.389
    }

    if unit in conversion_map:
        return round(value * conversion_map[unit], 2), "Pa"
    else:
        return value, "Pa"

def senso_convert_timestamp(value):
    try:
        if value is None or str(value).strip() == "":
            converted_timestamp = int(time.time() * 1000)  
            return converted_timestamp

        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            value = int(value)
            converted_timestamp = value * (1000 if len(str(value)) <= 10 else 1)  
            return converted_timestamp

        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            converted_timestamp = int(dt.timestamp() * 1000) 
            return converted_timestamp
        except ValueError:
            pass

        try:
            dt = parsedate_to_datetime(value)
            converted_timestamp = int(dt.timestamp() * 1000) 
            return converted_timestamp
        except Exception:
            pass

        custom_formats = ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%d-%m-%Y %H:%M", "%m-%d-%Y %H:%M:%S"]
        for fmt in custom_formats:
            try:
                dt = datetime.strptime(value, fmt).replace(tzinfo=pytz.UTC)
                converted_timestamp = int(dt.timestamp() * 1000)  
                return converted_timestamp
            except ValueError:
                continue

    except Exception:
        converted_timestamp = int(time.time() * 1000)  
        return converted_timestamp 

def convert_keys_to_lowercase(obj):
    if isinstance(obj, dict):
        return {key.lower(): convert_keys_to_lowercase(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_keys_to_lowercase(item) for item in obj]
    else:
        return obj

def senso_normalise_json(input_json):
    input_json = convert_keys_to_lowercase(input_json)
    
    mapped_mfg = next((k for k in input_json if senso_find_best_match(k) == "mfg"), "mfg")
    mapped_device_list = next((k for k in input_json if senso_find_best_match(k) == "deviceList"), "deviceList")
    
    if "device_id" in input_json and "device_type" in input_json:
        converted_timestamp = senso_convert_timestamp(input_json.get("time", input_json.get("createdTime", "")))

        normalized_data = {
            "mfg": input_json.get("manufacturer", "unknown"),
            "deviceList": [
                {
                    "deviceId": input_json.get("device_id", "unknown"),
                    "deviceType": input_json.get("device_type", "unknown"),
                    "mode": input_json.get("mode", "Auto"),
                    "timestamp": converted_timestamp,
                    "createdTime": converted_timestamp, 
                    "status": input_json.get("status", "Okay"),
                    "measurements": []
                }
            ]
        }

        for param in ["temperature", "humidity", "pressure"]:
            if param in input_json:
                unit_key = f"{param}_unit"
                normalized_measurement = {
                    "paramName": param.capitalize(),
                    "value": round(float(input_json[param]), 2),
                    "multiplier": input_json.get("multiplier", 1),
                    "unit": input_json.get(unit_key, "unknown")
                }
                if param == "temperature":
                    normalized_measurement["value"], normalized_measurement["unit"] = senso_convert_temp_unit(
                        normalized_measurement["value"], normalized_measurement["unit"]
                    )
                elif param == "pressure":
                    normalized_measurement["value"], normalized_measurement["unit"] = senso_convert_pressure_unit(
                        normalized_measurement["value"], normalized_measurement["unit"]
                    )
                normalized_data["deviceList"][0]["measurements"].append(normalized_measurement)

        return normalized_data

    normalized_data = {"mfg": input_json.get(mapped_mfg, "unknown"), "deviceList": []}
    
    device_list = input_json.get(mapped_device_list, [])
    if isinstance(device_list, dict):
        device_list = list(device_list.values())

    for device in device_list:
        device_mapped_keys = {raw_key: senso_find_best_match(raw_key) for raw_key in device.keys()}
        reverse_device_map = {v: k for k, v in device_mapped_keys.items()}

        timestamp_value = device.get("timestamp") or device.get("time") or device.get("ts")
        created_time_value = device.get("createdTime") or device.get("created_time") or device.get("generatedTime")

        if isinstance(timestamp_value, (int, str)) and str(timestamp_value).strip():
            timestamp = senso_convert_timestamp(timestamp_value)
        else:
            timestamp = int(time.time() * 1000)  

        if isinstance(created_time_value, (int, str)) and str(created_time_value).strip():
            created_time = senso_convert_timestamp(created_time_value)
        else:
            created_time = timestamp

        normalized_device = {
            "deviceId": device.get(reverse_device_map.get("deviceId"), "unknown"),
            "deviceType": device.get(reverse_device_map.get("deviceType"), "unknown"),
            "mode": device.get(reverse_device_map.get("mode"), "unknown"),
            "timestamp": timestamp,
            "createdTime": created_time,
            "status": device.get(reverse_device_map.get("status"), "unknown"),
            "measurements": []
        }

        measurement_key = reverse_device_map.get("measurements", "measurements")
        measurements = device.get(measurement_key, [])

        if isinstance(measurements, dict):
            if all(isinstance(value, list) for value in measurements.values()):
                param_names = measurements.get("attris", [])
                values = measurements.get("nums", [])
                multipliers = measurements.get("facts", [1] * len(values))
                units = measurements.get("units", ["unknown"] * len(values))

                for i in range(len(param_names)):
                    normalized_measurement = {
                        "paramName": param_names[i],
                        "value": round(float(values[i]), 2),
                        "multiplier": multipliers[i],
                        "unit": units[i]
                    }
                    if normalized_measurement["paramName"].lower() == "temperature":
                        normalized_measurement["value"], normalized_measurement["unit"] = senso_convert_temp_unit(
                            float(normalized_measurement["value"]), normalized_measurement["unit"]
                        )
                    elif normalized_measurement["paramName"].lower() == "pressure":
                        normalized_measurement["value"], normalized_measurement["unit"] = senso_convert_pressure_unit(
                            float(normalized_measurement["value"]), normalized_measurement["unit"]
                        )
                    normalized_device["measurements"].append(normalized_measurement)
            else:
                measurements = list(measurements.values())

        for measurement in measurements:
            if not isinstance(measurement, dict):
                continue  
            measurement_mapped_keys = {raw_key: senso_find_best_match(raw_key) for raw_key in measurement.keys()}
            reverse_measurement_map = {v: k for k, v in measurement_mapped_keys.items()}
            normalized_measurement = {
                "paramName": measurement.get(reverse_measurement_map.get("paramName"), "unknown"),
                "value": round(float(measurement.get(reverse_measurement_map.get("value"), 1)), 2),
                "multiplier": measurement.get(reverse_measurement_map.get("multiplier"), 1),
                "unit": measurement.get(reverse_measurement_map.get("unit"), "unknown")
            }
            if normalized_measurement["paramName"].lower() == "temperature":
                normalized_measurement["value"], normalized_measurement["unit"] = senso_convert_temp_unit(
                    float(normalized_measurement["value"]), normalized_measurement["unit"]
                )
            elif normalized_measurement["paramName"].lower() == "pressure":
                normalized_measurement["value"], normalized_measurement["unit"] = senso_convert_pressure_unit(
                    float(normalized_measurement["value"]), normalized_measurement["unit"]
                )
            normalized_device["measurements"].append(normalized_measurement)

        normalized_data["deviceList"].append(normalized_device)

    return normalized_data
