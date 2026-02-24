# CSV Converter Microservice

## Overview
This microservice converts JSON data into a CSV file based on a requested column list.
It supports:
- Custom column ordering
- Missing keys -> blank cells
- Optional flattening for nested JSON
- Nested arrays -> stored as JSON-string in the CSV cell

This microservice uses **file-based JSON request/response**.

---

# Communication Contract

## How to REQUEST data

### Request file name
The consuming program must create a JSON file named:

`csv_request.json`

### Required fields
- `inputJsonPath` (string): path to a JSON file containing the input data
- `outputCsvPath` (string): path to where the CSV should be written
- `columns` (array of strings): column names (and order) for the CSV header
- `flatten` (boolean): if true, nested dict keys become `parent.child`