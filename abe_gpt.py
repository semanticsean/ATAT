# abe_gpt.py
import json
import base64
import requests
import logging
import time
import uuid
import datetime
import os
from models import db, User, Survey
from openai import OpenAI, APIError

client = OpenAI()
openai_api_key = os.environ['OPENAI_API_KEY']


def process_agents(payload, current_user):
  agents_data = payload["agents_data"]
  instructions = payload["instructions"]

  updated_agents = []

  for agent in agents_data:
    # Create a copy of the agent data
    updated_agent_data = agent.copy()

    # Remove the specified fields from the agent data
    excluded_fields = ['id', 'email', 'unique_id', 'timestamp', 'photo_path']
    for field in excluded_fields:
      if field in updated_agent_data:
        del updated_agent_data[field]

    # Prepare the API payload for each agent
    agent_payload = {
        "model":
        "gpt-4-turbo-preview",
        "response_format": {
            "type": "json_object"
        },
        "messages": [{
            "role":
            "system",
            "content":
            f"You are a helpful assistant designed to update agent data in JSON format based on the following instructions:\n{json.load(open('abe/abe-instructions.json'))['modify_agents_json_instructions']}"
        }, {
            "role":
            "user",
            "content":
            f"Here is the agent data in JSON format:\n{json.dumps(updated_agent_data)}"
        }, {
            "role":
            "user",
            "content":
            f"Please update the agent data based on the following instructions:\n{' '.join(instructions.values())}"
        }, {
            "role":
            "user",
            "content":
            "Return the updated agent data as a JSON object."
        }],
    }

    # Call the OpenAI API with exponential backoff and retries
    max_retries = 12
    retry_delay = 5
    retry_count = 0
    print(f"Current token balance before API call: {current_user.credits}")

    while retry_count < max_retries:
      try:
        if current_user.credits is None or current_user.credits <= 0:
          raise Exception("Out of credits, please add more")

        response = client.chat.completions.create(**agent_payload)
        tokens_used = response.usage.total_tokens

        # Deduct credits based on the API call
        if agent_payload["model"].startswith("gpt-4"):
          credits_used = tokens_used * 10  # Deduct 10 credits per token for GPT-4 models
        elif agent_payload["model"].startswith("dall-e"):
          credits_used = 10  # Deduct a fixed amount of 10 credits for DALL-E models
        else:
          credits_used = tokens_used  # Deduct 1 credit per token for other models

        current_user.credits -= credits_used
        db.session.commit()
        break
      except APIError as e:
        logging.error(f"OpenAI API error: {e}")
        retry_count += 1
        if retry_count < max_retries:
          time.sleep(retry_delay)
          retry_delay *= 2
        else:
          raise e

    # Check if the response is valid JSON
    if response.choices[0].finish_reason == "stop":
      updated_agent_data = json.loads(response.choices[0].message.content)
    else:
      raise ValueError(
          f"Incomplete or invalid JSON response: {response.choices[0].message.content}"
      )

    # Add back the excluded fields to the updated agent data
    for field in excluded_fields:
      if field in agent:
        updated_agent_data[field] = agent[field]

    # Vision API - Get detailed description of profile picture
    photo_filename = updated_agent_data['photo_path'].split('/')[-1]
    image_data = current_user.images_data.get(
        photo_filename) if current_user.images_data else None

    print(f"Tokens used in the API call: {tokens_used}")
    print(f"Current token balance after API call: {current_user.credits}")

    if image_data:
      vision_payload = {
          "model":
          "gpt-4-vision-preview",
          "messages": [{
              "role":
              "user",
              "content": [{
                  "type":
                  "text",
                  "text":
                  "Provide a very detailed description of this image with explicit instructions for how to re-create it:"
              }, {
                  "type": "image_url",
                  "image_url": {
                      "url": f"data:image/jpeg;base64,{image_data}"
                  }
              }]
          }],
      }

      # Vision API - Get detailed description of profile picture
      max_retries = 12
      retry_delay = 5
      retry_count = 0
      while retry_count < max_retries:
        try:
          if current_user.credits is None or current_user.credits <= 0:
            raise Exception("Out of credits, please add more")
          vision_response = client.chat.completions.create(**vision_payload)
          tokens_used = vision_response.usage.total_tokens

          # Deduct credits based on the API call
          if vision_payload["model"].startswith("gpt-4"):
            credits_used = tokens_used * 10  # Deduct 10 credits per token for GPT-4 models
          elif vision_payload["model"].startswith("dall-e"):
            credits_used = 10  # Deduct a fixed amount of 10 credits for DALL-E models
          else:
            credits_used = tokens_used  # Deduct 1 credit per token for other models

          current_user.credits -= credits_used
          db.session.commit()
          break
        except APIError as e:
          logging.error(f"OpenAI API error: {e}")
          retry_count += 1
          if retry_count < max_retries:
            time.sleep(retry_delay)
            retry_delay *= 2
          else:
            raise e

      vision_description = vision_response.choices[0].message.content.strip()
      logging.info(f"Vision API response: {vision_description}")

      # Store vision description in agent JSON
      updated_agent_data[
          "vision_description_image_prompt"] = vision_description
    else:
      logging.warning(f"Image data not found for {photo_filename}")

    # DALL-E - Generate new profile picture
    image_prompt = updated_agent_data.get('image_prompt', '')
    dalle_prompt = f"{' '.join(instructions.values())} {json.load(open('abe/abe-instructions.json'))['dalle_modify_agents_instructions']} {image_prompt} {vision_description}"
    updated_agent_data[f"{agent['id']}_image_instructions"] = dalle_prompt
    logging.info(f"DALL-E prompt: {dalle_prompt}")

    # DALL-E - Generate new profile picture
    max_retries = 12
    retry_delay = 5
    retry_count = 0
    while retry_count < max_retries:
      try:
        if current_user.credits is None or current_user.credits <= 0:
          raise Exception("Out of credits, please add more")
        dalle_response = client.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt,
            quality="standard",
            size="1024x1024",
            n=1,
        )
        current_user.credits -= 10  # Deduct a fixed amount of 10 credits for DALL-E models
        db.session.commit()
        break
      except APIError as e:
        logging.error(f"OpenAI API error: {e}")
        retry_count += 1
        if retry_count < max_retries:
          time.sleep(retry_delay)
          retry_delay *= 2
        else:
          raise e

    image_url = dalle_response.data[0].url
    logging.info(f"Generated image URL: {image_url}")

    new_photo_filename = f"{agent['id']}_iteration_{len(current_user.images_data)+1}.png"
    logging.info(f"New photo filename: {new_photo_filename}")

    img_data = requests.get(image_url).content
    encoded_string = base64.b64encode(img_data).decode('utf-8')
    current_user.images_data[new_photo_filename] = encoded_string
    db.session.commit()

    updated_agent_data['photo_path'] = f"/images/{new_photo_filename}"
    logging.info(f"Updated photo path: {updated_agent_data['photo_path']}")

    # Add back the modified_id field
    if 'id' in updated_agent_data:
      updated_agent_data['modified_id'] = updated_agent_data['id']

    updated_agents.append(updated_agent_data)

    # Create a new timeframe and save the updated agents
    new_timeframe = Timeframe(name=payload["timeframe_name"], user_id=current_user.id, agents_data=updated_agents)
    db.session.add(new_timeframe)
    db.session.commit()

  updated_agents.appendupdated_agents.append(updated_agent_data)
  logger.info(f"Updated agents: {updated_agents}")

  return updated_agents


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
  llm_instructions_combined = f"{question_instructions} {form_llm_instructions}".strip(
  )

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
            "model":
            "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": question_instructions
                },
                {
                    "role":
                    "user",
                    "content":
                    f"ID: {agent['id']}\nPersona: {agent['persona']}\nRelationships: {agent['relationships']}\nKeywords: {', '.join(agent['keywords'])}\n\nQuestion: {question_text}\n{llm_instructions_combined}\nPlease respond in JSON format."
                },
            ],
        }
        max_retries = 12
        retry_delay = 5
        retry_count = 0
        while retry_count < max_retries:
          try:
            if current_user.credits is None or current_user.credits <= 0:
              raise Exception("Out of credits, please add more")

            response = client.chat.completions.create(**agent_payload)
            tokens_used = response.usage.total_tokens

            # Deduct credits based on the API call
            if agent_payload["model"].startswith("gpt-4"):
              credits_used = tokens_used * 10  # Deduct 10 credits per token for GPT-4 models
            elif agent_payload["model"].startswith("dall-e"):
              credits_used = 10  # Deduct a fixed amount of 10 credits for DALL-E models
            else:
              credits_used = tokens_used  # Deduct 1 credit per token for other models

            current_user.credits -= credits_used
            db.session.commit()
            break
          except APIError as e:
            logging.error(f"OpenAI API error: {e}")
            retry_count += 1
            if retry_count < max_retries:
              time.sleep(retry_delay)
              retry_delay *= 2
            else:
              raise e
        responses[question_id] = response.choices[0].message.content.strip()
    else:
      questions_text = "\n".join([
          f"Question {question_id}: {question_data['text']}"
          for question_id, question_data in questions.items()
      ])
      agent_payload = {
          "model":
          "gpt-3.5-turbo",
          "messages": [
              {
                  "role": "system",
                  "content": question_instructions
              },
              {
                  "role":
                  "user",
                  "content":
                  f"ID: {agent['id']}\nPersona: {agent['persona']}\nRelationships: {agent['relationships']}\nKeywords: {', '.join(agent['keywords'])}\n\nPlease answer the following questions:\n{questions_text}\n{llm_instructions_combined}\nProvide your responses in JSON format."
              },
          ],
      }
      max_retries = 12
      retry_delay = 5
      retry_count = 0
      while retry_count < max_retries:
        try:
          if current_user.credits is None or current_user.credits <= 0:
            raise Exception("Out of credits, please add more")

          response = client.chat.completions.create(**agent_payload)
          tokens_used = response.usage.total_tokens

          # Deduct credits based on the API call
          if agent_payload["model"].startswith("gpt-4"):
            credits_used = tokens_used * 10  # Deduct 10 credits per token for GPT-4 models
          elif agent_payload["model"].startswith("dall-e"):
            credits_used = 10  # Deduct a fixed amount of 10 credits for DALL-E models
          else:
            credits_used = tokens_used  # Deduct 1 credit per token for other models

          current_user.credits -= credits_used
          db.session.commit()
          break
        except APIError as e:
          logging.error(f"OpenAI API error: {e}")
          retry_count += 1
          if retry_count < max_retries:
            time.sleep(retry_delay)
            retry_delay *= 2
          else:
            raise e

      responses = json.loads(response.choices[0].message.content.strip())

    agent_response["responses"] = responses
    survey_responses.append(agent_response)

  return survey_responses


def generate_new_agent(agent_name, jobtitle, agent_description, current_user):
  # Generate unique_id and timestamp
  unique_id = str(uuid.uuid4())
  timestamp = datetime.datetime.now().isoformat()
  email = f"{agent_name.lower()}@{os.environ['DOMAIN_NAME']}"

  # Prepare the API payload for the new agent
  agent_payload = {
      "model":
      "gpt-4-turbo-preview",
      "response_format": {
          "type": "json_object"
      },
      "messages": [{
          "role":
          "system",
          "content":
          f"You are a helpful assistant designed to generate a new agent data in JSON format based on the following instructions:\n{json.load(open('abe/abe-instructions.json'))['new_agent_json_instructions']} /n /n Relationships must be a list of dictionaries, each representing a unique relationship with detailed attributes (name, job, relationship_description, summary, common_interactions)"
      }, {
          "role":
          "user",
          "content":
          f"Agent Name: {agent_name}\nJob Title: {jobtitle}\nAgent Description: {agent_description}\n\nPlease generate the new agent data in JSON format without including the id, jobtitle, email, unique_id, timestamp, or photo_path fields."
      }]
  }

  # Call the OpenAI API with exponential backoff and retries
  max_retries = 12
  retry_delay = 5
  retry_count = 0
  while retry_count < max_retries:
    try:
      if current_user.credits is None or current_user.credits <= 0:
        raise Exception("Out of credits, please add more")

      response = client.chat.completions.create(**agent_payload)
      tokens_used = response.usage.total_tokens

      # Deduct credits based on the API call
      if agent_payload["model"].startswith("gpt-4"):
        credits_used = tokens_used * 10  # Deduct 10 credits per token for GPT-4 models
      elif agent_payload["model"].startswith("dall-e"):
        credits_used = 10  # Deduct a fixed amount of 10 credits for DALL-E models
      else:
        credits_used = tokens_used  # Deduct 1 credit per token for other models

      current_user.credits -= credits_used
      db.session.commit()
      break
    except APIError as e:
      logging.error(f"OpenAI API error: {e}")
      retry_count += 1
      if retry_count < max_retries:
        time.sleep(retry_delay)
        retry_delay *= 2
      else:
        raise e

  # Check if the response is valid JSON
  if response.choices[0].finish_reason == "stop":
    new_agent_data = json.loads(response.choices[0].message.content)
  else:
    raise ValueError(
        f"Incomplete or invalid JSON response: {response.choices[0].message.content}"
    )

  new_agent_data = {
      'id': agent_name,
      'email': email,
      'unique_id': unique_id,
      'timestamp': timestamp,
      'jobtitle': jobtitle,
      'model': "gpt-3.5-turbo",
      'shortcode_superpower': "",
      'include': True,
      **new_agent_data
  }

  # DALL-E - Generate profile picture for the new agent
  image_prompt = new_agent_data.get('image_prompt', '')
  dalle_prompt = f"{image_prompt}"

  # DALL-E - Generate profile picture
  max_retries = 12
  retry_delay = 5
  retry_count = 0
  while retry_count < max_retries:
    try:
      if current_user.credits is None or current_user.credits <= 0:
        raise Exception("Out of credits, please add more")

      dalle_response = client.images.generate(
          model="dall-e-3",
          prompt=dalle_prompt,
          quality="standard",
          size="1024x1024",
          n=1,
      )
      current_user.credits -= 10  # Deduct a fixed amount of 10 credits for DALL-E models
      db.session.commit()
      break
    except APIError as e:
      logging.error(f"OpenAI API error: {e}")
      retry_count += 1
      if retry_count < max_retries:
        time.sleep(retry_delay)
        retry_delay *= 2
      else:
        raise e

  image_url = dalle_response.data[0].url
  logging.info(f"Generated image URL: {image_url}")

  new_photo_filename = f"{agent_name}.png"
  logging.info(f"New photo filename: {new_photo_filename}")

  img_data = requests.get(image_url).content
  encoded_string = base64.b64encode(img_data).decode('utf-8')
  current_user.images_data[new_photo_filename] = encoded_string
  db.session.commit()

  new_agent_data['photo_path'] = f"/images/{new_photo_filename}"
  logging.info(f"Updated photo path: {new_agent_data['photo_path']}")

  # Add the new agent data to the user's agents_data
  if current_user.agents_data is None:
    current_user.agents_data = []

  current_user.agents_data.append(new_agent_data)
  db.session.commit()

  return new_agent_data
