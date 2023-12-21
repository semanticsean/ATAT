import argparse
import json
import os
import shutil
import openai
from jsonschema import validate, ValidationError, SchemaError


def read_description(description_or_path):
  if os.path.isfile(description_or_path):
    with open(description_or_path, 'r') as file:
      return file.read().strip()
  return description_or_path

openai.api_key = os.getenv("OPENAI_API_KEY")

# JSON Schema for the agent entries
schema = {
    "type": "object",
    "properties": {
        "id": {
            "type": "string"
        },
        "email": {
            "type": "string"
        },
        "persona": {
            "type": "string"
        }
    },
    "required": ["id", "email", "persona"],
}


def backup_file(file_path):
  shutil.copy(file_path, f"{file_path}.bak")


def restore_backup(file_path):
  shutil.move(f"{file_path}.bak", file_path)


def generate_persona(base_persona, modification_instructions):
  response = openai.ChatCompletion.create(
      model="gpt-4",
      messages=[{
          "role":
          "system",
          "content":
          "You are a capable AI that can generate persona descriptions based on existing ones."
      }, {
          "role": "user",
          "content": f"{base_persona}"
      }, {
          "role": "user",
          "content": f"{modification_instructions}"
      }])
  return response['choices'][0]['message']['content'].strip()


def validate_json(json_data):
  try:
    for entry in json_data:
      validate(instance=entry, schema=schema)
    return True
  except (ValidationError, SchemaError) as e:
    print(f"Validation Error: {e}")
    return False


def add_new_agent(base_agent_id, modification_instructions, new_name):
  # Load agents
  with open("agents/agents.json", "r") as file:
    agents = json.load(file)

  if validate_json(agents):
    backup_file("agents/agents.json")

    # Find base agent
    base_agent = next((a for a in agents if a['id'] == base_agent_id), None)
    if not base_agent:
      print(f"No agent found with id: {base_agent_id}")
      return

    # Generate new persona based on modification instructions
    new_persona = generate_persona(base_agent['persona'],
                                   modification_instructions)

    # Create new agent
    new_agent = {
        "id": new_name,
        "email": base_agent['email'],
        "persona": new_persona
    }

    # Append new agent
    agents.append(new_agent)

    # Check if it is still valid json
    if validate_json(agents):
      with open("agents/agents.json", "w") as file:
        json.dump(agents, file, indent=4)
    else:
      print("New agent not valid. Restoring backup...")
      restore_backup("agents/agents.json")


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      description=
      'Create a new agent based on an existing agent and description.')
  parser.add_argument('existingAgentReference',
                      type=str,
                      help='ID of the existing agent')
  parser.add_argument('newAgentName',
                      type=str,
                      help='New name (ID) for the agent')
  parser.add_argument(
      'description',
      type=str,
      help='Description for the new persona or file path to a txt or md file')
  args = parser.parse_args()

  description = read_description(args.description)
  add_new_agent(args.existingAgentReference, description, args.newAgentName)
