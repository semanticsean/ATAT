# abe_gpt.py
import json
import base64
import requests
import logging
import time
import uuid
import datetime
import os
import tempfile

from models import db, User, Survey, Timeframe, Meeting, Agent, Image
from openai import OpenAI, APIError
from PIL import Image
from io import BytesIO

client = OpenAI()
openai_api_key = os.environ['OPENAI_API_KEY']


def save_image_to_database(image_url, timeframe_id, photo_filename):
  try:
    response = requests.get(image_url)
    if response.status_code != 200:
      raise Exception(
          f"Failed to download image with status code {response.status_code}")
    img_data = response.content
    encoded_string = base64.b64encode(img_data).decode('utf-8')

    timeframe = Timeframe.query.get(timeframe_id)
    if not timeframe:
      raise ValueError(f"Timeframe with ID {timeframe_id} not found.")

    if not timeframe.images_data:
      timeframe.images_data = json.dumps({})

    timeframe_images_data = json.loads(timeframe.images_data)
    timeframe_images_data[photo_filename] = encoded_string
    timeframe.images_data = json.dumps(timeframe_images_data)
    db.session.commit()
    logging.info(f"Successfully saved image for timeframe {timeframe_id}.")
    return True
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
      thumbnail_images_data=json.dumps(new_thumbnail_images_data))
  db.session.add(new_timeframe)
  db.session.commit()

  for agent in agents_data:
    logging.info(f"Processing agent: {agent['id']}")

    # Create a copy of the agent data
    updated_agent_data = agent.copy()

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
            f"Please update the agent data based on the following instructions:\n{' '.join(instructions.values())[:max_chatgpt_prompt_length]}"
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
      raise ValueError(
          f"Incomplete or invalid JSON response: {response.choices[0].message.content}"
      )

    # DALL-E - Generate new profile picture
    image_prompt = updated_agent_data.get('image_prompt', '')
    dalle_prompt = f"{' '.join(instructions.values())} {json.load(open('abe/abe-instructions.json'))['dalle_modify_agents_instructions']} {image_prompt}"[:
                                                                                                                                                          max_dalle_prompt_length]
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
          logging.warning(
              f"Failed to generate DALL-E image for agent {agent['id']} due to prompt length."
          )
          updated_agent_data['photo_path'] = agent[
              'photo_path']  # Keep the original photo path
          break

    if dalle_response is None:
      logging.warning(
          f"Failed to generate DALL-E image for agent {agent['id']} after multiple retries."
      )
      updated_agent_data['photo_path'] = agent[
          'photo_path']  # Keep the original photo path
    else:
      image_url = dalle_response.data[0].url
      timeframe_id = new_timeframe.id
      photo_filename = f"{agent['id']}_iteration_{len(json.loads(new_timeframe.images_data))+1}.png"

      success = save_image_to_database(image_url, timeframe_id, photo_filename)
      if success:
        logging.info(
            f"Image {photo_filename} saved successfully to timeframe {timeframe_id}"
        )
      else:
        logging.error(
            f"Failed to save image {photo_filename} to timeframe {timeframe_id}"
        )

      updated_agent_data['photo_path'] = photo_filename
      logging.info(f"Updated photo path: {updated_agent_data['photo_path']}")

    # Add the updated agent data to the new_timeframe.agents_data list
    new_timeframe_agents_data = json.loads(new_timeframe.agents_data)
    new_timeframe_agents_data.append(updated_agent_data)
    new_timeframe.agents_data = json.dumps(new_timeframe_agents_data)
    logging.info(f"Agent data updated for: {agent['id']}")

  db.session.commit()

  summarize_process_agents(new_timeframe, payload, current_user)

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

  # Generate a default meeting name if not provided in the payload
  original_name = payload.get("meeting_name", "Untitled Meeting")
  meeting_name = original_name.replace(" ", "_")

  meeting_responses = []

  # Initialize a dictionary to store previous responses
  previous_responses = {}

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

        # Append previous responses to the agent_payload
        for prev_agent_id, prev_responses in previous_responses.items():
          if question_id in prev_responses:
            agent_payload["messages"].append({
                "role":
                "assistant",
                "content":
                f"Agent {prev_agent_id}'s response: {prev_responses[question_id]}"
            })

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

      # Store the current agent's responses for future reference
      previous_responses[agent["id"]] = responses

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

      # Append previous responses to the agent_payload
      for prev_agent_id, prev_responses in previous_responses.items():
        agent_payload["messages"].append({
            "role":
            "assistant",
            "content":
            f"Agent {prev_agent_id}'s responses:\n{json.dumps(prev_responses, indent=2)}"
        })

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

      # Store the current agent's responses for future reference
      previous_responses[agent["id"]] = responses

    agent_response["responses"] = responses
    meeting_responses.append(agent_response)
    logging.info(f"Processed agent: {agent['id']}")

  logging.info(f"Meeting responses: {meeting_responses[:142]}")

  # Find the existing meeting by ID
  meeting = Meeting.query.get(payload["meeting_id"])

  if meeting:
    # Update the meeting with the generated responses
    meeting.agents = json.dumps(agents_data)
    meeting.questions = json.dumps(questions)
    meeting.answers = json.dumps(meeting_responses)
    db.session.commit()

    process_meeting_summary(meeting, current_user)

    return meeting_responses
  else:
    raise ValueError(f"Meeting with ID {payload['meeting_id']} not found")


def generate_new_agent(agent_name, jobtitle, agent_description, current_user):
  # Generate unique_id and timestamp
  unique_id = str(uuid.uuid4())
  timestamp = datetime.datetime.now().isoformat()
  email = f"{agent_name.lower()}@{os.environ['DOMAIN_NAME']}"

  # Check for duplicate agent IDs and append a sequential number if needed
  agent_id = agent_name
  counter = 1
  while Agent.query.filter_by(id=agent_id).first():
    agent_id = f"{agent_name}_{counter}"
    counter += 1
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
      'id':
      agent_id,  # Use the generated agent_id with sequential number if needed
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

  photo_filename = f"{agent_name}.png"
  logging.info(f"New photo filename: {photo_filename[:142]}")

  img_data = requests.get(image_url).content
  encoded_string = base64.b64encode(img_data).decode('utf-8')

  # Update the photo_path in new_agent_data before storing the image data
  photo_filename = f"{agent_name}.png"
  new_agent_data['photo_path'] = f"/images/{photo_filename}"

  # Store the image data in the new_agent_data dictionary using the photo_path as the key
  new_agent_data['image_data'] = {new_agent_data['photo_path']: encoded_string}

  # Generate thumbnail image
  thumbnail_size = (200, 200)
  img = Image.open(BytesIO(img_data))
  img.thumbnail(thumbnail_size)
  thumbnail_buffer = BytesIO()
  img.save(thumbnail_buffer, format='PNG')
  thumbnail_data = thumbnail_buffer.getvalue()
  thumbnail_encoded_string = base64.b64encode(thumbnail_data).decode('utf-8')

  # Store the thumbnail image data in the new_agent_data dictionary using the photo_path as the key
  new_agent_data['thumbnail_image_data'] = {
      new_agent_data['photo_path'] + '_thumbnail': thumbnail_encoded_string
  }

  db.session.commit()

  new_agent_data['photo_path'] = f"/images/{photo_filename}"
  logging.info(f"Updated photo path: {new_agent_data['photo_path']}")

  if current_user.agents_data is None:
    current_user.agents_data = []

  current_user.agents_data.append(new_agent_data)
  db.session.commit()

  new_agent = Agent(id=new_agent_data['id'],
                    user_id=current_user.id,
                    data=new_agent_data)
  db.session.add(new_agent)
  db.session.commit()

  logging.info(f"Added new agent data to user's agents_data: {new_agent_data}")
  logging.info(f"Photo filename: {photo_filename}")
  logging.info(
      f"Image data stored in new_agent_data['image_data']: {new_agent_data['image_data'].get(new_agent_data['photo_path'], '')[:50]}..."
  )
  logging.info(
      f"Thumbnail image data stored in new_agent_data['thumbnail_image_data']: {new_agent_data['thumbnail_image_data'].get(new_agent_data['photo_path'] + '_thumbnail', '')[:50]}..."
  )

  return new_agent


def process_meeting_summary(meeting, current_user):
  logging.info("Entering process_meeting_summary function")

  # Load instructions from abe/abe-instructions.json
  with open("abe/abe-instructions.json", "r") as file:
    abe_instructions = json.load(file)
    meeting_summary_instructions = abe_instructions.get(
        "meeting_summary_instructions", "")
    meeting_summary_dalle = abe_instructions.get("meeting_summary_dalle", "")

  agents_data = json.loads(meeting.agents)
  questions = json.loads(meeting.questions)
  answers = json.loads(meeting.answers)

  # Prepare the API payload for meeting summary
  summary_payload = {
      "model":
      "gpt-4-turbo-preview",
      "messages": [{
          "role": "system",
          "content": meeting_summary_instructions
      }, {
          "role":
          "user",
          "content":
          f"Meeting Name: {meeting.name}\nQuestions: {json.dumps(questions)}\nAnswers: {json.dumps(answers)}\n\nAgents Data:\n{json.dumps(agents_data, indent=2)}\n\nPlease generate a concise summary of the meeting."
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

      logging.info("Sending request to OpenAI API for meeting summary")
      response = client.chat.completions.create(**summary_payload)
      logging.info("Received response from OpenAI API for meeting summary")

      # Deduct credits based on the API call
      credits_used = 5  # Deduct 5 credits for gpt-4 models

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

  meeting_summary = response.choices[0].message.content.strip()
  meeting.summary = meeting_summary  # Store the meeting summary

  logging.info(f"Meeting summary generated: {meeting_summary[:100]}...")
  logging.info(
      f"Storing meeting summary in meeting.summary for Meeting ID: {meeting.id}"
  )

  db.session.commit()  # Commit the changes to the database
  logging.info(
      f"Meeting summary committed to the database for Meeting ID: {meeting.id}"
  )

  # Prepare the API payload for meeting image
  image_prompt = f"{meeting_summary_dalle}\n\nMeeting Summary: {meeting_summary}\n\nAgents Data:\n"
  for agent in agents_data:
    image_prompt += f"ID: {agent['id']}, Job Title: {agent['jobtitle']}, Summary: {agent['summary']}, Image Prompt: {agent['image_prompt']}\n"

  # DALL-E - Generate meeting image
  max_retries = 12
  retry_delay = 5
  retry_count = 0
  while retry_count < max_retries:
    try:
      if current_user.credits is None or current_user.credits < 10:
        raise Exception("Insufficient credits, please add more")

      dalle_response = client.images.generate(
          model="dall-e-3",
          prompt=image_prompt[:5000],
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

  img_data = requests.get(image_url).content
  meeting.image_data = base64.b64encode(img_data).decode(
      'utf-8')  # Store the encoded image data

  logging.info(f"Meeting image data generated from URL: {image_url[:142]}")
  logging.info(
      f"Storing meeting image data in meeting.image_data for Meeting ID: {meeting.id}"
  )
  logging.info(
      f"Sample of stored meeting image data: {meeting.image_data[:100]}...")

  # Generate thumbnail image
  thumbnail_size = (200, 200)
  img = Image.open(BytesIO(img_data))
  img.thumbnail(thumbnail_size)
  thumbnail_buffer = BytesIO()
  img.save(thumbnail_buffer, format='PNG')
  thumbnail_data = thumbnail_buffer.getvalue()
  meeting.thumbnail_image_data = base64.b64encode(thumbnail_data).decode(
      'utf-8')

  logging.info(f"Meeting thumbnail image data generated")
  logging.info(
      f"Storing meeting thumbnail image data in meeting.thumbnail_image_data for Meeting ID: {meeting.id}"
  )
  logging.info(
      f"Sample of stored meeting thumbnail image data: {meeting.thumbnail_image_data[:100]}..."
  )

  db.session.commit()  # Commit the changes to the database
  logging.info(
      f"Meeting image data and thumbnail image data committed to the database for Meeting ID: {meeting.id}"
  )

  logging.info(f"Verifying stored data for Meeting ID: {meeting.id}")
  logging.info(f"Meeting summary from database: {meeting.summary[:100]}...")
  logging.info(
      f"Meeting image data from database: {meeting.image_data[:100]}...")
  logging.info(
      f"Meeting thumbnail image data from database: {meeting.thumbnail_image_data[:100]}..."
  )

  logging.info("Meeting summary and image generated successfully")


def summarize_process_agents(new_timeframe, payload, current_user):
  logging.info("Entering summarize_process_agents function")

  # Load instructions from abe/abe-instructions.json
  with open("abe/abe-instructions.json", "r") as file:
    abe_instructions = json.load(file)
    summarize_process_agents_instructions = abe_instructions.get(
        "summarize_process_agents_instructions", "")
    summarize_process_agents_dalle = abe_instructions.get(
        "summarize_process_agents_dalle", "")

  agents_data = json.loads(new_timeframe.agents_data)
  instructions = payload["instructions"]

  # Prepare the API payload for process agents summary
  summary_payload = {
      "model":
      "gpt-4-turbo-preview",
      "messages": [{
          "role": "system",
          "content": summarize_process_agents_instructions
      }, {
          "role":
          "user",
          "content":
          f"Timeframe Name: {new_timeframe.name}\nInstructions: {json.dumps(instructions)}\n\nAgents Data:\n{json.dumps(agents_data, indent=2)}\n\nPlease generate a concise summary of the process agents operation."
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

      logging.info("Sending request to OpenAI API for process agents summary")
      response = client.chat.completions.create(**summary_payload)
      logging.info(
          "Received response from OpenAI API for process agents summary")

      # Deduct credits based on the API call
      credits_used = 5  # Deduct 5 credits for gpt-4 models

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

  process_agents_summary = response.choices[0].message.content.strip()
  new_timeframe.summary = process_agents_summary  # Store the process agents summary

  logging.info(
      f"Process agents summary generated: {process_agents_summary[:100]}...")
  logging.info(
      f"Storing process agents summary in new_timeframe.summary for Timeframe ID: {new_timeframe.id}"
  )

  # Prepare the prompt for process agents image
  image_prompt = f"{summarize_process_agents_dalle}\n\nProcess Agents Summary: {process_agents_summary}\n\nAgents Data:\n"
  for agent in agents_data:
    image_prompt += f"ID: {agent['id']}, Job Title: {agent['jobtitle']}, Summary: {agent['summary']}, Image Prompt: {agent['image_prompt']}\n"

  # DALL-E - Generate process agents image
  max_retries = 12
  retry_delay = 5
  retry_count = 0
  while retry_count < max_retries:
    try:
      if current_user.credits is None or current_user.credits < 10:
        raise Exception("Insufficient credits, please add more")

      logging.info("Sending request to OpenAI API for process agents image")
      dalle_response = client.images.generate(
          model="dall-e-3",
          prompt=image_prompt[:5000],
          quality="standard",
          size="1024x1024",
          n=1,
      )
      logging.info(
          "Received response from OpenAI API for process agents image")

      current_user.credits -= 10  # Deduct 10 credits for DALL-E models
      db.session.commit()
      break
    except APIError as e:
      logging.error(f"OpenAI API error: {e}")
      logging.error(f"DALL-E prompt: {image_prompt}")
      retry_count += 1
      if retry_count < max_retries:
        time.sleep(retry_delay)
        retry_delay *= 2
      else:
        logging.error("Max retries reached. Skipping image generation.")
        new_timeframe.image_data = None
        new_timeframe.thumbnail_image_data = None
        break

  if dalle_response:
    image_url = dalle_response.data[0].url
    logging.info(f"Generated image URL: {image_url}")

    img_data = requests.get(image_url).content
    new_timeframe.image_data = base64.b64encode(img_data).decode(
        'utf-8')  # Store the image data

    logging.info(f"Process agents image data generated from URL: {image_url}")
    logging.info(
        f"Storing process agents image data in new_timeframe.image_data for Timeframe ID: {new_timeframe.id}"
    )
    logging.info(
        f"Sample of stored process agents image data: {new_timeframe.image_data[:100]}..."
    )

    # Generate thumbnail image
    thumbnail_size = (200, 200)
    img = Image.open(BytesIO(img_data))
    img.thumbnail(thumbnail_size)
    thumbnail_buffer = BytesIO()
    img.save(thumbnail_buffer, format='PNG')
    thumbnail_data = thumbnail_buffer.getvalue()
    new_timeframe.thumbnail_image_data = base64.b64encode(
        thumbnail_data).decode('utf-8')  # Store the thumbnail image data

    logging.info(f"Process agents thumbnail image data generated")
    logging.info(
        f"Storing process agents thumbnail image data in new_timeframe.thumbnail_image_data for Timeframe ID: {new_timeframe.id}"
    )
    logging.info(
        f"Sample of stored process agents thumbnail image data: {new_timeframe.thumbnail_image_data[:100]}..."
    )
  else:
    logging.warning("No image generated for process agents summary")
    new_timeframe.image_data = None
    new_timeframe.thumbnail_image_data = None

  db.session.commit()  # Commit the changes to the database
  logging.info(
      f"Process agents summary, image data, and thumbnail image data committed to the database for Timeframe ID: {new_timeframe.id}"
  )

  logging.info(f"Verifying stored data for Timeframe ID: {new_timeframe.id}")
  logging.info(
      f"Process agents summary from database: {new_timeframe.summary[:100]}..."
  )
  logging.info(
      f"Process agents image data from database: {new_timeframe.image_data[:100] if new_timeframe.image_data else None}..."
  )
  logging.info(
      f"Process agents thumbnail image data from database: {new_timeframe.thumbnail_image_data[:100] if new_timeframe.thumbnail_image_data else None}..."
  )

  logging.info("Process agents summary and image generation completed")
