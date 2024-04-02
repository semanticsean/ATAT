# abe_gpt.py
import json
import base64
import requests
import logging
import time
import uuid
import datetime
import os
from models import db, User, Survey, Timeframe
from openai import OpenAI, APIError
from flask import url_for
from PIL import Image
from io import BytesIO

client = OpenAI()
openai_api_key = os.environ['OPENAI_API_KEY']


def process_agents(payload, current_user):
    logging.info("Entering process_agents function")
    agents_data = payload["agents_data"]
    instructions = payload["instructions"]

    updated_agents = []

    new_timeframe = Timeframe(name=payload["timeframe_name"],
                              user_id=current_user.id,
                              agents_data=[])
    db.session.add(new_timeframe)
    db.session.commit()

    for agent in agents_data:
        logging.info(f"Processing agent: {agent['id']}")

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
        logging.info(
            f"Current credit balance before API call: {current_user.credits}")

        while retry_count < max_retries:
            try:
                if current_user.credits is None or current_user.credits < 5:
                    raise Exception("Insufficient credits, please add more")

                response = client.chat.completions.create(**agent_payload)

                # Deduct credits based on the API call
                if agent_payload["model"].startswith("gpt-4"):
                    credits_used = 5  # Deduct 5 credits for GPT-4 models
                else:
                    raise ValueError(
                        f"Unexpected model: {agent_payload['model']}")

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
            updated_agent_data = json.loads(
                response.choices[0].message.content)
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

        logging.info(
            f"Current credit balance after API call: {current_user.credits}")

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
                    if current_user.credits is None or current_user.credits < 10:
                        raise Exception(
                            "Insufficient credits, please add more")
                    vision_response = client.chat.completions.create(
                        **vision_payload)

                    # Deduct credits based on the API call
                    credits_used = 10  # Deduct 10 credits for image calls

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

            vision_description = vision_response.choices[0].message.content.strip(
            )
            logging.info(f"Vision API response: {vision_description}")

            # Store vision description in agent JSON
            updated_agent_data[
                "vision_description_image_prompt"] = vision_description
        else:
            logging.warning(
                f"Image data not found for {photo_filename}")

        # DALL-E - Generate new profile picture
        image_prompt = updated_agent_data.get('image_prompt', '')
        max_prompt_length = 5000  # Adjust this value based on the DALL-E API's limit
        dalle_prompt = f"{' '.join(instructions.values())} {json.load(open('abe/abe-instructions.json'))['dalle_modify_agents_instructions']} {image_prompt} {vision_description}"[:max_prompt_length]
        updated_agent_data[
            f"{agent['id']}_image_instructions"] = dalle_prompt
        logging.info(f"DALL-E prompt: {dalle_prompt}")

        # DALL-E - Generate new profile picture
        max_retries = 1
        retry_delay = 30
        retry_count = 0
        while retry_count < max_retries:
            try:
                if current_user.credits is None or current_user.credits < 10:
                    raise Exception("Insufficient credits, please add more")

                logging.info(
                    f"Sending DALL-E request with prompt: {dalle_prompt}")
                dalle_response = client.images.generate(
                    model="dall-e-3",
                    prompt=dalle_prompt[:5000],
                    quality="standard",
                    size="1024x1024",
                    n=1,
                )
                current_user.credits -= 10  # Deduct 10 credits for DALL-E models
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
            except Exception as e:
                logging.error(
                    f"Error occurred while generating DALL-E image: {e}")
                raise e

        if dalle_response is None:
            logging.error(
                "Failed to generate DALL-E image after multiple retries")
            raise Exception("Failed to generate DALL-E image")

        image_url = dalle_response.data[0].url
        logging.info(f"Generated image URL: {image_url}")

        new_photo_filename = f"{agent['id']}_iteration_{len(current_user.images_data)+1}.png"
        logging.info(f"New photo filename: {new_photo_filename}")

        try:
            img_data = requests.get(image_url).content
            encoded_string = base64.b64encode(
                img_data).decode('utf-8')
            current_user.images_data[
                f"timeframe_{new_timeframe.id}_{new_photo_filename}"] = encoded_string

            # Generate thumbnail image
            thumbnail_size = (200, 200)
            img = Image.open(BytesIO(img_data))
            img.thumbnail(thumbnail_size)
            thumbnail_buffer = BytesIO()
            img.save(thumbnail_buffer, format='PNG')
            thumbnail_data = thumbnail_buffer.getvalue()
            thumbnail_encoded_string = base64.b64encode(
                thumbnail_data).decode('utf-8')
            current_user.thumbnail_images_data[
                f"timeframe_{new_timeframe.id}_{new_photo_filename}"] = thumbnail_encoded_string

            db.session.commit()
        except Exception as e:
            logging.error(f"Error occurred while saving image data: {e}")
            raise e

        updated_agent_data['photo_path'] = f"timeframe_{new_timeframe.id}_{new_photo_filename}"
        logging.info(f"Updated photo path: {updated_agent_data['photo_path']}")

        # Update the agent data directly in new_timeframe.agents_data
        agent_index = agents_data.index(agent)
        logging.info(f"Updating agent data for: {agent['id']}")
        new_timeframe.agents_data[agent_index] = updated_agent_data
        logging.info(f"Agent data updated for: {agent['id']}")

    db.session.commit()
    logging.info("Database session committed after processing agents")

    return new_timeframe



def conduct_meeting(payload, current_user):
  logging.info("Entering conduct_meeting function")
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

  logging.info(f"Agents data: {agents_data[:142]}")
  logging.info(f"Questions: {questions[:142]}")
  logging.info(f"LLM instructions: {llm_instructions_combined[:142]}")
  logging.info(f"Request type: {request_type[:142]}")

  meeting_responses = []

  for agent in agents_data:
    agent_response = {}
    agent_response["id"] = agent["id"]
    agent_response["email"] = agent["email"]
    agent_response["questions"] = questions

    logging.info(f"Processing agent: {agent['id']}")

    if request_type == "iterative":
      responses = {}
      for question_id, question_text in questions.items():
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
            if current_user.credits is None or current_user.credits < 1:
              raise Exception("Insufficient credits, please add more")

            logging.info(
                f"Sending request to OpenAI API for agent: {agent['id']}, question: {question_id}"
            )
            response = client.chat.completions.create(**agent_payload)
            logging.info(
                f"Received response from OpenAI API for agent: {agent['id']}, question: {question_id}"
            )

            # Deduct credits based on the API call
            credits_used = 1  # Deduct 1 credit for gpt-3.5-turbo models

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
          f"Question {question_id}: {question_text}"
          for question_id, question_text in questions.items()
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
          if current_user.credits is None or current_user.credits < 1:
            raise Exception("Insufficient credits, please add more")

          logging.info(
              f"Sending request to OpenAI API for agent: {agent['id']}")
          response = client.chat.completions.create(**agent_payload)
          logging.info(
              f"Received response from OpenAI API for agent: {agent['id']}")

          # Deduct credits based on the API call
          credits_used = 1  # Deduct 1 credit for gpt-3.5-turbo models

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
    meeting_responses.append(agent_response)
    logging.info(f"Processed agent: {agent['id']}")

  logging.info(f"Meeting responses: {meeting_responses[:142]}")
  return meeting_responses


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
      if current_user.credits is None or current_user.credits < 5:
        raise Exception("Insufficient credits, please add more")

      response = client.chat.completions.create(**agent_payload)

      # Deduct credits based on the API call
      credits_used = 5  # Deduct 5 credits for gpt-4-turbo-preview models

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
  # DALL-E - Generate new profile picture
  image_prompt = new_agent_data.get('image_prompt', '')
  dalle_prompt = f"{image_prompt[:3000]}"

  dalle_prompt = f"{image_prompt[:3000]}"

  # DALL-E - Generate profile picture
  max_retries = 12
  retry_delay = 5
  retry_count = 0
  while retry_count < max_retries:
    try:
      if current_user.credits is None or current_user.credits < 10:
        raise Exception("Insufficient credits, please add more")

      dalle_response = client.images.generate(
          model="dall-e-3",
          prompt=dalle_prompt[:5000],
          quality="standard",
          size="1024x1024",
          n=1,
      )
      current_user.credits -= 10  # Deduct 10 credits for DALL-E models
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
  logging.info(f"Generated image URL: {image_url[:142]}")

  new_photo_filename = f"{agent_name}.png"
  logging.info(f"New photo filename: {new_photo_filename[:142]}")

  img_data = requests.get(image_url).content
  encoded_string = base64.b64encode(img_data).decode('utf-8')
  current_user.images_data[new_photo_filename] = encoded_string
  db.session.commit()

  # Generate thumbnail image
  thumbnail_size = (200, 200)
  img = Image.open(BytesIO(img_data))
  img.thumbnail(thumbnail_size)
  thumbnail_buffer = BytesIO()
  img.save(thumbnail_buffer, format='PNG')
  thumbnail_data = thumbnail_buffer.getvalue()
  thumbnail_encoded_string = base64.b64encode(thumbnail_data).decode('utf-8')
  current_user.thumbnail_images_data[
      new_photo_filename] = thumbnail_encoded_string

  db.session.commit()

  new_agent_data['photo_path'] = f"/images/{new_photo_filename}"
  logging.info(f"Updated photo path: {new_agent_data['photo_path']}")

  # Add the new agent data to the user's agents_data
  if current_user.agents_data is None:
    current_user.agents_data = []

  current_user.agents_data.append(new_agent_data)
  db.session.commit()

  return new_agent_data
