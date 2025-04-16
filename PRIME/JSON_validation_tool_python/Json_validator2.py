import sys
import json

FIELD_VARIATIONS = {
    "mfg": ["manufacture", "mgf", "production", "manf", "man", "manu", "maker", "prod_maker"],
    "deviceList": ["devices", "devList", "list", "dev_list", "d_list", "devices", "dev_arr","dId"],
    "deviceId": ["sensorId", "id", "d_id", "device_id", "sensor", "deviceID", "uid"],
    "deviceType": ["type", "dType", "device_tp", "d_t", "devType"],
    "mode": ["mode", "Mode", "mo", "md", "operationMode", "functionMode", "opMode","mod"],
    "timestamp": ["time", "ts", "utc", "utcTime", "rfc", "epoch"],
    "createdTime": ["create", "created", "created_at", "creationTime", "generatedTime"],
    "status": ["state", "deviceStatus", "currentState", "device_state", "state_dev", "devState","stas"], 
    "measurements": ["measures", "sensorData", "readings", "metrics", "observations", "meas"],
    "paramName": ["parameter", "param_name", "name", "attribute", "name_para", "param", "parameter_name", "paramName", "param_name"],
    "value": ["reading", "val", "data", "amount", "number", "readValue"],
    "multiplier": ["mult", "factor", "scale", "multiplication_factor", "conversion"],
    "unit": ["units", "paramUnit", "parameter_unit", "unit_name", "unitType", "unit_para", "unitType", "uniType"]
}

def load_json(file_path):
    """Load JSON data from a file and track line numbers."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return json.loads(content), content.split("\n")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Syntax Error: {e.msg} at line {e.lineno}, column {e.colno}.")
        sys.exit(1)

def find_line_column(json_lines, field_name):
    """Find line and column number of a given field in JSON file."""
    for line_number, line in enumerate(json_lines, start=1):
        column_number = line.find(f'"{field_name}"')
        if column_number != -1:
            return line_number, column_number + 1
    return None, None

def check_misspellings(field_name, valid_field_names, context, json_lines):
    """Check for misspellings in field names and return error with line and column info."""
    line, col = find_line_column(json_lines, field_name)
    if field_name not in valid_field_names:
        for valid_field, variations in FIELD_VARIATIONS.items():
            if field_name.lower() in [v.lower() for v in variations]:
                return f"Error in {context}: Field '{field_name}' is misspelled at Line {line}, Column {col}. Suggested fix: Change '{field_name}' to '{valid_field}'."
        return f"Error in {context}: Field '{field_name}' is invalid at Line {line}, Column {col}. Suggested fix: Use one of {valid_field_names}."
    return None

def validate_json_structure(data, json_lines):
    """Validate the JSON structure and return errors with line/column info."""
    errors = []
    required_fields = {"mfg", "deviceList"}

    for field in data.keys():
        misspelling_error = check_misspellings(field, required_fields, "top-level", json_lines)
        if misspelling_error:
            errors.append(misspelling_error)

    missing_fields = required_fields - set(data.keys())
    if missing_fields:
        errors.append(f"Missing top-level fields: {', '.join(missing_fields)}. Suggested fix: Add these fields.")

    if "deviceList" not in data or not isinstance(data["deviceList"], list):
        errors.append("Error: 'deviceList' must be a list. Suggested fix: Ensure 'deviceList' is an array.")
    else:
        for i, device in enumerate(data["deviceList"]):
            errors.extend(validate_device(device, i, json_lines))

    return errors

def validate_device(device, index, json_lines):
    """Validate each device and return errors with line/column info."""
    errors = []
    required_fields = {"deviceId", "deviceType", "mode", "timestamp", "createdTime", "measurements"}

    for field in device.keys():
        valid_fields = required_fields | {"status"} 
        misspelling_error = check_misspellings(field, valid_fields, f"deviceList[{index}]", json_lines)
        if misspelling_error:
            errors.append(misspelling_error)

    missing_fields = required_fields - set(device.keys())
    if missing_fields:
        errors.append(f"Error in deviceList[{index}]: Missing fields: {', '.join(missing_fields)}.")

    for field in ["timestamp", "createdTime"]:
        if field not in device or not isinstance(device[field], int) or len(str(device[field])) != 13:
            errors.append(f"Error in deviceList[{index}]: '{field}' must be a 13-digit epoch time (milliseconds).")

    if "measurements" not in device or not isinstance(device["measurements"], list):
        errors.append(f"Error in deviceList[{index}]: 'measurements' must be a list.")
    else:
        for j, measurement in enumerate(device["measurements"]):
            errors.extend(validate_measurement(measurement, index, j, json_lines))

    return errors

def validate_measurement(measurement, device_index, measurement_index, json_lines):
    """Validate each measurement and return errors with line/column info."""
    errors = []
    required_fields = {"paramName", "value", "multiplier", "unit"}

    for field in measurement.keys():
        valid_fields = required_fields
        context = f"deviceList[{device_index}]['measurements'][{measurement_index}]"
        misspelling_error = check_misspellings(field, valid_fields, context, json_lines)
        if misspelling_error:
            errors.append(misspelling_error)

    missing_fields = required_fields - set(measurement.keys())
    if missing_fields:
        errors.append(f"Error in deviceList[{device_index}]['measurements'][{measurement_index}]: "
                    f"Missing fields: {', '.join(missing_fields)}.")

    valid_param_names = {"Temperature", "Humidity", "Pressure", "Gas Resistance", "AQI"}
    if measurement["paramName"] not in valid_param_names:
        errors.append(f"Error in deviceList[{device_index}]['measurements'][{measurement_index}]: "
                    f"'paramName' must be one of {valid_param_names}.")

    if not isinstance(measurement["value"], (int, float)):
        errors.append(f"Error in deviceList[{device_index}]['measurements'][{measurement_index}]: "
                    f"'value' must be an integer or float.")

    return errors

def main():
    if len(sys.argv) != 2:
        print("Usage: python Json_validator.py <filename>")
        sys.exit(1)

    file_path = sys.argv[1]
    data, json_lines = load_json(file_path)
    errors = validate_json_structure(data, json_lines)

    if errors:
        print("Validation failed. Resolve the errors first.")
        for error in errors:
            print(error)
    else:
        print("Valid format. Ready to deliver to the system.")

if __name__ == "__main__":
    main()
