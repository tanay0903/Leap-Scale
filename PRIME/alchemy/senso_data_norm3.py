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

    # Dynamically resolve manufacturer
    mfg_key = senso_find_best_match("mfg")
    normalized_data["mfg"] = input_json.get(mfg_key, "Unknown Manufacturer")

    normalized_data["deviceList"] = []

    # Dynamically resolve device list key
    device_list_key = senso_find_best_match("deviceList")
    device_list = input_json.get(device_list_key, {})

    # Handle both dictionary and list formats for `deviceList`
    if isinstance(device_list, dict):
        device_list = device_list.values()

    for device in device_list:
        if not isinstance(device, dict):
            raise ValueError("Each device entry in `deviceList` must be a dictionary.")

        normalized_device = OrderedDict()

        # Dynamically resolve deviceId
        device_id_key = senso_find_best_match("deviceId")
        normalized_device["deviceId"] = device.get(device_id_key, "Unknown Device")

        # Dynamically resolve deviceType
        device_type_key = senso_find_best_match("deviceType")
        normalized_device["deviceType"] = device.get(device_type_key, "Unknown Type")

        # Dynamically resolve mode
        mode_key = senso_find_best_match("mode")
        raw_mode = device.get(mode_key, "Auto")
        normalized_device["mode"] = raw_mode.capitalize() if raw_mode.lower() in ["auto", "manual"] else "Auto"

        # Dynamically resolve timestamps
        timestamp_key = senso_find_best_match("timestamp")
        created_time_key = senso_find_best_match("createdTime")
        normalized_device["timestamp"] = senso_convert_timestamp(device.get(timestamp_key))
        normalized_device["createdTime"] = senso_convert_timestamp(device.get(created_time_key))

        # Dynamically resolve status
        status_key = senso_find_best_match("status")
        normalized_device["status"] = device.get(status_key, "Unknown Status")

        # Process measurements
        measurement_key = senso_find_best_match("measurements")
        normalized_device["measurements"] = []

        if measurement_key in device:
            measurements = device[measurement_key]
            param_names = measurements.get(senso_find_best_match("paramName"), [])
            values = measurements.get(senso_find_best_match("value"), [])
            multipliers = measurements.get(senso_find_best_match("multiplier"), [])
            units = measurements.get(senso_find_best_match("unit"), [])

            for i in range(len(param_names)):
                normalized_measurement = OrderedDict()
                normalized_measurement["paramName"] = param_names[i] if i < len(param_names) else "Unknown Parameter"
                value = values[i] if i < len(values) else 0.0
                unit = units[i] if i < len(units) else "unknown"
                multiplier = multipliers[i] if i < len(multipliers) else 1
                
                try:
                    value, unit = senso_convert_temp_unit(value, unit)
                except ValueError:
                    value, unit = value, "unknown"

                normalized_measurement["value"] = value
                normalized_measurement["unit"] = unit
                normalized_measurement["multiplier"] = multiplier
                normalized_device["measurements"].append(normalized_measurement)

        normalized_data["deviceList"].append(normalized_device)

    return normalized_data
