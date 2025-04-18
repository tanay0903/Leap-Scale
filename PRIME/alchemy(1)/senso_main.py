import json
from collections import OrderedDict
from senso_data_norm import senso_normalise_json, senso_find_best_match
import requests

raw_data = {
  "man": "Interns Leap&Scale",
  "dList": [
    {
      "dId": "IN03091228",
      "dType": "IN_005",
      "mod": "Auto",
      "ts": "2025-03-22 05:21:14",
      "createdT": "2025-03-22 05:21:14",
      "state": "Okay",
      "readings": [
        {
          "name": "temperature",
          "num": "30",
          "factor": 1,
          "uni": "celsius"
        },
        {
          "attri": "temperature",
          "num": "25",
          "fact": 1,
          "uni": "celsius"
        }
      ]
    }
  ]
}

correct_order = {
    "mfg": 0, "deviceList": 1,
    "deviceId":0, "deviceType":1, "mode":2, "timestamp":3, "createdTime": 4, "status": 5, "measurements":6,
    "paramName": 0, "value": 1, "multiplier": 2, "unit": 3
}

url = "https://sparrow.sensoyo.io/DataCollection/test"
# url = "https://ronny.iotclay.net/DataCollection/test"

headers = {"Content-Type": "application/json"}

normalized_data = senso_normalise_json(raw_data)

if normalized_data is None:
    raise ValueError("Data normalization failed. Please check the input data.")

def reorder_json(data, order):
    if isinstance(data, dict):
        return {k: reorder_json(v, order) for k, v in sorted(
            data.items(),
            key=lambda x: order.get(x[0], 100)
        )}
    elif isinstance(data, list):
        return [reorder_json(item, order) for item in data]
    else:
        return data

normalized_data = reorder_json(normalized_data, correct_order)

raw_data_json = json.dumps(raw_data, indent=2)
normalized_data_json = json.dumps(normalized_data, indent=2)

print("Raw data:", raw_data_json)
print("Normalized data:", normalized_data_json)

response = requests.post(url, data=normalized_data_json, headers=headers)
print("Response Status Code: ", response.status_code)
print("Response Text: ", response.text)

# print(type(normalized_data))
