import json
from openai import OpenAI
import os
import shutil

client = OpenAI()

openai_api_key = os.environ['OPENAI_API_KEY']


def process_agents(payload, current_user):
    agents_data = payload["agents_data"]
    instructions = payload["instructions"]

    updated_agents = []

    # Create a new pics folder for the updated agents
    agents_dir = os.path.join(current_user.folder_path, 'agents')
    copies_dir = os.path.join(agents_dir, 'copies')
    new_pics_dir = os.path.join(copies_dir, f"pics_{len(os.listdir(copies_dir)) + 1}")
    os.makedirs(new_pics_dir, exist_ok=True)

    for agent in agents_data:
        # Create a copy of the agent data
        updated_agent_data = agent.copy()

        # Remove the specified fields from the agent data
        excluded_fields = ['id', 'email', 'unique_id', 'timestamp','photo_path']
        for field in excluded_fields:
            if field in updated_agent_data:
                del updated_agent_data[field]

        # Prepare the API payload for each agent
        agent_payload = {
            "model": "gpt-4-turbo-preview",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": f"You are a helpful assistant designed to update agent data in JSON format based on the following instructions:\n{json.load(open('abe/abe-instructions.json'))['modify_agents_json_instructions']}"},
                {"role": "user", "content": f"Here is the agent data in JSON format:\n{json.dumps(updated_agent_data)}"},
                {"role": "user", "content": f"Please update the agent data based on the following instructions:\n{' '.join(instructions.values())}"},
                {"role": "user", "content": "Return the updated agent data as a JSON object."}
            ],
        }

        # Call the OpenAI API
        response = client.chat.completions.create(**agent_payload)

        # Check if the response is valid JSON
        if response.choices[0].finish_reason == "stop":
            updated_agent_data = json.loads(response.choices[0].message.content)
        else:
            raise ValueError(f"Incomplete or invalid JSON response: {response.choices[0].message.content}")

        # Add back the excluded fields to the updated agent data
        for field in excluded_fields:
            if field in agent:
                updated_agent_data[field] = agent[field]

        # Create the modified_id field
        if 'id' in updated_agent_data:
            updated_agent_data['modified_id'] = updated_agent_data['id']

        # Update the photo_path and copy the pic
        old_photo_path = updated_agent_data['photo_path']

        if old_photo_path.startswith('agents/copies/'):
            photo_filename = os.path.basename(old_photo_path)
        else:
            photo_filename = os.path.basename(old_photo_path)
            original_photo_path = os.path.join(agents_dir, 'pics', photo_filename)
            shutil.copy(original_photo_path, os.path.join(new_pics_dir, photo_filename))

        new_photo_path_relative = os.path.join('agents', 'copies', os.path.basename(new_pics_dir), photo_filename)
        updated_agent_data['photo_path'] = new_photo_path_relative

        updated_agents.append(updated_agent_data)

    return updated_agents



def conduct_survey(payload, current_user):
  agents_data = payload["agents_data"]
  questions = payload["questions"]
  llm_instructions = payload.get("llm_instructions", "")
  request_type = payload["request_type"]
  
  survey_responses = []
  
  for agent in agents_data:
      agent_response = {}
      agent_response["id"] = agent["id"]
      agent_response["email"] = agent["email"]
      agent_response["questions"] = questions
  
      if request_type == "iterative":
          responses = {}
          for question_id, question_data in questions.items():
              question_text = question_data["text"]
              agent_payload = {
                  "model": "gpt-3.5-turbo-0125",
                  "response_format": {"type": "json_object"},
                  "messages": [
                      {"role": "system", "content": json.load(open("abe-instructions.json"))["question_instructions"]},
                      {"role": "user", "content": f"Question: {question_text}\n{llm_instructions}"},
                  ],
              }
              response = openai.ChatCompletion.create(**agent_payload)
              responses[question_id] = response.choices[0].message.content.strip()
      else:
          questions_text = "\n".join([f"Question {question_id}: {question_data['text']}" for question_id, question_data in questions.items()])
          agent_payload = {
              "model": "gpt-3.5-turbo-0125",
              "messages": [
                  {"role": "system", "content": json.load(open("abe-instructions.json"))["question_instructions"]},
                  {"role": "user", "content": f"Please answer the following questions:\n{questions_text}\n{llm_instructions}\nProvide your responses in JSON format with the question ID as the key and your answer as the value."},
              ],
          }
          response = openai.ChatCompletion.create(**agent_payload)
          responses = json.loads(response.choices[0].message.content.strip())
  
      agent_response["responses"] = responses
      survey_responses.append(agent_response)
  
  return survey_responses