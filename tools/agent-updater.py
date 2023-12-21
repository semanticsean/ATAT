import json
import os
import openai
import requests
import uuid
from datetime import datetime


def initialize_api():
  openai.api_key = os.getenv('OPENAI_API_KEY')


def read_agents(file_path):
  with open(file_path, 'r') as file:
    agents = json.load(file)
  return agents


def save_agents(agents, file_path):
  with open(file_path, 'w') as file:
    json.dump(agents, file, indent=4)


def generate_text_with_gpt(persona_description, retry_count=6):
  for attempt in range(retry_count):
    try:
      messages = [{
          "role":
          "system",
          "content":
          "You are a helpful assistant making instructions for llm-based AI agents that are extremely clear and always consistently formatted. Your dall-e instructions are part of a consistent brand identity for an AI agent startup based in LA using rich storytelling techniques to build amazing agents. You do great work on instruction design for hybrid multi-agent models."
      }, {
          "role":
          "user",
          "content":
          f"This AI agent's persona is described as: '{persona_description}'. Please generate a 'summary' that is exactly one information dense sentence long, 6 'keywords', and a 6-8 sentence DALL-E image-prompt that adheres to the detailed instructions for a polished and approachable headshot. The instructions need to be indicative of the persona - be creative and very detailed with story / character clues through artifacts and context in the background. Your response must be in valid JSON and the JSON must include these fields in this format of response exactly ''summary':'...','keywords':'...','image-prompt':'...'' which will be extracted from your answer."
      }]
      response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
      return response
    except json.JSONDecodeError:
      if attempt < retry_count - 1:
        print(f"Retrying gpt-4 request for agent: {attempt + 1}/{retry_count}")
      else:
        print(
            f"Failed after {retry_count} attempts for agent. Skipping agent.")
        return None


def generate_image_with_dalle(prompt):
  response = openai.Image.create(model="dall-e-3",
                                 prompt=prompt,
                                 n=1,
                                 size="1024x1024",
                                 quality="standard")
  return response


def download_and_save_image(url, path):
  response = requests.get(url)
  if response.status_code == 200:
    with open(path, 'wb') as file:
      file.write(response.content)


def ensure_dir_exists(path):
  if not os.path.exists(path):
    os.makedirs(path)


def image_exists(path):
  """Check if an image file exists at the given path."""
  return os.path.isfile(path)


def process_agents():
  agents_file_path = '../agents/agents.json'
  agents = read_agents(agents_file_path)
  ensure_dir_exists('pics')

  for agent in agents:
    if 'summary' not in agent or 'keywords' not in agent or 'image_prompt' not in agent or (
        'photo_path' in agent and not image_exists(agent['photo_path'])):
      if not agent.get('unique_id'):
        agent['unique_id'] = str(uuid.uuid4())
        agent['timestamp'] = datetime.now().isoformat()

      persona_description = agent.get('persona', '')
      text_response = generate_text_with_gpt(persona_description)

      if text_response:
        try:
          structured_data = json.loads(
              text_response['choices'][0]['message']['content'])
          agent.update({
              'summary': structured_data.get('summary', ''),
              'keywords': structured_data.get('keywords', []),
              'image_prompt': structured_data.get('image-prompt', '')
          })
          save_agents(agents, agents_file_path)
        except json.JSONDecodeError:
          print(
              f"Failed to interpret gpt-4 response as JSON for agent: {agent['id']}"
          )
          continue

      name = agent.get('name', 'Unnamed Agent')
      job_title = agent.get('job_title', 'Unknown Job Title')
      summary = agent.get('summary', '')
      custom_image_prompt = agent.get('image_prompt', '')

      detailed_prompt = f"Create a headshot portraying an AI role-playing a human character named '{name}', who is imagined in the role of '{job_title}'. They can be described as '{custom_image_prompt}'. [Detailed instructions here]"

      image_response = generate_image_with_dalle(detailed_prompt)
      if image_response:
        image_url = image_response['data'][0]['url']
        image_path = f"pics/{agent['unique_id']}.png"
        download_and_save_image(image_url, image_path)
        agent['photo_path'] = image_path
        save_agents(agents, agents_file_path)
      else:
        print(f"Failed to generate DALL-E image for agent: {agent['id']}")
        continue

  save_agents(agents, agents_file_path)


if __name__ == "__main__":
  initialize_api()
  process_agents()
