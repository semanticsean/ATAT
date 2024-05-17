#render_agents.py 
import os
import datetime
import glob
import json
import random
import string
import uuid
import sys
import argparse
import shutil
from openai import OpenAI

from update_team import create_new_agent_files

client = OpenAI()
import requests


domain_name = os.environ.get('DOMAIN_NAME', 'semantic-life.com')
company_name = os.environ.get('COMPANY_NAME', 'Semantic Life')


def clear_agents_json():
  print("Clearing agents.json content...")
  json_path = os.path.join('agents', 'agents.json')
  with open(json_path, "w") as file:
    json.dump([], file)
  print("agents.json cleared.")


def clear_pics_directory():
  print("Clearing pictures directory...")
  pics_path = os.path.join('agents', 'pics')
  if not os.path.exists(pics_path):
    os.makedirs(pics_path)
  else:
    for filename in os.listdir(pics_path):
      file_path = os.path.join(pics_path, filename)
      try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
          os.unlink(file_path)
        elif os.path.isdir(file_path):
          shutil.rmtree(file_path)
        print(f"Deleted {file_path}")
      except Exception as e:
        print(f"Failed to delete {file_path}. Reason: {e}")
  print("Pictures directory cleared.")


def log_to_file(message):
  log_file = "api_log.txt"
  with open(log_file, "a") as file:
    file.write(f"{datetime.datetime.now().isoformat()}: {message}\n")


def read_description(file_path):
  print(f"Reading description from {file_path}...")
  with open(file_path, 'r') as file:
    lines = file.readlines()
    agent_name = lines[0].strip() if lines else ''.join(
        random.choices(string.ascii_letters + string.digits, k=16))
    description = ' '.join(lines[1:]).strip() if len(lines) > 1 else ''
    return agent_name, description


def agent_exists(agent_name, agents_file=None):
  if agents_file is None:
    agents_file = os.path.join('agents', 'agents.json')
  try:
    with open(agents_file, "r") as file:
      agents = json.load(file)
    for agent in agents:
      if agent["id"] == agent_name:
        return True
    return False
  except FileNotFoundError:
    print(f"File not found: {agents_file}")
    return False
  except json.JSONDecodeError:
    print(f"Failed to decode JSON from {agents_file}")
    return False


def generate_image_with_dalle(prompt):
  print(f"Generating image with prompt: {prompt[:20]}")
  """Generates an image using DALL-E with additional hardcoded instructions and returns the response."""

  # Hardcoded instructions
  instructions = "Create a highly detailed, vivid, and somewhat imaginative image as a work headshot(s) for the AI agent. Make the backdrop indicative of their work. Make sure the face is the foreground center looking at the camera. THEY SHOULD BE FRIENDLY UNLESS THEIR PERSONA EXPLICITLY SAYS THEY ARE NOT FRIENDLY. If the user specifies something different than a headshot, do that; otherwise, headshots."

  # Combine the base prompt with the hardcoded instructions
  full_prompt = f"{prompt}. {instructions}"

  # Call the DALL-E API with the combined prompt
  response = client.images.generate(model="dall-e-3",
                                 prompt=full_prompt,
                                 n=1,
                                 size="1024x1024",
                                 quality="standard")
  return response


def download_and_save_image(url, path):
  """Downloads and saves an image from a URL."""
  # Ensure the directory exists
  os.makedirs(os.path.dirname(path), exist_ok=True)

  response = requests.get(url)
  if response.status_code == 200:
    with open(path, 'wb') as file:
      file.write(response.content)


def generate_persona(agent_name,
                     description,
                     version="A",
                     max_tokens=3000,
                     temperature=0.7,
                     top_p=0.5):
  print(f"Generating persona for {agent_name} with version {version}")
  if version == "B":
    prompt_message = {
        "role":
        "system",
        "content":
        "Generate a detailed narrative description of a persona based on this information, including the agent's name ("
        + agent_name +
        ") in the image_prompt. Generate a detailed narrative description of a persona based on this information and convert it into JSON format with these fields: persona, summary, keywords, and image_prompt. Each is a single field, and only keywords is a dictionary, the rest are single text block answers in the value. so it's exactly like this: 'persona':'','summary':'',,'jobtitle':'','keywords':['keyword1','keyword2','keyword3','keyword4','keyword5','keyword6'],'relationships':['familyrelationship1','familyrelationship2','familyrelationship3','familyrelationship4','keyword5','keyword6'],'image_prompt':'' -- it is critical that the JSON be exactly like that. An important consideration is that the keyword dictionary is JUST the keywords and not using any labels / keys for the values within the dictionary. CHANGE THE NAME OF THE AGENT; CHANGE THE DETAILS SO THEY ARE DIFFERENT BUT VERY SIMILAR. For relationships, each entry should be a unique relationship that heavily influences this agent. When generating the keywords and relationships for each agent, ensure the output adheres to the following structures to maintain consistency across all agent profiles:Keywords: Must be provided as a list of strings. Each string represents a keyword related to the agent's skills, expertise, or attributes. Do not use a dictionary or any key-value pairs for keywords. For example, the keywords should be formatted as ['Keyword1', 'Keyword2', 'Keyword3', ...].Relationships: Should be formatted as a list of dictionaries. Each dictionary within the list represents a distinct relationship, detailing the name, job, relationship description, and a summary of normal interactions between the agent and the relationship. Ensure each relationship is a separate dictionary within the list, rather than combining them into a single dictionary with key-value pairs. For instance, relationships should look like [{ 'name': 'PersonA', 'job': 'JobTitle', 'relationship_description': 'Description', 'summary': 'Interaction Summary' }, { 'name': 'PersonB', ...}]. Each relationships needs a name, job, relationship description, and summary of normal interactions between the main agent and that relationships with a list of common interactions with context setting and discsussion topics for each agent, short and concise. For details, persona should include this stuff: 'Job Title working for {company_name} {domain_name}, Field of Expertise, THEORY OF MIND, ACTION TENDENCY MECHANISM, SOCIAL IMPORTANCE DYNAMICS, MODEL OF GOALS, MODEL OF DESIRES, MODEL OF AGENDAS, MODEL OF THOUGHT COMPLEXITY, MODEL OF CURIOSITY, MODEL OF INTERNAL FAMILY SYSTEMS OF UNNAMED BUT RECOGNIZED INFLUENCES, General Character Disposition, Primary Company Name, Position in the Company, Company's Work, Associated Company Name, Relation to Primary Company, Associated Company's Work, Products and/or Services Offered, Emotional Processing, Memory Processing, Decision-making Mechanism, Social Interaction Understanding, Anticipating Others' Behavior, Action Guidance, Symbolic or Representational Stories or Experiences, Future Vision and Philosophical Stance, Important Collaborative Relationships, Primary Aims and Targets' and Summary should be a one sentence version of this. image_prompt is descriptions for dalle and should emphasize character details as well as backgrounds and contexts that provide many clues about the agent. PERSONA SHOULD BE VERY VERBOSE. Note: All agents work at {company_name}."
    }
  else:
    prompt_message = {
        "role":
        "system",
        "content":
        "Generate a detailed narrative description of a persona based on this information, including the agent's name ("
        + agent_name +
        ") in the image_prompt. Generate a detailed narrative description of a persona based on this information and convert it into JSON format with these fields: persona, summary, keywords, and image_prompt. Each is a single field, and only keywords is a dictionary, the rest are single text block answers in the value. so it's exactly like this: 'persona':'','summary':'',,'jobtitle':'','keywords':['keyword1','keyword2','keyword3','keyword4','keyword5','keyword6'],'relationships':['familyrelationship1','familyrelationship2','familyrelationship3','familyrelationship4','keyword5','keyword6'],'image_prompt':'' -- it is critical that the JSON be exactly like that. An important consideration is that the keyword dictionary is JUST the keywords and not using any labels / keys for the values within the dictionary. For relationships, each entry should be a unique relationship that heavily influences this agent. Each relationships needs a name, job, relationship description, and summary of normal interactions between the main agent and that relationships with a list of common interactions with context setting and discsussion topics for each agent, short and concise. When generating the keywords and relationships for each agent, ensure the output adheres to the following structures to maintain consistency across all agent profiles:Keywords: Must be provided as a list of strings. Each string represents a keyword related to the agent's skills, expertise, or attributes. Do not use a dictionary or any key-value pairs for keywords. For example, the keywords should be formatted as ['Keyword1', 'Keyword2', 'Keyword3', ...].Relationships: Should be formatted as a list of dictionaries. Each dictionary within the list represents a distinct relationship, detailing the name, job, relationship description, and a summary of normal interactions between the agent and the relationship. Ensure each relationship is a separate dictionary within the list, rather than combining them into a single dictionary with key-value pairs. For instance, relationships should look like [{ 'name': 'PersonA', 'job': 'JobTitle', 'relationship_description': 'Description', 'summary': 'Interaction Summary' }, { 'name': 'PersonB', ...}]. For details, persona should include this stuff: 'Job Title working for {company_name} {domain_name}, Field of Expertise, THEORY OF MIND, ACTION TENDENCY MECHANISM, SOCIAL IMPORTANCE DYNAMICS, MODEL OF GOALS, MODEL OF DESIRES, MODEL OF AGENDAS, MODEL OF THOUGHT COMPLEXITY, MODEL OF CURIOSITY, MODEL OF INTERNAL FAMILY SYSTEMS OF UNNAMED BUT RECOGNIZED INFLUENCES, General Character Disposition, Primary Company Name, Position in the Company, Company's Work, Associated Company Name, Relation to Primary Company, Associated Company's Work, Products and/or Services Offered, Emotional Processing, Memory Processing, Decision-making Mechanism, Social Interaction Understanding, Anticipating Others' Behavior, Action Guidance, Symbolic or Representational Stories or Experiences, Future Vision and Philosophical Stance, Important Collaborative Relationships, Primary Aims and Targets' and Summary should be a one sentence version of this. image_prompt is descriptions for dalle and should emphasize character details as well as backgrounds and contexts that provide many clues about the agent. PERSONA SHOULD BE VERY VERBOSE. Note: All agents work at {company_name}."
    }

  narrative_prompt = {"role": "user", "content": description}

  response = client.chat.completions.create(model="gpt-4-1106-preview",
  messages=[prompt_message, narrative_prompt],
  max_tokens=max_tokens,
  temperature=temperature,
  top_p=top_p,
  response_format={"type": "json_object"})

  return response.choices[0].message.content.strip()


def add_new_agent(agent_name, description, version="A"):
  print(f"Starting to add a new agent: {agent_name} with version {version}")
  new_persona_json = generate_persona(agent_name, description, version)
  print(f"Generated persona JSON for {agent_name}: {new_persona_json}")

  try:
    new_persona = json.loads(new_persona_json)
    email = agent_name.replace(" ", "").lower() + f"@{domain_name}"
    timestamp = datetime.datetime.now().isoformat()

    print(f"Creating new agent object for {agent_name}")
    new_agent = {
        "id": agent_name,
        "email": email,
        "persona": new_persona.get('persona', ''),
        "unique_id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "summary": new_persona.get('summary', ''),
        "jobtitle": new_persona.get('jobtitle', ''),
        "keywords": new_persona.get('keywords', []),
        "relationships": new_persona.get('relationships', []),
        "image_prompt": new_persona.get('image_prompt', ''),
        "photo_path": ""
    }

    # Generate and save image
    image_prompt = new_agent['image_prompt']
    if image_prompt:
      print(
          f"Generating image for {agent_name} with prompt: {image_prompt[:20]}"
      )
      image_response = generate_image_with_dalle(image_prompt)
      if image_response:
        image_url = image_response.data[0].url 
        image_path = os.path.join('agents', 'pics',
                                  f"{new_agent['unique_id']}.png")

        print(f"Downloading image for {agent_name} from URL: {image_url[:20]}")
        download_and_save_image(image_url, image_path)
        new_agent['photo_path'] = image_path
        print(f"Image saved for {agent_name} at {image_path}")

    print(f"New agent added successfully: {agent_name}")
    return new_agent
  except json.JSONDecodeError as e:
    print(f"Failed to decode JSON for {agent_name}. Error: {e}")
    raise ValueError("Failed to decode JSON from LLM response.")

def parse_new_agent_files_content(args):
  new_agent_files_content = {}
  try:
      if args.new_agent_files:
          new_agent_files_content = json.loads(args.new_agent_files)
  except json.JSONDecodeError as e:
      print(f"Error parsing new agent files content: {e}")
  return new_agent_files_content


def parse_arguments():
  print("Parsing arguments...")
  parser = argparse.ArgumentParser(description='Process agents and options.')
  parser.add_argument('--version',
                      default='A',
                      choices=['A', 'B'],
                      help='Version A or B')
  parser.add_argument('--clear-json',
                      action='store_true',
                      help='Clear existing agents.json content')
  parser.add_argument('--clear-pics',
                      action='store_true',
                      help='Clear existing pics content')
  parser.add_argument('--new-agent-files',
                      type=str,
                      default='{}',
                      help='New agent files content')
  args = parser.parse_args()
  print(
      f"Arguments parsed. Version: {args.version}, Clear JSON: {args.clear_json}, Clear Pics: {args.clear_pics}"
  )
  return args

def process_agents(version, new_agent_files_content):
  print(f"Processing agent files with version {version}")
  print(f"New agent files content: {new_agent_files_content}")  # Add this line

  agents_file_path = os.path.join('agents', 'agents.json')
  print(f"agents.json path: {agents_file_path}")

  for file, content in new_agent_files_content.items():
      print(f"Processing file: {file}")  # Add this line
      agent_name, description = read_description_from_content(content)
      if not agent_exists(agent_name, agents_file_path):
          print(f"Adding new agent: {agent_name}")  # Add this line
          new_agent = add_new_agent(agent_name, description, version)
          append_agent_to_file(new_agent, agents_file_path)
          print(f"Appended new agent: {agent_name} to {agents_file_path}.")
      else:
          print(f"Agent {agent_name} already exists, skipping.")

  if not new_agent_files_content:
      print("No agent description files found.")

def append_agent_to_file(agent, file_path):
  """Appends a new agent to the existing list in the JSON file."""
  try:
    # Load the existing data
    if os.path.exists(file_path):
      with open(file_path, 'r') as file:
        agents = json.load(file)
    else:
      agents = []

    # Append the new agent
    agents.append(agent)

    # Save the updated list back to the file
    with open(file_path, 'w') as file:
      json.dump(agents, file, indent=4)

    print(f"Agent {agent['id']} successfully appended to {file_path}.")
  except Exception as e:
    print(f"Error appending agent to {file_path}: {e}")


def generate_cover_photo(transformation_prompt):
  print("Generating cover photo for the website...")
  cover_photo_instructions = "Create a captivating and professional cover photo for a website. Make it obviously illustrated, and for a TEAM of AI Agents here to help. "
  full_prompt = f"{transformation_prompt}. {cover_photo_instructions}"

  image_response = generate_image_with_dalle(full_prompt)
  if image_response:
    image_url = image_response.data[0].url 
    image_path = os.path.join('agents', 'pics', 'cover_photo.png')

    print(f"Downloading cover photo from URL: {image_url}")
    download_and_save_image(image_url, image_path)
    print(f"Cover photo saved at {image_path}")


if __name__ == "__main__":
  args = parse_arguments()

  try:
      with open('start-config.json', 'r') as config_file:
          config = json.load(config_file)
          transformation_prompt = config.get('cover_photo_instructions', '')
  except Exception as e:
      print(f"Failed to read start-config.json: {e}")
      transformation_prompt = ''

  if args.clear_json:
      clear_agents_json()
  if args.clear_pics:
      clear_pics_directory()

  # Generate the cover photo for the website
  if transformation_prompt:
      generate_cover_photo(transformation_prompt)

  print(f"Starting agent processing with version {args.version}, clear_json: {args.clear_json}, clear_pics: {args.clear_pics}")
  
  new_agent_files_content = parse_new_agent_files_content(args)
  process_agents(args.version, new_agent_files_content)
  
  print("Agent processing and cover photo generation completed.")