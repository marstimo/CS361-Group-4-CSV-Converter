import json
import os
import time
import csv
from typing import Any, Dict, List, Optional

# ---------------------------
# Config (matches your plan)
# ---------------------------
REQUEST_FILE = "csv_request.json"
DONE_FILE = "csv_done.json"
ERROR_FILE = "csv_error.json"

POLL_INTERVAL = 0.10  # seconds

# Default behavior
DEFAULT_FLATTEN = False


# ---------------------------
# Helpers
# ---------------------------
def safe_remove(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def write_json(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_parent_dir(file_path: str) -> None:
    parent = os.path.dirname(file_path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def is_dict(x: Any) -> bool:
    return isinstance(x, dict)


def is_list(x: Any) -> bool:
    return isinstance(x, list)


def flatten_json(obj: Any, prefix: str = "", out: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Flattens nested dictionaries.
    - Nested dict keys become parent.child
    - Arrays become JSON-string cell values
    - Non-dict values stored directly
    """
    if out is None:
        out = {}

    if is_dict(obj):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else str(k)
            flatten_json(v, new_key, out)
    elif is_list(obj):
        # Arrays become a JSON string
        out[prefix] = json.dumps(obj, ensure_ascii=False)
    else:
        out[prefix] = obj

    return out


def normalize_rows(rows: Any, flatten: bool) -> List[Dict[str, Any]]:
    """
    Input JSON should be a list of objects or a single object.
    Return list[dict].
    """
    if is_dict(rows):
        rows_list = [rows]
    elif is_list(rows):
        rows_list = rows
    else:
        raise ValueError("Input JSON must be an object or a list of objects.")

    normalized = []
    for item in rows_list:
        if not is_dict(item):
            raise ValueError("All rows must be JSON objects (dict).")
        normalized.append(flatten_json(item) if flatten else item)

    return normalized


def value_to_csv_cell(value: Any) -> str:
    """
    Convert Python value to CSV cell string.
    - None => ""
    - dict/list => JSON string
    - everything else => str(value)
    """
    if value is None:
        return ""
    if is_dict(value) or is_list(value):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def build_csv(normalized_rows: List[Dict[str, Any]], columns: List[str]) -> List[List[str]]:
    """
    Build CSV rows (including header).
    Missing keys => blank cells.
    """
    csv_rows = [columns]
    for row in normalized_rows:
        csv_row = []
        for col in columns:
            csv_row.append(value_to_csv_cell(row.get(col)))
        csv_rows.append(csv_row)
    return csv_rows


def write_csv(path: str, csv_rows: List[List[str]]) -> None:
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerows(csv_rows)


def validate_request(req: dict) -> None:
    required = ["inputJsonPath", "outputCsvPath", "columns", "flatten"]
    missing = [k for k in required if k not in req]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")

    if not isinstance(req["inputJsonPath"], str) or not req["inputJsonPath"]:
        raise ValueError("inputJsonPath must be a non-empty string.")
    if not isinstance(req["outputCsvPath"], str) or not req["outputCsvPath"]:
        raise ValueError("outputCsvPath must be a non-empty string.")
    if not isinstance(req["columns"], list):
        raise ValueError("columns must be an array of strings.")
    if len(req["columns"]) == 0:
        raise ValueError("columns cannot be empty.")
    if not all(isinstance(c, str) and c for c in req["columns"]):
        raise ValueError("columns must contain only non-empty strings.")
    if not isinstance(req["flatten"], bool):
        raise ValueError("flatten must be a boolean.")


# ---------------------------
# Main microservice loop
# ---------------------------
def convert_json_to_csv(input_path: str, output_path: str, columns: List[str], flatten: bool) -> int:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input JSON file not found: {input_path}")
    raw_json = read_json(input_path)
    normalized_rows = normalize_rows(raw_json, flatten=flatten)
    csv_rows = build_csv(normalized_rows, columns)
    write_csv(output_path, csv_rows)
    return max(0, len(csv_rows) - 1)


def process_one_request() -> None:
    """
    Reads REQUEST_FILE, performs conversion, writes DONE_FILE or ERROR_FILE,
    and deletes REQUEST_FILE after processing.
    """
    safe_remove(DONE_FILE)
    safe_remove(ERROR_FILE)

    req = read_json(REQUEST_FILE)
    validate_request(req)

    output_path = req["outputCsvPath"]
    rows_written = convert_json_to_csv(req["inputJsonPath"], output_path, req["columns"], req["flatten"])

    write_json(DONE_FILE, {"status": "ok", "outputCsvPath": output_path, "rowsWritten": rows_written})


def run_service() -> None:
    print("CSV Converter microservice running.")
    print(f"Watching for: {REQUEST_FILE}")
    while True:
        try:
            if os.path.exists(REQUEST_FILE):
                try:
                    process_one_request()
                except json.JSONDecodeError:
                    write_json(ERROR_FILE, {"status": "error", "message": "Invalid JSON in request file."})
                except Exception as e:
                    write_json(ERROR_FILE, {"status": "error", "message": str(e)})
                finally:
                    # Remove request so it doesn't re-run forever
                    safe_remove(REQUEST_FILE)

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\nService stopped.")
            break


if __name__ == "__main__":
    run_service()