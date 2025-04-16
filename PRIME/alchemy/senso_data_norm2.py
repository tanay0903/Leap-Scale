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
            "mfg": ["manufacture", "mgf", "production", "manf", "manu"],
            "deviceList": ["devices", "devList", "list", "dev_list", "d_list"],
            "deviceId": ["sensorId", "id", "d_id", "device_id", "sensor"],
            "deviceType": ["type", "dType", "device_tp", "d_t", "devType"],
            "mode": ["mode", "Mode", "mo", "md", "operationMode", "functionMode"],
            "timestamp": ["time", "ts", "utc", "utcTime", "rfc"],
            "createdTime": ["create", "created", "created_at", "creationTime", "generatedTime"],
            "status": ["state", "deviceStatus", "currentState", "device_state","state_dev"],
            "measurements": ["measures", "sensorData", "readings", "metrics", "observations"],
            "paramName": ["parameter", "param_name", "name", "attribute"],
            "value": ["reading", "val", "data", "amount", "number"],
            "multiplier": ["mult", "factor", "scale", "multiplication_factor", "conversion"],
            "unit": ["units", "paramUnit", "parameter_unit", "unit_name", "unitType"]
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
    normalized_data = OrderedDict()

    
    mfg_key = senso_find_best_match("mfg")
    if mfg_key in input_json:
        normalized_data["mfg"] = input_json[mfg_key]
    else:
        for synonym in field_map.get("mfg", []):
            if synonym in input_json:
                normalized_data["mfg"] = input_json[synonym]
                break
        else:
            normalized_data["mfg"] = "Unknown Manufacturer"

    normalized_data["deviceList"] = []

    
    device_list_key = next((key for key in input_json if senso_find_best_match(key) == "deviceList"), None)
    if not device_list_key:
        raise ValueError("Device list key not found in input JSON.")

    for device in input_json.get(device_list_key, []):
        normalized_device = OrderedDict()

        device_id = None
        device_id_key = senso_find_best_match("deviceId")
        if device_id_key in device:
            device_id = device[device_id_key]
        else:
            for synonym in field_map.get("deviceId", []):
                if synonym in device:
                    device_id = device[synonym]
                    break
        normalized_device["deviceId"] = device_id if device_id else "Unknown Device"

        # Resolve deviceType dynamically
        device_type = None
        device_type_key = senso_find_best_match("deviceType")

        # Directly use the resolved key if it exists in the device
        if device_type_key and device_type_key in device:
            device_type = device[device_type_key]
        else:
            # Fall back to searching synonyms explicitly
            for synonym in field_map.get("deviceType", []):
                if synonym in device:
                    device_type = device[synonym]
                    break

        # Default to "Unknown Type" if no match is found
        normalized_device["deviceType"] = device_type if device_type else "Unknown Type"


        mode = None
        mode_key = senso_find_best_match("mode")
        if mode_key in device:
            mode = device[mode_key]
        else:
            for synonym in field_map.get("mode", []):
                if synonym in device:
                    mode = device[synonym]
                    break
    
        normalized_device["mode"] = mode.capitalize() if mode and mode.lower() in ["auto", "manual"] else "Auto"
        normalized_device["timestamp"] = senso_convert_timestamp(device.get(senso_find_best_match("timestamp")))
        normalized_device["createdTime"] = senso_convert_timestamp(device.get(senso_find_best_match("createdTime")))

        measurement_key = next((key for key in device if senso_find_best_match(key) == "measurements"), None)
        normalized_device["measurements"] = []
        if measurement_key:
            for measurement in device[measurement_key]:
                normalized_measurement = OrderedDict()
                normalized_measurement["paramName"] = senso_find_best_match(
                    measurement.get("name_para", measurement.get("param", measurement.get("name", "Unknown Parameter")))
                )

                value_field = measurement.get("readValue", measurement.get("Value", "0"))
                try:
                    value = float(value_field)
                except ValueError:
                    value = 0.0
                unit_field = measurement.get("unit_para", measurement.get("paramunit", measurement.get("unit", "celsius")))
                try:
                    value, unit = senso_convert_temp_unit(value, unit_field)
                except ValueError:
                    value, unit = value, "celsius"

                normalized_measurement["value"] = value
                normalized_measurement["unit"] = unit
                normalized_measurement["multiplier"] = measurement.get(senso_find_best_match("multiplier"), 1)

                normalized_device["measurements"].append(normalized_measurement)

        normalized_data["deviceList"].append(normalized_device)

    return normalized_data
