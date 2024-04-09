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
import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO


client = OpenAI()
openai_api_key = os.environ['OPENAI_API_KEY']

logging.basicConfig(level=logging.INFO)

def process_agents(payload, current_user):
  logging.info("Entering process_agents function")
  agents_data = payload["agents_data"]
  instructions = payload["instructions"]

  new_timeframe = create_new_timeframe(payload, current_user)

  for agent in agents_data:
      process_single_agent(agent, instructions, new_timeframe, current_user)

  db.session.commit()
  logging.info("Database session committed after processing agents")

  return new_timeframe


def create_new_timeframe(payload, current_user):
  new_timeframe = Timeframe(
      name=payload["timeframe_name"],
      user_id=current_user.id,
      agents_data=[],
      images_data={},
      thumbnail_images_data={}
  )
  db.session.add(new_timeframe)
  db.session.commit()
  return new_timeframe


def process_single_agent(agent, instructions, new_timeframe, current_user):
  logging.info(f"Processing agent: {agent['id']}")

  updated_agent_data = prepare_agent_data(agent)
  updated_agent_data = update_agent_data_with_openai(updated_agent_data, instructions, current_user)
  vision_description = get_vision_description(updated_agent_data, current_user)
  updated_agent_data["vision_description_image_prompt"] = vision_description
  updated_agent_data = generate_new_profile_picture(updated_agent_data, instructions, new_timeframe, current_user)

  new_timeframe.agents_data.append(updated_agent_data)
  logging.info(f"Agent data updated for: {agent['id']}")

  db.session.commit()


def prepare_agent_data(agent):
  updated_agent_data = agent.copy()
  excluded_fields = ['id', 'email', 'unique_id', 'timestamp', 'photo_path']
  for field in excluded_fields:
      if field in updated_agent_data:
          del updated_agent_data[field]
  return updated_agent_data


def update_agent_data_with_openai(updated_agent_data, instructions, current_user):
  agent_payload = {
      "model": "gpt-4-turbo-preview",
      "response_format": {"type": "json_object"},
      "messages": [
          {
              "role": "system",
              "content": f"You are a helpful assistant designed to update agent data in JSON format based on the following instructions:\n{json.load(open('abe/abe-instructions.json'))['modify_agents_json_instructions']}"
          },
          {
              "role": "user",
              "content": f"Here is the agent data in JSON format:\n{json.dumps(updated_agent_data)}"
          },
          {
              "role": "user",
              "content": f"Please update the agent data based on the following instructions:\n{' '.join(instructions.values())}"
          },
          {
              "role": "user",
              "content": "Return the updated agent data as a JSON object."
          }
      ],
  }

  response = call_openai_api(agent_payload, current_user)
  updated_agent_data = json.loads(response.choices[0].message.content)

  return updated_agent_data


def get_vision_description(updated_agent_data, current_user):
  photo_filename = updated_agent_data['photo_path'].split('/')[-1]
  image_data = current_user.images_data.get(photo_filename) if current_user.images_data else None

  if image_data:
      vision_payload = {
          "model": "gpt-4-vision-preview",
          "messages": [
              {
                  "role": "user",
                  "content": [
                      {
                          "type": "text",
                          "text": "Provide a very detailed description of this image with explicit instructions for how to re-create it:"
                      },
                      {
                          "type": "image_url",
                          "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                      }
                  ]
              }
          ],
      }

      vision_response = call_openai_api(vision_payload, current_user)
      vision_description = vision_response.choices[0].message.content.strip()
      logging.info(f"Vision API response: {vision_description}")
  else:
      logging.warning(f"Image data not found for {photo_filename}")
      vision_description = ""

  return vision_description


def generate_new_profile_picture(updated_agent_data, instructions, new_timeframe, current_user):
  image_prompt = updated_agent_data.get('image_prompt', '')
  max_prompt_length = 5000
  dalle_prompt = f"{' '.join(instructions.values())} {json.load(open('abe/abe-instructions.json'))['dalle_modify_agents_instructions']} {image_prompt} {updated_agent_data.get('vision_description_image_prompt', '')}"[:max_prompt_length]
  updated_agent_data[f"{updated_agent_data['id']}_image_instructions"] = dalle_prompt
  logging.info(f"DALL-E prompt: {dalle_prompt}")

  dalle_response = call_dalle_api(dalle_prompt, current_user)

  if dalle_response is None:
      logging.warning(f"Failed to generate DALL-E image for agent {updated_agent_data['id']} after multiple retries.")
      updated_agent_data['photo_path'] = updated_agent_data['photo_path']
  else:
      image_url = dalle_response.data[0].url
      logging.info(f"Generated image URL: {image_url}")
      new_photo_filename = f"{updated_agent_data['id']}_iteration_{len(new_timeframe.images_data)+1}.png"
      logging.info(f"New photo filename: {new_photo_filename}")

      img_data = requests.get(image_url).content
      encoded_string = base64.b64encode(img_data).decode('utf-8')
      new_timeframe.images_data[new_photo_filename] = encoded_string

      thumbnail_encoded_string = generate_thumbnail_image(img_data)
      new_timeframe.thumbnail_images_data[new_photo_filename] = thumbnail_encoded_string

      updated_agent_data['photo_path'] = f"timeframe_{new_timeframe.id}_{new_photo_filename}"
      logging.info(f"Updated photo path: {updated_agent_data['photo_path']}")

  return updated_agent_data


def generate_thumbnail_image(img_data):
  thumbnail_size = (200, 200)
  img = Image.open(BytesIO(img_data))
  img.thumbnail(thumbnail_size)
  thumbnail_buffer = BytesIO()
  img.save(thumbnail_buffer, format='PNG')
  thumbnail_data = thumbnail_buffer.getvalue()
  thumbnail_encoded_string = base64.b64encode(thumbnail_data).decode('utf-8')
  return thumbnail_encoded_string


def call_openai_api(payload, current_user):
  max_retries = 12
  retry_delay = 5
  retry_count = 0
  logging.info(f"Current credit balance before API call: {current_user.credits}")

  while retry_count < max_retries:
      try:
          if current_user.credits is None or current_user.credits < 5:
              raise Exception("Insufficient credits, please add more")

          response = client.chat.completions.create(**payload)

          # Deduct credits based on the API call
          if payload["model"].startswith("gpt-4"):
              credits_used = 5
          else:
              raise ValueError(f"Unexpected model: {payload['model']}")

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

  logging.info(f"Current credit balance after API call: {current_user.credits}")
  return response


def call_dalle_api(dalle_prompt, current_user):
  max_retries = 1
  retry_delay = 30
  retry_count = 0
  dalle_response = None

  while retry_count < max_retries:
      try:
          prompt_chunks = [dalle_prompt[i:i+2000] for i in range(0, len(dalle_prompt), 2000)]

          for chunk in prompt_chunks:
              try:
                  dalle_response = client.images.generate(
                      model="dall-e-3",
                      prompt=chunk,
                      quality="standard",
                      size="1024x1024",
                      n=1,
                  )
                  current_user.credits -= 10
                  db.session.commit()
                  break
              except APIError as e:
                  logging.error(f"OpenAI API error for chunk: {e}")
                  logging.error(f"DALL-E prompt chunk: {chunk}")

          if dalle_response is not None:
              break
      except APIError as e:
          logging.error(f"OpenAI API error: {e}")
          logging.error(f"DALL-E prompt: {dalle_prompt}")
          retry_count += 1
          if retry_count < max_retries:
              time.sleep(retry_delay)
              retry_delay *= 2
          else:
              logging.warning(f"Failed to generate DALL-E image due to prompt length.")
              break

  return dalle_response

class TestProcessAgents(unittest.TestCase):
  @patch('your_module.db.session.commit')
  @patch('your_module.create_new_timeframe')
  @patch('your_module.process_single_agent')
  def test_process_agents(self, mock_process_single_agent, mock_create_new_timeframe, mock_commit):
      payload = {
          "agents_data": [{"id": 1}, {"id": 2}],
          "instructions": {"key": "value"}
      }
      current_user = MagicMock()
      new_timeframe = MagicMock()
      mock_create_new_timeframe.return_value = new_timeframe

      result = process_agents(payload, current_user)

      mock_create_new_timeframe.assert_called_once_with(payload, current_user)
      mock_process_single_agent.assert_any_call({"id": 1}, {"key": "value"}, new_timeframe, current_user)
      mock_process_single_agent.assert_any_call({"id": 2}, {"key": "value"}, new_timeframe, current_user)
      mock_commit.assert_called_once()
      self.assertEqual(result, new_timeframe)

  @patch('your_module.db.session.commit')
  @patch('your_module.db.session.add')
  def test_create_new_timeframe(self, mock_add, mock_commit):
      payload = {"timeframe_name": "Test Timeframe"}
      current_user = MagicMock(id=1)

      result = create_new_timeframe(payload, current_user)

      self.assertIsInstance(result, Timeframe)
      self.assertEqual(result.name, "Test Timeframe")
      self.assertEqual(result.user_id, 1)
      self.assertEqual(result.agents_data, [])
      self.assertEqual(result.images_data, {})
      self.assertEqual(result.thumbnail_images_data, {})
      mock_add.assert_called_once_with(result)
      mock_commit.assert_called_once()

  @patch('your_module.db.session.commit')
  @patch('your_module.generate_new_profile_picture')
  @patch('your_module.get_vision_description')
  @patch('your_module.update_agent_data_with_openai')
  @patch('your_module.prepare_agent_data')


  
  def test_process_single_agent(self, mock_prepare_agent_data, mock_update_agent_data_with_openai,
                                mock_get_vision_description, mock_generate_new_profile_picture, mock_commit):
      agent = {"id": 1}
      instructions = {"key": "value"}
      new_timeframe = MagicMock()
      current_user = MagicMock()
      updated_agent_data = {"id": 1, "name": "Agent 1"}
      vision_description = "Vision description"
      mock_prepare_agent_data.return_value = updated_agent_data
      mock_update_agent_data_with_openai.return_value = updated_agent_data
      mock_get_vision_description.return_value = vision_description
      mock_generate_new_profile_picture.return_value = updated_agent_data
  
      process_single_agent(agent, instructions, new_timeframe, current_user)
  
      mock_prepare_agent_data.assert_called_once_with(agent)
      mock_update_agent_data_with_openai.assert_called_once_with(updated_agent_data, instructions, current_user)
      mock_get_vision_description.assert_called_once_with(updated_agent_data, current_user)
      self.assertEqual(updated_agent_data["vision_description_image_prompt"], vision_description)
      mock_generate_new_profile_picture.assert_called_once_with(updated_agent_data, instructions, new_timeframe, current_user)
      new_timeframe.agents_data.append.assert_called_once_with(updated_agent_data)
      mock_commit.assert_called_once()

def test_prepare_agent_data(self):
    agent = {
        "id": 1,
        "email": "agent@example.com",
        "unique_id": "abc123",
        "timestamp": "2023-05-25",
        "photo_path": "/path/to/photo.jpg",
        "name": "Agent 1"
    }

    result = prepare_agent_data(agent)

    expected_result = {"name": "Agent 1"}
    self.assertEqual(result, expected_result)
  

  @patch('your_module.call_openai_api')
  def test_update_agent_data_with_openai(self, mock_call_openai_api):
      updated_agent_data = {"name": "Agent 1"}
      instructions = {"key": "value"}
      current_user = MagicMock()
      mock_response = MagicMock()
      mock_response.choices[0].message.content = json.dumps({"name": "Updated Agent 1"})
      mock_call_openai_api.return_value = mock_response

      result = update_agent_data_with_openai(updated_agent_data, instructions, current_user)

      expected_payload = {
          "model": "gpt-4-turbo-preview",
          "response_format": {"type": "json_object"},
          "messages": [
              {
                  "role": "system",
                  "content": f"You are a helpful assistant designed to update agent data in JSON format based on the following instructions:\n{json.load(open('abe/abe-instructions.json'))['modify_agents_json_instructions']}"
              },
              {
                  "role": "user",
                  "content": f"Here is the agent data in JSON format:\n{json.dumps(updated_agent_data)}"
              },
              {
                  "role": "user",
                  "content": f"Please update the agent data based on the following instructions:\n{' '.join(instructions.values())}"
              },
              {
                  "role": "user",
                  "content": "Return the updated agent data as a JSON object."
              }
          ],
      }
      mock_call_openai_api.assert_called_once_with(expected_payload, current_user)
      self.assertEqual(result, {"name": "Updated Agent 1"})

  @patch('your_module.call_openai_api')
  def test_get_vision_description_with_image_data(self, mock_call_openai_api):
      updated_agent_data = {"photo_path": "/path/to/photo.jpg"}
      current_user = MagicMock()
      current_user.images_data = {"photo.jpg": "base64_image_data"}
      mock_response = MagicMock()
      mock_response.choices[0].message.content = "Detailed vision description"
      mock_call_openai_api.return_value = mock_response

      result = get_vision_description(updated_agent_data, current_user)

      expected_payload = {
          "model": "gpt-4-vision-preview",
          "messages": [
              {
                  "role": "user",
                  "content": [
                      {
                          "type": "text",
                          "text": "Provide a very detailed description of this image with explicit instructions for how to re-create it:"
                      },
                      {
                          "type": "image_url",
                          "image_url": {"url": "data:image/jpeg;base64,base64_image_data"}
                      }
                  ]
              }
          ],
      }
      mock_call_openai_api.assert_called_once_with(expected_payload, current_user)
      self.assertEqual(result, "Detailed vision description")

  def test_get_vision_description_without_image_data(self):
      updated_agent_data = {"photo_path": "/path/to/photo.jpg"}
      current_user = MagicMock()
      current_user.images_data = None

      result = get_vision_description(updated_agent_data, current_user)

      self.assertEqual(result, "")


  @patch('your_module.call_dalle_api')
  @patch('your_module.requests.get')
  def test_generate_new_profile_picture_success(self, mock_requests_get, mock_call_dalle_api):
      updated_agent_data = {
          'id': 'agent1',
          'image_prompt': 'Test image prompt',
          'vision_description_image_prompt': 'Test vision description'
      }
      instructions = {'key': 'value'}
      new_timeframe = MagicMock()
      new_timeframe.images_data = {}
      new_timeframe.thumbnail_images_data = {}
      current_user = MagicMock()
      mock_dalle_response = MagicMock()
      mock_dalle_response.data = [MagicMock(url='http://example.com/image.png')]
      mock_call_dalle_api.return_value = mock_dalle_response
      mock_requests_get.return_value = MagicMock(content=b'image_data')

      result = generate_new_profile_picture(updated_agent_data, instructions, new_timeframe, current_user)

      expected_dalle_prompt = "value abe_instructions['dalle_modify_agents_instructions'] Test image prompt Test vision description"
      mock_call_dalle_api.assert_called_once_with(expected_dalle_prompt, current_user)
      self.assertEqual(updated_agent_data['agent1_image_instructions'], expected_dalle_prompt)
      self.assertEqual(result['photo_path'], 'timeframe_None_agent1_iteration_1.png')
      self.assertIn('agent1_iteration_1.png', new_timeframe.images_data)
      self.assertIn('agent1_iteration_1.png', new_timeframe.thumbnail_images_data)

  @patch('your_module.call_dalle_api')
  def test_generate_new_profile_picture_failure(self, mock_call_dalle_api):
      updated_agent_data = {'id': 'agent1', 'photo_path': 'original_path.png'}
      instructions = {'key': 'value'}
      new_timeframe = MagicMock()
      current_user = MagicMock()
      mock_call_dalle_api.return_value = None

      result = generate_new_profile_picture(updated_agent_data, instructions, new_timeframe, current_user)

      self.assertEqual(result['photo_path'], 'original_path.png')

  def test_generate_thumbnail_image(self):
      img_data = b'test_image_data'
      thumbnail_size = (200, 200)

      with patch('your_module.Image.open') as mock_image_open, \
           patch('your_module.BytesIO') as mock_bytesio:
          mock_image = MagicMock()
          mock_image_open.return_value = mock_image
          mock_thumbnail_buffer = MagicMock()
          mock_bytesio.return_value = mock_thumbnail_buffer
          mock_thumbnail_data = b'thumbnail_data'
          mock_thumbnail_buffer.getvalue.return_value = mock_thumbnail_data

          result = generate_thumbnail_image(img_data)

          mock_image_open.assert_called_once_with(mock_bytesio(img_data))
          mock_image.thumbnail.assert_called_once_with(thumbnail_size)
          mock_image.save.assert_called_once_with(mock_thumbnail_buffer, format='PNG')
          self.assertEqual(result, base64.b64encode(mock_thumbnail_data).decode('utf-8'))

  @patch('your_module.client.chat.completions.create')
  def test_call_openai_api_success(self, mock_create):
      payload = {'model': 'gpt-4', 'messages': []}
      current_user = MagicMock(credits=10)
      mock_response = MagicMock()
      mock_create.return_value = mock_response

      result = call_openai_api(payload, current_user)

      mock_create.assert_called_once_with(**payload)
      self.assertEqual(current_user.credits, 5)
      self.assertEqual(result, mock_response)

  @patch('your_module.client.chat.completions.create')
  def test_call_openai_api_insufficient_credits(self, mock_create):
      payload = {'model': 'gpt-4', 'messages': []}
      current_user = MagicMock(credits=0)

      with self.assertRaises(Exception) as context:
          call_openai_api(payload, current_user)

      self.assertEqual(str(context.exception), "Insufficient credits, please add more")
      mock_create.assert_not_called()

  @patch('your_module.client.chat.completions.create')
  def test_call_openai_api_unexpected_model(self, mock_create):
      payload = {'model': 'unexpected_model', 'messages': []}
      current_user = MagicMock(credits=10)

      with self.assertRaises(ValueError) as context:
          call_openai_api(payload, current_user)

      self.assertEqual(str(context.exception), "Unexpected model: unexpected_model")
      mock_create.assert_not_called()

  @patch('your_module.client.chat.completions.create', side_effect=APIError('API error'))
  @patch('your_module.time.sleep')
  def test_call_openai_api_retry_and_raise(self, mock_sleep, mock_create):
      payload = {'model': 'gpt-4', 'messages': []}
      current_user = MagicMock(credits=10)

      with self.assertRaises(APIError) as context:
          call_openai_api(payload, current_user)

      self.assertEqual(str(context.exception), 'API error')
      self.assertEqual(mock_create.call_count, 12)  # Retry 12 times
      self.assertEqual(mock_sleep.call_count, 11)  


def call_dalle_api(dalle_prompt, current_user):
  max_retries = 1
  retry_delay = 30
  retry_count = 0
  dalle_response = None

  while retry_count < max_retries:
      try:
          prompt_chunks = [dalle_prompt[i:i+2000] for i in range(0, len(dalle_prompt), 2000)]

          for chunk in prompt_chunks:
              try:
                  dalle_response = client.images.generate(
                      model="dall-e-3",
                      prompt=chunk,
                      quality="standard",
                      size="1024x1024",
                      n=1,
                  )
                  current_user.credits -= 10
                  db.session.commit()
                  break
              except APIError as e:
                  logging.error(f"OpenAI API error for chunk: {e}")
                  logging.error(f"DALL-E prompt chunk: {chunk}")

          if dalle_response is not None:
              break
      except APIError as e:
          logging.error(f"OpenAI API error: {e}")
          logging.error(f"DALL-E prompt: {dalle_prompt}")
          retry_count += 1
          if retry_count < max_retries:
              time.sleep(retry_delay)
              retry_delay *= 2
          else:
              logging.warning(f"Failed to generate DALL-E image due to prompt length.")
              break

  return dalle_response



def conduct_meeting(payload, current_user):
  logging.info("Entering conduct_meeting function")
  agents_data = payload["agents_data"]
  questions = payload["questions"]
  form_llm_instructions = payload.get("llm_instructions", "")
  request_type = payload["request_type"]

  question_instructions = load_question_instructions()
  llm_instructions_combined = combine_instructions(question_instructions, form_llm_instructions)

  log_meeting_details(agents_data, questions, llm_instructions_combined, request_type)

  meeting_responses = process_agents(agents_data, questions, request_type, llm_instructions_combined, current_user)

  logging.info(f"Meeting responses: {meeting_responses[:142]}")
  return meeting_responses

class TestConductMeeting(unittest.TestCase):
  @patch('your_module.process_agents')
  @patch('your_module.log_meeting_details')
  @patch('your_module.combine_instructions')
  @patch('your_module.load_question_instructions')
  def test_conduct_meeting(self, mock_load_instructions, mock_combine_instructions,
                           mock_log_details, mock_process_agents):
      payload = {
          "agents_data": [{"id": 1}, {"id": 2}],
          "questions": {"q1": "Question 1", "q2": "Question 2"},
          "llm_instructions": "Additional instructions",
          "request_type": "iterative"
      }
      current_user = MagicMock()
      mock_load_instructions.return_value = "Loaded instructions"
      mock_combine_instructions.return_value = "Combined instructions"
      mock_process_agents.return_value = [{"id": 1, "responses": {"q1": "Answer 1"}},
                                          {"id": 2, "responses": {"q2": "Answer 2"}}]

      result = conduct_meeting(payload, current_user)

      mock_load_instructions.assert_called_once()
      mock_combine_instructions.assert_called_once_with("Loaded instructions", "Additional instructions")
      mock_log_details.assert_called_once_with([{"id": 1}, {"id": 2}],
                                               {"q1": "Question 1", "q2": "Question 2"},
                                               "Combined instructions", "iterative")
      mock_process_agents.assert_called_once_with([{"id": 1}, {"id": 2}],
                                                  {"q1": "Question 1", "q2": "Question 2"},
                                                  "iterative", "Combined instructions", current_user)
      self.assertEqual(result, [{"id": 1, "responses": {"q1": "Answer 1"}},
                                {"id": 2, "responses": {"q2": "Answer 2"}}])

def load_question_instructions():
  with open("abe/abe-instructions.json", "r") as file:
      abe_instructions = json.load(file)
      question_instructions = abe_instructions.get("question_instructions", "")
  return question_instructions

class TestLoadQuestionInstructions(unittest.TestCase):
  def test_load_question_instructions(self):
      mock_data = '{"question_instructions": "Test instructions"}'
      with patch("builtins.open", mock_open(read_data=mock_data)):
          result = load_question_instructions()
          self.assertEqual(result, "Test instructions")

  def test_load_question_instructions_missing_key(self):
      mock_data = '{}'
      with patch("builtins.open", mock_open(read_data=mock_data)):
          result = load_question_instructions()
          self.assertEqual(result, "")

def combine_instructions(question_instructions, form_llm_instructions):
  return f"{question_instructions} {form_llm_instructions}".strip()

class TestCombineInstructions(unittest.TestCase):
  def test_combine_instructions(self):
      result = combine_instructions("Question instructions", "Form instructions")
      self.assertEqual(result, "Question instructions Form instructions")

  def test_combine_instructions_empty(self):
      result = combine_instructions("", "")
      self.assertEqual(result, "")


def log_meeting_details(agents_data, questions, llm_instructions_combined, request_type):
  logging.info(f"Agents data: {agents_data[:142]}")
  logging.info(f"Questions: {questions[:142]}")
  logging.info(f"LLM instructions: {llm_instructions_combined[:142]}")
  logging.info(f"Request type: {request_type[:142]}")

class TestLogMeetingDetails(unittest.TestCase):
  def test_log_meeting_details(self):
      with self.assertLogs(level=logging.INFO) as log:
          log_meeting_details([{"id": 1}, {"id": 2}],
                              {"q1": "Question 1", "q2": "Question 2"},
                              "Combined instructions", "iterative")
          self.assertEqual(len(log.output), 4)
          self.assertIn("Agents data: [{'id': 1}, {'id': 2}]", log.output[0])
          self.assertIn("Questions: {'q1': 'Question 1', 'q2': 'Question 2'}", log.output[1])
          self.assertIn("LLM instructions: Combined instructions", log.output[2])
          self.assertIn("Request type: iterative", log.output[3])


def process_agents(agents_data, questions, request_type, llm_instructions_combined, current_user):
  meeting_responses = []
  for agent in agents_data:
      agent_response = process_single_agent(agent, questions, request_type, llm_instructions_combined, current_user)
      meeting_responses.append(agent_response)
  return meeting_responses

class TestProcessAgents(unittest.TestCase):
  @patch('your_module.process_single_agent')
  def test_process_agents(self, mock_process_single_agent):
      agents_data = [{"id": 1}, {"id": 2}]
      questions = {"q1": "Question 1", "q2": "Question 2"}
      request_type = "iterative"
      llm_instructions_combined = "Combined instructions"
      current_user = MagicMock()
      mock_process_single_agent.side_effect = [{"id": 1, "responses": {"q1": "Answer 1"}},
                                               {"id": 2, "responses": {"q2": "Answer 2"}}]

      result = process_agents(agents_data, questions, request_type, llm_instructions_combined, current_user)

      self.assertEqual(mock_process_single_agent.call_count, 2)
      mock_process_single_agent.assert_any_call({"id": 1}, {"q1": "Question 1", "q2": "Question 2"},
                                                "iterative", "Combined instructions", current_user)
      mock_process_single_agent.assert_any_call({"id": 2}, {"q1": "Question 1", "q2": "Question 2"},
                                                "iterative", "Combined instructions", current_user)
      self.assertEqual(result, [{"id": 1, "responses": {"q1": "Answer 1"}},
                                {"id": 2, "responses": {"q2": "Answer 2"}}])


def process_single_agent(agent, questions, request_type, llm_instructions_combined, current_user):
  agent_response = {
      "id": agent["id"],
      "email": agent["email"],
      "questions": questions
  }

  logging.info(f"Processing agent: {agent['id']}")

  if request_type == "iterative":
      responses = process_iterative_questions(agent, questions, llm_instructions_combined, current_user)
  else:
      responses = process_combined_questions(agent, questions, llm_instructions_combined, current_user)

  agent_response["responses"] = responses
  logging.info(f"Processed agent: {agent['id']}")
  return agent_response

class TestProcessSingleAgent(unittest.TestCase):
  @patch('your_module.process_iterative_questions')
  def test_process_single_agent_iterative(self, mock_process_iterative_questions):
      agent = {"id": 1, "email": "agent1@example.com"}
      questions = {"q1": "Question 1", "q2": "Question 2"}
      request_type = "iterative"
      llm_instructions_combined = "Combined instructions"
      current_user = MagicMock()
      mock_process_iterative_questions.return_value = {"q1": "Answer 1", "q2": "Answer 2"}

      result = process_single_agent(agent, questions, request_type, llm_instructions_combined, current_user)

      mock_process_iterative_questions.assert_called_once_with({"id": 1, "email": "agent1@example.com"},
                                                               {"q1": "Question 1", "q2": "Question 2"},
                                                               "Combined instructions", current_user)
      self.assertEqual(result, {"id": 1, "email": "agent1@example.com",
                                "questions": {"q1": "Question 1", "q2": "Question 2"},
                                "responses": {"q1": "Answer 1", "q2": "Answer 2"}})

  @patch('your_module.process_combined_questions')
  def test_process_single_agent_combined(self, mock_process_combined_questions):
      agent = {"id": 1, "email": "agent1@example.com"}
      questions = {"q1": "Question 1", "q2": "Question 2"}
      request_type = "combined"
      llm_instructions_combined = "Combined instructions"
      current_user = MagicMock()
      mock_process_combined_questions.return_value = {"q1": "Answer 1", "q2": "Answer 2"}

      result = process_single_agent(agent, questions, request_type, llm_instructions_combined, current_user)

      mock_process_combined_questions.assert_called_once_with({"id": 1, "email": "agent1@example.com"},
                                                              {"q1": "Question 1", "q2": "Question 2"},
                                                              "Combined instructions", current_user)
      self.assertEqual(result, {"id": 1, "email": "agent1@example.com",
                                "questions": {"q1": "Question 1", "q2": "Question 2"},
                                "responses": {"q1": "Answer 1", "q2": "Answer 2"}})


def process_iterative_questions(agent, questions, llm_instructions_combined, current_user):
  responses = {}
  for question_id, question_text in questions.items():
      agent_payload = {
          "model": "gpt-3.5-turbo",
          "messages": [
              {
                  "role": "system",
                  "content": llm_instructions_combined
              },
              {
                  "role": "user",
                  "content": f"ID: {agent['id']}\nPersona: {agent['persona']}\nRelationships: {agent['relationships']}\nKeywords: {', '.join(agent['keywords'])}\n\nQuestion: {question_text}\n{llm_instructions_combined}\nPlease respond in JSON format."
              },
          ],
      }
      response = call_openai_api(agent_payload, current_user)
      responses[question_id] = response.choices[0].message.content.strip()
  return responses

class TestProcessIterativeQuestions(unittest.TestCase):
  @patch('your_module.call_openai_api')
  def test_process_iterative_questions(self, mock_call_openai_api):
      agent = {"id": 1, "persona": "Persona", "relationships": "Relationships", "keywords": ["Keyword1", "Keyword2"]}
      questions = {"q1": "Question 1", "q2": "Question 2"}
      llm_instructions_combined = "Combined instructions"
      current_user = MagicMock()
      mock_call_openai_api.side_effect = [
          MagicMock(choices=[MagicMock(message=MagicMock(content="Answer 1"))]),
          MagicMock(choices=[MagicMock(message=MagicMock(content="Answer 2"))])
      ]

      result = process_iterative_questions(agent, questions, llm_instructions_combined, current_user)

      self.assertEqual(mock_call_openai_api.call_count, 2)
      mock_call_openai_api.assert_any_call({
          "model": "gpt-3.5-turbo",
          "messages": [
              {"role": "system", "content": "Combined instructions"},
              {"role": "user", "content": "ID: 1\nPersona: Persona\nRelationships: Relationships\nKeywords: Keyword1, Keyword2\n\nQuestion: Question 1\nCombined instructions\nPlease respond in JSON format."}
          ]
      }, current_user)
      mock_call_openai_api.assert_any_call({
          "model": "gpt-3.5-turbo",
          "messages": [
              {"role": "system", "content": "Combined instructions"},
              {"role": "user", "content": "ID: 1\nPersona: Persona\nRelationships: Relationships\nKeywords: Keyword1, Keyword2\n\nQuestion: Question 2\nCombined instructions\nPlease respond in JSON format."}
          ]
      }, current_user)
      self.assertEqual(result, {"q1": "Answer 1", "q2": "Answer 2"})

def process_combined_questions(agent, questions, llm_instructions_combined, current_user):
  questions_text = "\n".join([
      f"Question {question_id}: {question_text}"
      for question_id, question_text in questions.items()
  ])
  agent_payload = {
      "model": "gpt-3.5-turbo",
      "messages": [
          {
              "role": "system",
              "content": llm_instructions_combined
          },
          {
              "role": "user",
              "content": f"ID: {agent['id']}\nPersona: {agent['persona']}\nRelationships: {agent['relationships']}\nKeywords: {', '.join(agent['keywords'])}\n\nPlease answer the following questions:\n{questions_text}\n{llm_instructions_combined}\nProvide your responses in JSON format."
          },
      ],
  }
  response = call_openai_api(agent_payload, current_user)
  responses = json.loads(response.choices[0].message.content.strip())
  return responses

class TestProcessCombinedQuestions(unittest.TestCase):
  @patch('your_module.call_openai_api')
  def test_process_combined_questions(self, mock_call_openai_api):
      agent = {"id": 1, "persona": "Persona", "relationships": "Relationships", "keywords": ["Keyword1", "Keyword2"]}
      questions = {"q1": "Question 1", "q2": "Question 2"}
      llm_instructions_combined = "Combined instructions"
      current_user = MagicMock()
      mock_call_openai_api.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content='{"q1": "Answer 1", "q2": "Answer 2"}'))])

      result = process_combined_questions(agent, questions, llm_instructions_combined, current_user)

      mock_call_openai_api.assert_called_once_with({
          "model": "gpt-3.5-turbo",
          "messages": [
              {"role": "system", "content": "Combined instructions"},
              {"role": "user", "content": "ID: 1\nPersona: Persona\nRelationships: Relationships\nKeywords: Keyword1, Keyword2\n\nPlease answer the following questions:\nQuestion q1: Question 1\nQuestion q2: Question 2\nCombined instructions\nProvide your responses in JSON format."}
          ]
      }, current_user)
      self.assertEqual(result, {"q1": "Answer 1", "q2": "Answer 2"})

def call_openai_api(payload, current_user):
  max_retries = 12
  retry_delay = 5
  retry_count = 0
  while retry_count < max_retries:
      try:
          if current_user.credits is None or current_user.credits < 1:
              raise Exception("Insufficient credits, please add more")

          logging.info(f"Sending request to OpenAI API")
          response = client.chat.completions.create(**payload)
          logging.info(f"Received response from OpenAI API")

          # Deduct credits based on the API call
          credits_used = 1  # Deduct 1 credit for gpt-3.5-turbo models

          current_user.credits -= credits_used
          db.session.commit()
          return response
      except APIError as e:
          logging.error(f"OpenAI API error: {e}")
          retry_count += 1
          if retry_count < max_retries:
              time.sleep(retry_delay)
              retry_delay *= 2
          else:
              raise e

            class TestCallOpenAIAPI(unittest.TestCase):
              @patch('your_module.client.chat.completions.create')
              def test_call_openai_api_success(self, mock_create):
                  payload = {"model": "gpt-3.5-turbo", "messages": []}
                  current_user = MagicMock(credits=10)
                  mock_response = MagicMock()
                  mock_create.return_value = mock_response

                  result = call_openai_api(payload, current_user)

                  mock_create.assert_called_once_with(**payload)
                  self.assertEqual(current_user.credits, 9)
                  self.assertEqual(result, mock_response)

              def test_call_openai_api_insufficient_credits(self):
                  payload = {"model": "gpt-3.5-turbo", "messages": []}
                  current_user = MagicMock(credits=0)

                  with self.assertRaises(Exception) as cm:
                      call_openai_api(payload, current_user)

                  self.assertEqual(str(cm.exception), "Insufficient credits, please add more")

              @patch('your_module.client.chat.completions.create', side_effect=APIError("API error"))
              @patch('your_module.time.sleep')
              def test_call_openai_api_retry_and_raise(self, mock_sleep, mock_create):
                  payload = {"model": "gpt-3.5-turbo", "messages": []}
                  current_user = MagicMock(credits=10)

                  with self.assertRaises(APIError) as cm:
                      call_openai_api(payload, current_user)

                  self.assertEqual(str(cm.exception), "API error")
                  self.assertEqual(mock_create.call_count, 12)  # Retry 12 times
                  self.assertEqual(mock_sleep.call_count, 11) 



def generate_new_agent(agent_name, jobtitle, agent_description, current_user):
    # Generate unique_id and timestamp
    unique_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    email = f"{agent_name.lower()}@{os.environ['DOMAIN_NAME']}"

    new_agent_data = generate_new_agent_data(agent_name, jobtitle, agent_description, current_user)

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

    new_agent_data = generate_profile_picture(new_agent_data, current_user)
    add_new_agent_to_user(new_agent_data, current_user)

    return new_agent_data


class TestGenerateNewAgent(unittest.TestCase):
    @patch('your_module.generate_new_agent_data')
    @patch('your_module.generate_profile_picture')
    @patch('your_module.add_new_agent_to_user')
    def test_generate_new_agent(self, mock_add_new_agent_to_user, mock_generate_profile_picture, mock_generate_new_agent_data):
        agent_name = "John Doe"
        jobtitle = "Software Engineer"
        agent_description = "A skilled software engineer"
        current_user = MagicMock()
        mock_generate_new_agent_data.return_value = {"name": "John Doe", "job": "Software Engineer"}
        mock_generate_profile_picture.return_value = {"name": "John Doe", "job": "Software Engineer", "photo_path": "/images/john_doe.png"}

        with patch.dict(os.environ, {'DOMAIN_NAME': 'example.com'}):
            result = generate_new_agent(agent_name, jobtitle, agent_description, current_user)

        mock_generate_new_agent_data.assert_called_once_with(agent_name, jobtitle, agent_description, current_user)
        mock_generate_profile_picture.assert_called_once_with({"id": "John Doe", "email": "john_doe@example.com", "unique_id": result['unique_id'], "timestamp": result['timestamp'], "jobtitle": "Software Engineer", "model": "gpt-3.5-turbo", "shortcode_superpower": "", "include": True, "name": "John Doe", "job": "Software Engineer"}, current_user)
        mock_add_new_agent_to_user.assert_called_once_with({"id": "John Doe", "email": "john_doe@example.com", "unique_id": result['unique_id'], "timestamp": result['timestamp'], "jobtitle": "Software Engineer", "model": "gpt-3.5-turbo", "shortcode_superpower": "", "include": True, "name": "John Doe", "job": "Software Engineer", "photo_path": "/images/john_doe.png"}, current_user)
        self.assertEqual(result, {"id": "John Doe", "email": "john_doe@example.com", "unique_id": result['unique_id'], "timestamp": result['timestamp'], "jobtitle": "Software Engineer", "model": "gpt-3.5-turbo", "shortcode_superpower": "", "include": True, "name": "John Doe", "job": "Software Engineer", "photo_path": "/images/john_doe.png"})

def generate_new_agent_data(agent_name, jobtitle, agent_description, current_user):
    agent_payload = {
        "model": "gpt-4-turbo-preview",
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": f"You are a helpful assistant designed to generate a new agent data in JSON format based on the following instructions:\n{json.load(open('abe/abe-instructions.json'))['new_agent_json_instructions']} /n /n Relationships must be a list of dictionaries, each representing a unique relationship with detailed attributes (name, job, relationship_description, summary, common_interactions)"
            },
            {
                "role": "user",
                "content": f"Agent Name: {agent_name}\nJob Title: {jobtitle}\nAgent Description: {agent_description}\n\nPlease generate the new agent data in JSON format without including the id, jobtitle, email, unique_id, timestamp, or photo_path fields."
            }
        ]
    }

    response = call_openai_api(agent_payload, current_user, credits_required=5)

    if response.choices[0].finish_reason == "stop":
        new_agent_data = json.loads(response.choices[0].message.content)
    else:
        raise ValueError(f"Incomplete or invalid JSON response: {response.choices[0].message.content}")

    return new_agent_data

class TestGenerateNewAgentData(unittest.TestCase):
    @patch('your_module.call_openai_api')
    def test_generate_new_agent_data_success(self, mock_call_openai_api):
        agent_name = "John Doe"
        jobtitle = "Software Engineer"
        agent_description = "A skilled software engineer"
        current_user = MagicMock()
        mock_response = MagicMock(choices=[MagicMock(finish_reason="stop", message=MagicMock(content='{"name": "John Doe", "job": "Software Engineer"}'))])
        mock_call_openai_api.return_value = mock_response

        result = generate_new_agent_data(agent_name, jobtitle, agent_description, current_user)

        expected_payload = {
            "model": "gpt-4-turbo-preview",
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a helpful assistant designed to generate a new agent data in JSON format based on the following instructions:\n{json.load(open('abe/abe-instructions.json'))['new_agent_json_instructions']} /n /n Relationships must be a list of dictionaries, each representing a unique relationship with detailed attributes (name, job, relationship_description, summary, common_interactions)"
                },
                {
                    "role": "user",
                    "content": f"Agent Name: John Doe\nJob Title: Software Engineer\nAgent Description: A skilled software engineer\n\nPlease generate the new agent data in JSON format without including the id, jobtitle, email, unique_id, timestamp, or photo_path fields."
                }
            ]
        }
        mock_call_openai_api.assert_called_once_with(expected_payload, current_user, credits_required=5)
        self.assertEqual(result, {"name": "John Doe", "job": "Software Engineer"})

    @patch('your_module.call_openai_api')
    def test_generate_new_agent_data_invalid_response(self, mock_call_openai_api):
        agent_name = "John Doe"
        jobtitle = "Software Engineer"
        agent_description = "A skilled software engineer"
        current_user = MagicMock()
        mock_response = MagicMock(choices=[MagicMock(finish_reason="length", message=MagicMock(content='Incomplete JSON'))])
        mock_call_openai_api.return_value = mock_response

        with self.assertRaises(ValueError) as cm:
            generate_new_agent_data(agent_name, jobtitle, agent_description, current_user)

        self.assertEqual(str(cm.exception), "Incomplete or invalid JSON response: Incomplete JSON")

def generate_profile_picture(new_agent_data, current_user):
    image_prompt = new_agent_data.get('image_prompt', '')
    dalle_prompt = f"{image_prompt[:3000]}"

    dalle_response = call_dalle_api(dalle_prompt, current_user)

    image_url = dalle_response.data[0].url
    logging.info(f"Generated image URL: {image_url[:142]}")

    new_photo_filename = f"{new_agent_data['id']}.png"
    logging.info(f"New photo filename: {new_photo_filename[:142]}")

    img_data = requests.get(image_url).content
    encoded_string = base64.b64encode(img_data).decode('utf-8')
    current_user.images_data[new_photo_filename] = encoded_string
    db.session.commit()

    thumbnail_encoded_string = generate_thumbnail(img_data)
    current_user.thumbnail_images_data[new_photo_filename] = thumbnail_encoded_string
    db.session.commit()

    new_agent_data['photo_path'] = f"/images/{new_photo_filename}"
    logging.info(f"Updated photo path: {new_agent_data['photo_path']}")

    return new_agent_data


class TestGenerateProfilePicture(unittest.TestCase):
    @patch('your_module.call_dalle_api')
    @patch('your_module.requests.get')
    def test_generate_profile_picture_success(self, mock_requests_get, mock_call_dalle_api):
        new_agent_data = {"id": "John Doe", "image_prompt": "A photo of John Doe"}
        current_user = MagicMock(images_data={}, thumbnail_images_data={})
        mock_dalle_response = MagicMock(data=[MagicMock(url="https://example.com/image.png")])
        mock_call_dalle_api.return_value = mock_dalle_response
        mock_requests_get.return_value = MagicMock(content=b"image_data")

        with self.assertLogs(level=logging.INFO) as log:
            result = generate_profile_picture(new_agent_data, current_user)

        mock_call_dalle_api.assert_called_once_with("A photo of John Doe", current_user)
        mock_requests_get.assert_called_once_with("https://example.com/image.png")
        self.assertIn(("INFO:root:Generated image URL: https://example.com/image.png",), log.output)
        self.assertIn(("INFO:root:New photo filename: John Doe.png",), log.output)
        self.assertIn(("INFO:root:Updated photo path: /images/John Doe.png",), log.output)
        self.assertEqual(current_user.images_data, {"John Doe.png": "aW1hZ2VfZGF0YQ=="})
        self.assertEqual(current_user.thumbnail_images_data, {"John Doe.png": "dGh1bWJuYWlsX2RhdGE="})
        self.assertEqual(result, {"id": "John Doe", "image_prompt": "A photo of John Doe", "photo_path": "/images/John Doe.png"})

def generate_thumbnail(img_data):
    thumbnail_size = (200, 200)
    img = Image.open(BytesIO(img_data))
    img.thumbnail(thumbnail_size)
    thumbnail_buffer = BytesIO()
    img.save(thumbnail_buffer, format='PNG')
    thumbnail_data = thumbnail_buffer.getvalue()
    thumbnail_encoded_string = base64.b64encode(thumbnail_data).decode('utf-8')
    return thumbnail_encoded_string


class TestGenerateThumbnail(unittest.TestCase):
    def test_generate_thumbnail(self):
        img_data = b"image_data"

        with patch('your_module.Image.open') as mock_image_open, \
             patch('your_module.BytesIO') as mock_bytesio:
            mock_image = MagicMock()
            mock_image_open.return_value = mock_image
            mock_thumbnail_buffer = MagicMock()
            mock_bytesio.return_value = mock_thumbnail_buffer
            mock_thumbnail_data = b"thumbnail_data"
            mock_thumbnail_buffer.getvalue.return_value = mock_thumbnail_data

            result = generate_thumbnail(img_data)

        mock_image_open.assert_called_once_with(mock_bytesio(img_data))
        mock_image.thumbnail.assert_called_once_with((200, 200))
        mock_image.save.assert_called_once_with(mock_thumbnail_buffer, format='PNG')
        self.assertEqual(result, "dGh1bWJuYWlsX2RhdGE=")

def add_new_agent_to_user(new_agent_data, current_user):
    if current_user.agents_data is None:
        current_user.agents_data = []

    current_user.agents_data.append(new_agent_data)
    db.session.commit()


class TestAddNewAgentToUser(unittest.TestCase):
    def test_add_new_agent_to_user_existing_agents_data(self):
        new_agent_data = {"id": "John Doe"}
        current_user = MagicMock(agents_data=[{"id": "Jane Doe"}])

        add_new_agent_to_user(new_agent_data, current_user)

        self.assertEqual(current_user.agents_data, [{"id": "Jane Doe"}, {"id": "John Doe"}])
        current_user.db.session.commit.assert_called_once()

    def test_add_new_agent_to_user_no_existing_agents_data(self):
        new_agent_data = {"id": "John Doe"}
        current_user = MagicMock(agents_data=None)

        add_new_agent_to_user(new_agent_data, current_user)

        self.assertEqual(current_user.agents_data, [{"id": "John Doe"}])
        current_user.db.session.commit.assert_called_once()

def call_openai_api(payload, current_user, credits_required):
    max_retries = 12
    retry_delay = 5
    retry_count = 0
    while retry_count < max_retries:
        try:
            if current_user.credits is None or current_user.credits < credits_required:
                raise Exception("Insufficient credits, please add more")

            response = client.chat.completions.create(**payload)

            current_user.credits -= credits_required
            db.session.commit()
            return response
        except APIError as e:
            logging.error(f"OpenAI API error: {e}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise e


class TestCallOpenAIAPI(unittest.TestCase):
    @patch('your_module.client.chat.completions.create')
    def test_call_openai_api_success(self, mock_create):
        payload = {"model": "gpt-4-turbo-preview", "messages": []}
        current_user = MagicMock(credits=10)
        mock_response = MagicMock()
        mock_create.return_value = mock_response

        result = call_openai_api(payload, current_user, credits_required=5)

        mock_create.assert_called_once_with(**payload)
        self.assertEqual(current_user.credits, 5)
        current_user.db.session.commit.assert_called_once()
        self.assertEqual(result, mock_response)

    def test_call_openai_api_insufficient_credits(self):
        payload = {"model": "gpt-4-turbo-preview", "messages": []}
        current_user = MagicMock(credits=2)

        with self.assertRaises(Exception) as cm:
            call_openai_api(payload, current_user, credits_required=5)

        self.assertEqual(str(cm.exception), "Insufficient credits, please add more")

    @patch('your_module.client.chat.completions.create', side_effect=APIError("API error"))
    @patch('your_module.time.sleep')
    def test_call_openai_api_retry_and_raise(self, mock_sleep, mock_create):
        payload = {"model": "gpt-4-turbo-preview", "messages": []}
        current_user = MagicMock(credits=10)

        with self.assertRaises(APIError) as cm, self.assertLogs(level=logging.ERROR) as log:
            call_openai_api(payload, current_user, credits_required=5)

        self.assertEqual(str(cm.exception), "API error")
        self.assertEqual(mock_create.call_count, 12)  # Retry 12 times
        self.assertEqual(mock_sleep.call_count, 11)  # Sleep 11 times between retries
        self.assertIn(("ERROR:root:OpenAI API error: API error",), log.output)


def call_dalle_api(dalle_prompt, current_user):
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
            return dalle_response
        except APIError as e:
            logging.error(f"OpenAI API error: {e}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise e

class TestCallDALLEAPI(unittest.TestCase):
    @patch('your_module.client.images.generate')
    def test_call_dalle_api_success(self, mock_generate):
        dalle_prompt = "A photo of John Doe"
        current_user = MagicMock(credits=20)
        mock_response = MagicMock()
        mock_generate.return_value = mock_response

        result = call_dalle_api(dalle_prompt, current_user)

        mock_generate.assert_called_once_with(model="dall-e-3", prompt=dalle_prompt, quality="standard", size="1024x1024", n=1)
        self.assertEqual(current_user.credits, 10)
        current_user.db.session.commit.assert_called_once()
        self.assertEqual(result, mock_response)

    def test_call_dalle_api_insufficient_credits(self):
        dalle_prompt = "A photo of John Doe"
        current_user = MagicMock(credits=5)

        with self.assertRaises(Exception) as cm:
            call_dalle_api(dalle_prompt, current_user)

        self.assertEqual(str(cm.exception), "Insufficient credits, please add more")

    @patch('your_module.client.images.generate', side_effect=APIError("API error"))
    @patch('your_module.time.sleep')
    def test_call_dalle_api_retry_and_raise(self, mock_sleep, mock_generate):
        dalle_prompt = "A photo of John Doe"
        current_user = MagicMock(credits=20)

        with self.assertRaises(APIError) as cm, self.assertLogs(level=logging.ERROR) as log:
            call_dalle_api(dalle_prompt, current_user)

        self.assertEqual(str(cm.exception), "API error")
        self.assertEqual(mock_generate.call_count, 12)  # Retry 12 times
        self.assertEqual(mock_sleep.call_count, 11)  # Sleep 11 times between retries
        self.assertIn(("ERROR:root:OpenAI API error: API error",), log.output)
