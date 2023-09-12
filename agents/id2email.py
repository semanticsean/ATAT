import json

# Load the JSON file
with open('agents.json', 'r') as file:
    data = json.loads(file.read())

# Check if data is a dictionary, if so convert to a list
if isinstance(data, dict):
    data = [data]

# Modify the data
for agent in data:
    agent['id'] = agent['id'].lower()
    agent['email'] = f"{agent['id']}@semantic-life.com"

# Write the modified data back to the JSON file
with open('agents.json', 'w') as file:
    json.dump(data, file, indent=4)

print("JSON file updated successfully.")
