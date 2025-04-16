import json
from senso_data_norm import senso_normalise_json, senso_find_best_match

raw_data = {
  "manu": "TAS Industries PVT LTD",
  "d_list": [
    {
      "id": "",
      "dType": "T10",
      "md": "",
      # "ts": "27-02-2024 10:30",
      "time": "Tue, 27 Feb 2024 10:30:00",
      "create_t": '',
      "state_dev": "",
      "metric": [
        {
          "name_para": "temperature",
          "readValue": "30",
          "CONVERTER": 1,
          "unit_para": ""
        },
        {
          "name_para": "",
          "readValue": "25",
          "converter": 1,
          "unit_para": " "
        }
      ]
    }
  ]
}

normalized_data = senso_normalise_json(raw_data)

raw_data = json.dumps(raw_data, indent=2)
print("Raw data: ", raw_data)

if normalized_data is None:
    print("senso_normalised_json returned None!")
else:
    normalized_data = json.dumps(normalized_data, indent=2)
    print("Normalized data: ", normalized_data)
