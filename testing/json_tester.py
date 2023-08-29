import os
import json


def get_type(value):
  """Get the type of the value."""

  if isinstance(value, dict):

    return "object"

  elif isinstance(value, list):

    return "array"

  elif isinstance(value, str):

    return "string"

  elif isinstance(value, int):

    return "integer"

  elif isinstance(value, float):

    return "float"

  elif isinstance(value, bool):

    return "boolean"

  else:

    return "null"


def extract_schema(data, is_root=True):
  """Recursively extract schema from a data structure."""

  schema = {}

  # If data is a dictionary

  if isinstance(data, dict):

    schema["type"] = "object"

    schema["properties"] = {}

    # Take the first item in the dictionary to determine the schema if it's the root

    items_to_check = list(data.values())[0] if is_root else data

    for key, value in items_to_check.items():

      schema["properties"][key] = extract_schema(value, is_root=False)

  # If data is a list

  elif isinstance(data, list):

    schema["type"] = "array"

    if data:  # Check that the list is not empty

      schema["items"] = extract_schema(data[0], is_root=False)

  # If data is a basic type (string, integer, etc.)

  else:

    schema["type"] = get_type(data)

  return schema


def main():

  # List of JSON files to analyze. Update this list with the paths to your JSON files.

  json_files = ['agents/agents.json', 'processed_threads.json']

  report = {}

  for json_file in json_files:

    try:

      with open(json_file, 'r') as f:

        data = json.load(f)

      report[json_file] = extract_schema(data)

    except Exception as e:

      report[json_file] = f"An error occurred: {e}"

  # Save the report to a JSON file

  with open('json_schemas_report5.json', 'w') as f:

    json.dump(report, f, indent=4)


if __name__ == "__main__":
  main()
