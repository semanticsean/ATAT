# abe_gpt.py
import json
import base64
import requests
import logging
import time
import uuid
import datetime
import os
from models import db, Timeframe, User
from openai import OpenAI, APIError
from PIL import Image
from io import BytesIO
from flask import redirect, url_for

client = OpenAI()
openai_api_key = os.environ['OPENAI_API_KEY']

def save_image_to_database(image_url, user_id=None, timeframe_id=None, photo_filename=None):
  try:
      # Download the image from the URL
      response = requests.get(image_url)
      img_data = response.content

      # Convert the image to base64
      encoded_string = base64.b64encode(img_data).decode('utf-8')

      if timeframe_id:
          # Save the base64 image to the database for the timeframe
          timeframe = Timeframe.query.get(timeframe_id)
          if timeframe:
              timeframe_images_data = json.loads(timeframe.images_data)
              timeframe_images_data[photo_filename] = encoded_string
              timeframe.images_data = json.dumps(timeframe_images_data)
              db.session.commit()
              return True
          else:
              raise ValueError(f"Timeframe with ID {timeframe_id} not found.")
      elif user_id:
          # Save the base64 image to the user's images_data
          user = User.query.get(user_id)
          if user:
              user.images_data[photo_filename] = encoded_string
              db.session.commit()
              return True
          else:
              raise ValueError(f"User with ID {user_id} not found.")
      else:
          raise ValueError("Either user_id or timeframe_id must be provided.")

  except Exception as e:
      logging.error(f"Error occurred while saving image data: {e}")
      return False
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

  new_agents_data = []
  new_images_data = {}
  new_thumbnail_images_data = {}

  new_timeframe = Timeframe(
      name=payload["timeframe_name"],
      user_id=current_user.id,
      agents_data=json.dumps(new_agents_data),
      images_data=json.dumps(new_images_data),
      thumbnail_images_data=json.dumps(new_thumbnail_images_data)
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

      # DALL-E - Generate new profile picture
      image_prompt = updated_agent_data.get('image_prompt', '')
      dalle_prompt = f"{' '.join(instructions.values())} {json.load(open('abe/abe-instructions.json'))['dalle_modify_agents_instructions']} {image_prompt}"[:max_dalle_prompt_length]
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
          image_url = dalle_response.data[0].url
          timeframe_id = new_timeframe.id
          photo_filename = f"{agent['id']}_iteration_{len(json.loads(new_timeframe.images_data))+1}.png"

          success = save_image_to_database(image_url, timeframe_id, photo_filename)
          if success:
              logging.info(f"Image {photo_filename} saved successfully to timeframe {timeframe_id}")
          else:
              logging.error(f"Failed to save image {photo_filename} to timeframe {timeframe_id}")

          updated_agent_data['photo_path'] = photo_filename
          logging.info(f"Updated photo path: {updated_agent_data['photo_path']}")

      # Add the updated agent data to the new_timeframe.agents_data list
      new_timeframe_agents_data = json.loads(new_timeframe.agents_data)
      new_timeframe_agents_data.append(updated_agent_data)
      new_timeframe.agents_data = json.dumps(new_timeframe_agents_data)
      logging.info(f"Agent data updated for: {agent['id']}")

  db.session.commit()

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
  logging.info(f"Questions: {str(questions)[:142]}")
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
  

def generate_new_agent(agent_id, jobtitle, agent_description, current_user):

  # Generate unique_id and timestamp
  unique_id = str(uuid.uuid4())
  timestamp = datetime.datetime.now().isoformat()
  email = f"{agent_id.lower()}@{os.environ['DOMAIN_NAME']}"
  logging.info(f"Generating new agent data for agent {agent_id}")

  # Prepare the API payload for the new agent
  agent_payload = {
      "model": "gpt-4-turbo-preview",
      "response_format": {
          "type": "json_object"
      },
      "messages": [{
          "role": "system",
          "content": f"You are a helpful assistant designed to generate a new agent data in JSON format based on the following instructions:\n{json.load(open('abe/abe-instructions.json'))['new_agent_json_instructions']} /n /n Relationships must be a list of dictionaries, each representing a unique relationship with detailed attributes (name, job, relationship_description, summary, common_interactions)"
      }, {
          "role": "user",
          "content": f"Agent Name: {agent_id}\nJob Title: {jobtitle}\nAgent Description: {agent_description}\n\nPlease generate the new agent data in JSON format without including the id, jobtitle, email, unique_id, timestamp, or photo_path fields."
      }],
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
      raise ValueError(f"Incomplete or invalid JSON response: {response.choices[0].message.content}")

  new_agent_data = {
      'id': agent_id,
      'email': email,
      'unique_id': unique_id,
      'timestamp': timestamp,
      'jobtitle': jobtitle,
      'model': "gpt-3.5-turbo",
      'shortcode_superpower': "",
      'include': True,
      **new_agent_data
  }
  logging.info(f"New agent data generated: {new_agent_data}")
  # DALL-E - Generate new profile picture
  image_prompt = new_agent_data.get('image_prompt', '')
  max_dalle_prompt_length = 1000  # Define the variable with an appropriate value
  dalle_prompt = f"{image_prompt[:max_dalle_prompt_length]}"

  # Call the DALL-E API to generate the profile picture
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
              logging.warning(f"Failed to generate DALL-E image for agent {agent_id} due to prompt length.")
              new_agent_data['photo_path'] = None
              break

  if dalle_response is None:
        logging.warning(f"Failed to generate DALL-E image for agent {agent_id} after multiple retries.")
        new_agent_data['photo_path'] = None
  else:
      image_url = dalle_response.data[0].url
      photo_filename = f"{agent_id}.png"

      success = save_image_to_database(image_url, user_id=current_user.id, photo_filename=photo_filename)
      if success:
          logging.info(f"Image {photo_filename} saved successfully for user {current_user.id}")
      else:
          logging.error(f"Failed to save image {photo_filename} for user {current_user.id}")

      new_agent_data['photo_path'] = photo_filename
      logging.info(f"Updated photo path: {new_agent_data['photo_path']}")

  logging.info(f"Current user: {current_user}")
  logging.info(f"Current user ID: {current_user.id}")
  logging.info(f"Current user agents_data before appending: {current_user.agents_data}")

  max_retries = 3
  retry_delay = 1
  retry_count = 0

  while retry_count < max_retries:
      try:
          if current_user.agents_data is None:
              current_user.agents_data = []

          logging.info(f"Saving new agent data to the database for user {current_user.id}")
          current_user.agents_data.append(new_agent_data)
          logging.info(f"Current user agents_data after appending: {current_user.agents_data}")

          db.session.commit()
          logging.info(f"New agent data saved to the database for user {current_user.id}")
          break
      except OperationalError as e:
          logging.error(f"Database error occurred: {str(e)}")
          db.session.rollback()
          retry_count += 1
          if retry_count < max_retries:
              time.sleep(retry_delay)
              retry_delay *= 2  # Exponential backoff
          else:
              raise e

  return new_agent_data