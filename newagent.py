import argparse
import json
import os
import shutil
import openai
from jsonschema import validate, ValidationError, SchemaError


def read_description(file_path):
  with open(file_path, 'r') as file:
    return file.read().strip()


def read_generic_agent():
  with open("newagent-generic.json", "r") as file:
    return json.load(file)['generic']['persona']


openai.api_key = os.getenv("OPENAI_API_KEY_2")

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
          "You are an advanced AI model designed to generate detailed persona descriptions based on prior information and additional instructions. If you are told about a generic agent as inspiration, you provide all the same details, but in high resolution for the agent you are creating. "
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
  with open("agents/agents.json", "r") as file:
    agents = json.load(file)

  if validate_json(agents):
    backup_file("agents/agents.json")
    base_agent = next((a for a in agents if a['id'] == base_agent_id), None)
    if not base_agent:
      print(f"No agent found with id: {base_agent_id}")
      return

    new_persona = generate_persona(base_agent['persona'],
                                   modification_instructions)
    new_agent = {
        "id": new_name,
        "email": base_agent['email'],
        "persona": new_persona
    }
    agents.append(new_agent)

    if validate_json(agents):
      with open("agents/agents.json", "w") as file:
        json.dump(agents, file, indent=4)
    else:
      print("New agent not valid. Restoring backup...")
      restore_backup("agents/agents.json")


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      description=
      'Create a new agent based on an existing agent or a generic profile and a local text file description.'
  )
  parser.add_argument('newAgentName',
                      type=str,
                      help='New name (ID) for the agent')
  parser.add_argument(
      'descriptionFilePath',
      type=str,
      help=
      'Path to a .txt or .md file containing the description for the new persona'
  )
  parser.add_argument(
      '--parent', type=str, help='ID of the existing agent',
      default=None)  # Added this line for the --parent argument
  args = parser.parse_args()

  description = read_description(args.descriptionFilePath)

  if args.parent:  # If --parent is provided
    add_new_agent(args.parent, description, args.newAgentName)
  else:  # If --parent is not provided
    generic_persona = read_generic_agent()
    new_agent_persona = generate_persona(generic_persona, description)

    # Assuming a default email for the generic agent, replace 'default@email.com' with an appropriate email
    new_agent = {
        "id": args.newAgentName,
        "email": "agent@semantic-life.com",
        "persona": new_agent_persona
    }

    with open("agents/agents.json", "r") as file:
      agents = json.load(file)

    if validate_json(agents):
      backup_file("agents/agents.json")
      agents.append(new_agent)

      if validate_json(agents):
        with open("agents/agents.json", "w") as file:
          json.dump(agents, file, indent=4)
      else:
        print("New agent not valid. Restoring backup...")
        restore_backup("agents/agents.json")
