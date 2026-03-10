import json
import os
import time

REQUEST_FILE = "csv_request.json"
DONE_FILE = "csv_done.json"
ERROR_FILE = "csv_error.json"

def safe_remove(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

safe_remove(DONE_FILE)
safe_remove(ERROR_FILE)

req = {
    "inputJsonPath": "test_client/sample_input.json",
    "outputCsvPath": "exports/output.csv",
    "columns": ["date", "category", "price", "note", "meta.store", "meta.tags"],
    "flatten": True
}

with open(REQUEST_FILE, "w", encoding="utf-8") as f:
    json.dump(req, f, indent=2)

print("Wrote request:", REQUEST_FILE)

while not (os.path.exists(DONE_FILE) or os.path.exists(ERROR_FILE)):
    time.sleep(0.1)

if os.path.exists(DONE_FILE):
    done_response = json.load(open(DONE_FILE, "r", encoding="utf-8"))
    print("DONE:", done_response)
else:
    error_response = json.load(open(ERROR_FILE, "r", encoding="utf-8"))
    print("ERROR:", error_response)