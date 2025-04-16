import json
import os
import sys
from jsonschema import Draft7Validator 
from difflib import get_close_matches
import logging

def get_file_path():
    return input("Enter the path of the JSON file: ").strip()

def get_valid_file():
    while True:
        file_path = input("Enter the full path to the file (\"bye\" to exit): ").strip()
        if os.path.isfile(file_path):
            #print(f"File found: {file_path}")
            return file_path
        elif file_path=="bye":
            return file_path
        else:
            print("\n!!! File not found. Please check the path and try again.\n")

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def get_line_number(json_str, key):
    lines = json_str.split('\n')
    for i, line in enumerate(lines, start=1):
        if f'"{key}"' in line:
            return i
    return "Unknown"

schema = {
    "type": "object",
    "properties": {
        "mfg": {"type": "string", "minLength": 1},
        "deviceList": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "deviceId": {"type": "string", "minLength": 1},
                    "deviceType": {"type": "string", "minLength": 1},
                    "mode": {"type": "string", "enum": ["Auto", "Manual"]},
                    "timestamp": {"type": "integer", "minimum": 0},
                    "createdTime": {"type": "integer", "minimum": 0},
                    "status": {"type": "string", "minLength": 1},
                    "measurements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "paramName": {"type": "string", "minLength": 1},
                                "value": {"type": ["number", "string"]},
                                "multiplier": {"type": "number", "minimum": 1},
                                "unit": {"type": "string", "minLength": 1}
                            },
                            "required": ["paramName", "value", "multiplier", "unit"]
                        }
                    }
                },
                "required": ["deviceId", "deviceType", "mode", "timestamp", "createdTime", "status", "measurements"]
            }
        }
    },
    "required": ["mfg", "deviceList"]
}

def correct_key_spelling(provided_keys, expected_keys, json_str):
    corrections = {}
    for key in provided_keys:
        if key not in expected_keys:
            closest_match = get_close_matches(key, expected_keys, n=1, cutoff=0.4)
            if closest_match:
                line_number = get_line_number(json_str, key)
                corrections[key] = (closest_match[0], line_number)
    return corrections

def validate_mfg_location(data, json_str):
    errors = []
    for device_index, device in enumerate(data.get("deviceList", [])):
        if "mfg" in device:
            line_number = get_line_number(json_str, "mfg")
            errors.append(f"line {line_number}: 'mfg' should not be inside deviceList[{device_index}]. Move it to the root level.")
    return errors

def validate_timestamp(data, json_str):
    errors = []
    for device in data.get("deviceList", []):
        timestamp = device.get("timestamp")
        if isinstance(timestamp, int) and not (1000000000000 <= timestamp <= 9999999999999):
            line_number = get_line_number(json_str, "timestamp")
            errors.append(f"line {line_number}: Invalid timestamp in device {device.get('deviceId', 'Unknown')}: Must be a 13-digit integer in milliseconds.")
    return errors

def validate_measurements(data, json_str):
    errors = []
    for device_index, device in enumerate(data.get("deviceList", [])):
        measurements_path = f"deviceList[{device_index}].measurements"
        if "measurements" not in device or not isinstance(device["measurements"], list):
            line_number = get_line_number(json_str, "measurements")
            errors.append(f"line {line_number}: Schema Error: {measurements_path} - Must be an array of measurement objects.")
            continue  
        for measurement_index, measurement in enumerate(device["measurements"]):
            measurement_path = f"{measurements_path}[{measurement_index}]"
            if not isinstance(measurement, dict):
                line_number = get_line_number(json_str, "measurements")
                errors.append(f"line {line_number}: Schema Error: {measurement_path} - Must be an object.")
                continue  
            missing_keys = [key for key in ["paramName", "value", "multiplier", "unit"] if key not in measurement]
            for key in missing_keys:
                line_number = get_line_number(json_str, key)
                errors.append(f"line {line_number}: Schema Error: {measurement_path} - '{key}' is a required property.")
    return errors

def recursive_key_check(data, schema_properties, json_str, parent_key=""):
    errors = []
    if isinstance(data, dict):
        corrections = correct_key_spelling(data.keys(), schema_properties.keys(), json_str)
        for wrong, (right, line_number) in corrections.items():
            errors.append(f"line {line_number}: {wrong} is spelled wrongly, change spelling to {right}")
        for key, value in data.items():
            if key in schema_properties:
                if "properties" in schema_properties[key]: 
                    errors.extend(recursive_key_check(value, schema_properties[key]["properties"], json_str, parent_key=f"{parent_key}{key}.")) 
                elif "items" in schema_properties[key]:  
                    errors.extend(recursive_key_check(value, schema_properties[key]["items"]["properties"], json_str, parent_key=f"{parent_key}{key}[]."))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, dict):
                errors.extend(recursive_key_check(item, schema_properties, json_str, parent_key=f"{parent_key}[{index}]."))
    return errors

def validateData(data, json_str):
    key_errors = recursive_key_check(data, schema["properties"], json_str)
    schema_errors = set()
    try:
        validator = Draft7Validator(schema)
        for error in validator.iter_errors(data):
            field_name = "root" if not error.path else "".join(f"[{part}]" if isinstance(part, int) else str(part) for part in error.path)
            field_name = field_name.replace("].[", "][").replace(".[", "[").replace("[.", "[")
            line_number = get_line_number(json_str, str(error.path[-1]) if error.path else "root")
            schema_errors.add(f"Schema Error: {field_name} - {error.message}")
    except Exception as e:
        schema_errors.add(f"Schema Error: root - {str(e)}")

    timestamp_errors = validate_timestamp(data, json_str) if not any("timestamp" in e for e in schema_errors) else []
    mfg_location_errors = validate_mfg_location(data, json_str)
     
    all_errors = list(key_errors) + list(schema_errors) + list(timestamp_errors) + list(mfg_location_errors)
    return "\n".join(all_errors) if all_errors else "JSON is valid."

def main():
    #file_path = get_file_path()
    file_path = get_valid_file()
    if (file_path=="bye"):
        sys.exit(1)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            json_str = file.read()
            data = json.loads(json_str)
        validation_results = validateData(data, json_str)
        print("\nValidation Results:\n======================")
        print(validation_results)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Unexpected error: {e}")
    print("\nExiting Sensoyo JSON Validator.")

if __name__ == "__main__":
    main()
