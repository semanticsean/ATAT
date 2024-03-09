import json
import os 
import openai


openai_api_key = os.environ['OPENAI_API_KEY']

def process_agents(payload):
    agents_data = payload["agents_data"]
    instructions = payload["instructions"]

    updated_agents = []

    for agent in agents_data:
        # Prepare the API payload for each agent
        agent_payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": json.load(open("abe/abe-instructions.json"))["modify_agents_json_instructions"]},
                {"role": "user", "content": json.dumps(agent)},
                {"role": "user", "content": " ".join(instructions.values())}, 
            ],
        }

        # Call the OpenAI API
        response = openai.ChatCompletion.create(**agent_payload)

        # Parse the updated agent data from the API response
        updated_agent_data = json.loads(response.choices[0].message.content)
        updated_agents.append(updated_agent_data)

    return updated_agents