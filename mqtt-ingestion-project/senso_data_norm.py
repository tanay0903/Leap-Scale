import json
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

def senso_convert_timestamp(value):
    try:
        if value is None:
            return int(datetime.now(timezone.utc).timestamp())
        
        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            return int(value) // 1000 if len(str(value)) > 10 else int(value)
        
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return int(dt.timestamp())
        except ValueError:
            pass

        try:
            dt = parsedate_to_datetime(value)
            return int(dt.timestamp())
        except Exception:
            pass

        custom_formats = ["%Y/%m/%d %H:%M:%S", "%d-%m-%Y %H:%M", "%m-%d-%Y %H:%M:%S"]
        for fmt in custom_formats:
            try:
                dt = datetime.strptime(value, fmt).replace(tzinfo=pytz.UTC)
                return int(dt.timestamp())
            except ValueError:
                continue

    except Exception:
        return int(datetime.now(timezone.utc).timestamp())

def senso_normalise_json(input_json):
    mapped_mfg = None
    mapped_device_list = None

    for key in input_json:
        canonical = senso_find_best_match(key)
        if canonical == "mfg":
            mapped_mfg = key
        elif canonical == "deviceList":
            mapped_device_list = key

    if not mapped_mfg or not mapped_device_list or \
        mapped_mfg not in input_json or mapped_device_list not in input_json:
        return None

    normalized_data = {
        "mfg": input_json.get(mapped_mfg),
        "deviceList": []
    }

    for device in input_json.get(mapped_device_list, []):
        device_mapped_keys = {raw_key: senso_find_best_match(raw_key) for raw_key in device.keys()}
        reverse_device_map = {v: k for k, v in device_mapped_keys.items()}

        normalized_device = {
            "deviceId": device.get(reverse_device_map.get("deviceId")) if device.get(reverse_device_map.get("deviceId"), "").strip() else None,
            "deviceType": device.get(reverse_device_map.get("deviceType")) if device.get(reverse_device_map.get("deviceType"), "").strip() else None,
            "mode": device.get(reverse_device_map.get("mode")) if device.get(reverse_device_map.get("mode"), "").strip() else None,
            "timestamp": senso_convert_timestamp(device.get(reverse_device_map.get("timestamp"))) if reverse_device_map.get("timestamp") in device else None,
            "createdTime": senso_convert_timestamp(device.get(reverse_device_map.get("createdTime"))) if reverse_device_map.get("createdTime") in device else None,
            "status": device.get(reverse_device_map.get("status")) if device.get(reverse_device_map.get("status"), "").strip() else None,
            "measurements": []
        }

        measurement_key = reverse_device_map.get("measurements")
        if not measurement_key:
            measurement_key = next((k for k in device if senso_find_best_match(k) == "measurements"), None)
        
        for measurement in device.get(measurement_key, []):
            measurement_mapped_keys = {raw_key: senso_find_best_match(raw_key) for raw_key in measurement.keys()}
            reverse_measurement_map = {v: k for k, v in measurement_mapped_keys.items()}

            normalized_measurement = {
                "paramName": measurement.get(reverse_measurement_map.get("paramName"), "unknown"),
                "value": measurement.get(reverse_measurement_map.get("value"), 1),
                "multiplier": measurement.get(reverse_measurement_map.get("multiplier"), 1),
                "unit": measurement.get(reverse_measurement_map.get("unit"), "unknown")
            }

            if normalized_measurement["paramName"] == "" or normalized_measurement["paramName"] == " ":
                if normalized_measurement["unit"].lower() in ["celcius", "kelvin", "fahrenheit", "c", "k", "f"]:
                    normalized_measurement["paramName"] = "temperature"

            if normalized_measurement["paramName"].lower() == "temperature":
                try:
                    value = float(normalized_measurement["value"])
                    unit = normalized_measurement["unit"].lower()
                    converted_val, converted_unit = senso_convert_temp_unit(value, unit)
                    normalized_measurement["value"] = str(converted_val)
                    normalized_measurement["unit"] = converted_unit
                except (ValueError, TypeError):
                    pass

            if normalized_measurement["paramName"] == "" or normalized_measurement["paramName"] == " ":
                if normalized_measurement["unit"] == "" or normalized_measurement["unit"] == " ":
                    return None

            # param_name = measurement.get(reverse_measurement_map.get("paramName"), "unknown")
            # unit = measurement.get(reverse_measurement_map.get("unit"), "unknown").lower()
            # value = float(measurement.get(reverse_measurement_map.get("value"), 1))

            # if param_name.lower() == "temperature" or unit in ["c", "f", "k", "celsius", "fahrenheit", "kelvin"]:
            #     param_name = "temperature"
            #     value, unit = senso_convert_temp_unit(value, unit)


            normalized_device["measurements"].append(normalized_measurement)

        normalized_data["deviceList"].append(normalized_device)

    return normalized_data
