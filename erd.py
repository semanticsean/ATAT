import os
import json
from sqlalchemy import inspect
from models import db
from abe import app

# Ensure the output directory exists
output_dir = 'logs'
if not os.path.exists(output_dir):
  os.makedirs(output_dir)
  print(f"Created directory: {output_dir}")
else:
  print(f"Directory already exists: {output_dir}")

erd_results = {}

try:
  with app.app_context():
    print("App context started.")

    # Extract schema details
    inspector = inspect(db.engine)
    tables = {}
    for table_name in inspector.get_table_names():
      columns = []
      for column in inspector.get_columns(table_name):
        columns.append({
            'name': column['name'],
            'type': str(column['type']),
            'nullable': column['nullable'],
            'default': str(column['default'])
        })
      tables[table_name] = columns

    erd_results = {
        "status": "success",
        "message": "Database schema generated successfully.",
        "schema": tables
    }
    print('Database schema generated successfully.')

except Exception as e:
  print(f'An error occurred while generating the database schema: {str(e)}')
  erd_results = {
      "status":
      "error",
      "message":
      f'An error occurred while generating the database schema: {str(e)}'
  }

# Write ERD results to JSON file
output_file_path = os.path.join(output_dir, 'erd.json')
with open(output_file_path, 'w') as json_file:
  json.dump(erd_results, json_file, indent=4)

print(f"ERD JSON file path: {output_file_path}")

# Check if the ERD JSON file was created
if os.path.isfile(output_file_path):
  print(f"ERD JSON file created successfully: {output_file_path}")
else:
  print(f"Failed to create ERD JSON file: {output_file_path}")
