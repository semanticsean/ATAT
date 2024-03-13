#abe_gpt.py 
import json
from openai import OpenAI
import os
import shutil
import base64
import requests
import logging
import time 

client = OpenAI()

openai_api_key = os.environ['OPENAI_API_KEY']

def process_agents(payload, current_user):
    agents_data = payload["agents_data"]
    instructions = payload["instructions"]

    updated_agents = []

    # Create a new pics folder for the updated agents
    agents_dir = os.path.join(current_user.folder_path, 'agents')
    copies_dir = os.path.join(agents_dir, 'copies')
    
    # Create the copies_dir if it doesn't exist
    os.makedirs(copies_dir, exist_ok=True)
    
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
        time.sleep(20)
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

        # Vision API - Get detailed description of profile picture
        old_photo_path = updated_agent_data['photo_path']
        if old_photo_path.startswith('agents/copies/'):
            photo_filename = os.path.basename(old_photo_path)
        else:
            photo_filename = os.path.basename(old_photo_path)

        original_photo_path = os.path.join(agents_dir, 'pics', photo_filename)
        logging.info(f"Original photo path: {original_photo_path}")

        with open(original_photo_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        vision_payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": "Provide a very detailed description of this image with explicit instructions for how to re-create it:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
                ]},
            ],
        }
        time.sleep(30)
        vision_response = client.chat.completions.create(**vision_payload)
        vision_description = vision_response.choices[0].message.content.strip()
        logging.info(f"Vision API response: {vision_description}")

        # Store vision description in agent JSON
        updated_agent_data["vision_description_image_prompt"] = vision_description

        # DALL-E - Generate new profile picture
        image_prompt = updated_agent_data.get('image_prompt', '')  
        dalle_prompt = f"{' '.join(instructions.values())} {json.load(open('abe/abe-instructions.json'))['dalle_modify_agents_instructions']} {image_prompt} {vision_description}"
        updated_agent_data[f"{agent['id']}_image_instructions"] = dalle_prompt
        logging.info(f"DALL-E prompt: {dalle_prompt}")

        time.sleep(30)
        dalle_response = client.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt,
            quality="standard",
            size="1024x1024",
            n=1,
        )

        image_url = dalle_response.data[0].url
        logging.info(f"Generated image URL: {image_url}")

        new_photo_filename = f"{agent['id']}_iteration_{len(os.listdir(new_pics_dir))+1}.png"
        new_photo_path = os.path.join(new_pics_dir, new_photo_filename)
        logging.info(f"New photo path: {new_photo_path}")

        img_data = requests.get(image_url).content
        with open(new_photo_path, 'wb') as handler:
            handler.write(img_data)

        updated_agent_data['photo_path'] = os.path.join('agents', 'copies', os.path.basename(new_pics_dir), new_photo_filename)
        logging.info(f"Updated photo path: {updated_agent_data['photo_path']}")

        # Add back the modified_id field
        if 'id' in updated_agent_data:
            updated_agent_data['modified_id'] = updated_agent_data['id']

        updated_agents.append(updated_agent_data)
        db.session.commit() 

    return updated_agents


psql -h ep-noisy-cherry-a5vaqnhe.us-east-2.aws.neon.tech -U neon -d neondb

def conduct_survey(payload, current_user):
  agents_data = payload["agents_data"]
  questions = payload["questions"]
  form_llm_instructions = payload.get("llm_instructions", "")
  request_type = payload["request_type"]

  # Load instructions from abe/abe-instructions.json
  with open("abe/abe-instructions.json", "r") as file:
      abe_instructions = json.load(file)
      question_instructions = abe_instructions.get("question_instructions", "")

  # Combine form-provided llm_instructions with question_instructions
  llm_instructions_combined = f"{question_instructions} {form_llm_instructions}".strip()

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
                  "model": "gpt-3.5-turbo",
                  "messages": [
                      {"role": "system", "content": question_instructions},
                      {"role": "user", "content": f"ID: {agent['id']}\nPersona: {agent['persona']}\nRelationships: {agent['relationships']}\nKeywords: {', '.join(agent['keywords'])}\n\nQuestion: {question_text}\n{llm_instructions_combined}\nPlease respond in JSON format."},
                  ],
              }
              time.sleep(30)
              response = client.chat.completions.create(**agent_payload)
              responses[question_id] = response.choices[0].message.content.strip()
      else:
          questions_text = "\n".join([f"Question {question_id}: {question_data['text']}" for question_id, question_data in questions.items()])
          agent_payload = {
              "model": "gpt-3.5-turbo",
              "messages": [
                  {"role": "system", "content": question_instructions},
                  {"role": "user", "content": f"ID: {agent['id']}\nPersona: {agent['persona']}\nRelationships: {agent['relationships']}\nKeywords: {', '.join(agent['keywords'])}\n\nPlease answer the following questions:\n{questions_text}\n{llm_instructions_combined}\nProvide your responses in JSON format."},
              ],
          }
          time.sleep(30)
          response = client.chat.completions.create(**agent_payload)
          responses = json.loads(response.choices[0].message.content.strip())

      agent_response["responses"] = responses
      survey_responses.append(agent_response)

  return survey_responses
