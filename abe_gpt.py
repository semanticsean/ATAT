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


# abe_gpt.py

def process_agents(payload, current_user):
    """
    Process agents based on the provided payload and update their data using OpenAI APIs.

    Args:
        payload (dict): The payload containing agent data and instructions.
        current_user (User): The current user object.

    Returns:
        Timeframe: The new timeframe object with updated agent data.

    Raises:
        Exception: If there are insufficient credits for API calls.
        APIError: If there is an error with the OpenAI API.
        ValueError: If the API response is incomplete or invalid.

    """
    logging.info("Entering process_agents function")
    agents_data = payload["agents_data"]
    instructions = payload["instructions"]

    # Set prompt length constraints
    max_chatgpt_prompt_length = 4096
    max_dalle_prompt_length = 1000

    new_timeframe = Timeframe(
        name=payload["timeframe_name"],
        user_id=current_user.id,
        agents_data='[]',
        images_data='{}',
        thumbnail_images_data='{}'
    )
    db.session.add(new_timeframe)
    db.session.commit()

    for agent in agents_data:
        logging.info(f"Processing agent: {agent['id']}")

        # Create a copy of the agent data
        updated_agent_data = agent.copy()

        # Prepare the API payload for each agent
        agent_payload = {
            "model": "gpt-4-turbo-preview",
            "response_format": {
                "type": "json_object"
            },
            "messages": [{
                "role": "system",
                "content": f"You are a helpful assistant designed to update agent data in JSON format based on the following instructions:\n{json.load(open('abe/abe-instructions.json'))['modify_agents_json_instructions']}"
            }, {
                "role": "user",
                "content": f"Here is the agent data in JSON format:\n{json.dumps(updated_agent_data)}"
            }, {
                "role": "user",
                "content": f"Please update the agent data based on the following instructions:\n{' '.join(instructions.values())[:max_chatgpt_prompt_length]}"
            }, {
                "role": "user",
                "content": "Return the updated agent data as a JSON object."
            }],
        }

        # Call the OpenAI API with exponential backoff and retries
        max_retries = 12
        retry_delay = 5
        retry_count = 0
        logging.info(f"Current credit balance before API call: {current_user.credits}")

        while retry_count < max_retries:
            try:
                if current_user.credits is None or current_user.credits < 5:
                    raise Exception("Insufficient credits, please add more")

                response = client.chat.completions.create(**agent_payload)

                # Deduct credits based on the API call
                if agent_payload["model"].startswith("gpt-4"):
                    credits_used = 5  # Deduct 5 credits for GPT-4 models
                else:
                    raise ValueError(f"Unexpected model: {agent_payload['model']}")

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
            raise ValueError(f"Incomplete or invalid JSON response: {response.choices[0].message.content}")

        # Vision API - Get detailed description of profile picture
        photo_filename = updated_agent_data['photo_path'].split('/')[-1]
        image_data = current_user.images_data.get(photo_filename) if current_user.images_data else None

        logging.info(f"Current credit balance after API call: {current_user.credits}")

        vision_description = ""
        if image_data:
            vision_payload = {
                "model": "gpt-4-vision-preview",
                "messages": [{
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": "Provide a very detailed description of this image with explicit instructions for how to re-create it:"
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
                        raise Exception("Insufficient credits, please add more")
                    vision_response = client.chat.completions.create(**vision_payload)

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

            vision_description = vision_response.choices[0].message.content.strip()
            logging.info(f"Vision API response: {vision_description[:142]}")

            # Store vision description in agent JSON
            updated_agent_data["vision_description_image_prompt"] = vision_description
        else:
            logging.warning(f"Image data not found for {photo_filename}")

        # DALL-E - Generate new profile picture
        image_prompt = updated_agent_data.get('image_prompt', '')
        dalle_prompt = f"{' '.join(instructions.values())} {json.load(open('abe/abe-instructions.json'))['dalle_modify_agents_instructions']} {image_prompt} {vision_description}"[:max_dalle_prompt_length]
        updated_agent_data[f"{agent['id']}_image_instructions"] = dalle_prompt
        logging.info(f"DALL-E prompt: {dalle_prompt[:142]}")

        # Store the DALL-E prompt in the database
        new_timeframe_agents_data = json.loads(new_timeframe.agents_data)
        new_timeframe_agents_data.append({
            'agent_id': agent['id'],
            'dalle_prompt': dalle_prompt
        })
        new_timeframe.agents_data = json.dumps(new_timeframe_agents_data)
        db.session.commit()

        # DALL-E - Generate new profile picture
        max_retries = 1
        retry_delay = 30
        retry_count = 0
        dalle_response = None

        while retry_count < max_retries:
            try:
                dalle_response = client.images.generate(
                    model="dall-e-3",
                    prompt=dalle_prompt[:max_dalle_prompt_length],
                    quality="standard",
                    size="1024x1024",
                    n=1,
                )
                current_user.credits -= 10
                db.session.commit()
                break
            except APIError as e:
                logging.error(f"OpenAI API error: {e}")
                logging.error(f"DALL-E prompt: {dalle_prompt}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    # Handle the case when the DALL-E API returns an error due to the prompt being too long
                    logging.warning(f"Failed to generate DALL-E image for agent {agent['id']} due to prompt length.")
                    updated_agent_data['photo_path'] = agent['photo_path']  # Keep the original photo path
                    break

        if dalle_response is None:
            logging.warning(f"Failed to generate DALL-E image for agent {agent['id']} after multiple retries.")
            updated_agent_data['photo_path'] = agent['photo_path']  # Keep the original photo path
        else:
            # Store the DALL-E response data in the database
            new_timeframe_agents_data = json.loads(new_timeframe.agents_data)
            new_timeframe_agents_data.append({
                'agent_id': agent['id'],
                'dalle_response': {
                    'created': dalle_response.created,
                    'data': [{'url': data.url} for data in dalle_response.data]
                }
            })
            new_timeframe.agents_data = json.dumps(new_timeframe_agents_data)
            db.session.commit()

            image_url = dalle_response.data[0].url

            logging.info(f"Generated image URL: {image_url}")

            new_photo_filename = f"{agent['id']}_iteration_{len(json.loads(new_timeframe.images_data))+1}.png"
            logging.info(f"New photo filename: {new_photo_filename}")

            # Save the generated image and thumbnail to the database
            try:
                img_data = requests.get(image_url).content
                encoded_string = base64.b64encode(img_data).decode('utf-8')
                new_timeframe_images_data = json.loads(new_timeframe.images_data)
                new_timeframe_images_data[f"timeframe_{new_timeframe.id}_{new_photo_filename}"] = encoded_string
                new_timeframe.images_data = json.dumps(new_timeframe_images_data)

                # Generate thumbnail image
                thumbnail_size = (200, 200)
                img = Image.open(BytesIO(img_data))
                img.thumbnail(thumbnail_size)
                thumbnail_buffer = BytesIO()
                img.save(thumbnail_buffer, format='PNG')
                thumbnail_data = thumbnail_buffer.getvalue()
                thumbnail_encoded_string = base64.b64encode(thumbnail_data).decode('utf-8')
                new_timeframe_thumbnail_images_data = json.loads(new_timeframe.thumbnail_images_data)
                new_timeframe_thumbnail_images_data[f"timeframe_{new_timeframe.id}_{new_photo_filename}"] = thumbnail_encoded_string
                new_timeframe.thumbnail_images_data = json.dumps(new_timeframe_thumbnail_images_data)

                db.session.commit()
            except Exception as e:
                logging.error(f"Error occurred while saving image data: {e}")
                raise e

            updated_agent_data['photo_path'] = f"timeframe_{new_timeframe.id}_{new_photo_filename}"
            logging.info(f"Updated photo path: {updated_agent_data['photo_path']}")

        # Add the updated agent data to the new_timeframe.agents_data list
        new_timeframe_agents_data = json.loads(new_timeframe.agents_data)
        new_timeframe_agents_data.append(updated_agent_data)
        new_timeframe.agents_data = json.dumps(new_timeframe_agents_data)
        logging.info(f"Agent data updated for: {agent['id']}")

    db.session.commit()

    return new_timeframe


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
