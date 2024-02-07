import os
import datetime
import glob
import json
import random
import string
import uuid

import openai
import requests

domain_name = os.environ.get('DOMAIN_NAME', 'semantic-life.com')
company_name = os.environ.get('COMPANY_NAME', 'Semantic Life')

## NOTE: WILL ONLY WORK IF OPENAI_API_KEY SET IN SECRETS


def log_to_file(message):
  log_file = "api_log.txt"
  with open(log_file, "a") as file:
    file.write(f"{datetime.datetime.now().isoformat()}: {message}\n")


def read_description(file_path):
  with open(file_path, 'r') as file:
    lines = file.readlines()
    agent_name = lines[0].strip() if lines else ''.join(
        random.choices(string.ascii_letters + string.digits, k=16))
    description = ' '.join(lines[1:]).strip() if len(lines) > 1 else ''
    return agent_name, description


def agent_exists(agent_name, agents_file="agents.json"):
  """Check if an agent with the given name already exists in the agents file."""
  try:
    with open(agents_file, "r") as file:
      agents = json.load(file)
    for agent in agents:
      if agent["id"] == agent_name:
        return True
    return False
  except FileNotFoundError:
    return False


def generate_image_with_dalle(prompt):
  """Generates an image using DALL-E with additional hardcoded instructions and returns the response."""

  # Hardcoded instructions
  instructions = "Create a highly detailed, vivid, and somewhat imaginative image as a work headshot for the AI agent. Make the backdrop indicative of their work. Make sure the face is the foreground center looking at the camera. THEY SHOULD BE FRIENDLY UNLESS THEIR PERSONA EXPLICITLY SAYS THEY ARE NOT FRIENDLY. Eyes should be humanoid. No robot parts. Realistic as though taken with a camera. No white android robots -- use humanoid expressions with a near-future vibe from the 2015 era. These are headshots for work and should feel professional, from a pre-AI-generated-art era."

  # Combine the base prompt with the hardcoded instructions
  full_prompt = f"{prompt}. {instructions}"

  # Call the DALL-E API with the combined prompt
  response = openai.Image.create(model="dall-e-3",
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
                     max_tokens=3000,
                     temperature=0.7,
                     top_p=0.5):
  prompt_message = {
      "role":
      "system",
      "content":
      "Generate a detailed narrative description of a persona based on this information, including the agent's name ("
      + agent_name +
      ") in the image_prompt. Generate a detailed narrative description of a persona based on this information and convert it into JSON format with these fields: persona, summary, keywords, and image_prompt. Each is a single field, and only keywords is a dictionary, the rest are single text block answers in the value. so it's exactly like this: 'persona':'','summary':'',,'jobtitle':'','keywords':['keyword1','keyword2','keyword3','keyword4','keyword5','keyword6'],'relationships':['familyrelationship1','familyrelationship2','familyrelationship3','familyrelationship4','keyword5','keyword6'],'image_prompt':'' -- it is critical that the JSON be exactly like that. An important consideration is that the keyword dictionary is JUST the keywords and not using any labels / keys for the values within the dictionary. For relationships, each entry should be a unique relationship that heavily influences this agent. Each relationships needs a name, job, relationship description, and summary of normal interactions between the main agent and that relationships with a list of common interactions with context setting and discsussion topics for each agent, short and concise. For details, persona should include this stuff: 'Job Title working for {company_name} {domain_name}, Field of Expertise, THEORY OF MIND, ACTION TENDENCY MECHANISM, SOCIAL IMPORTANCE DYNAMICS, MODEL OF GOALS, MODEL OF DESIRES, MODEL OF AGENDAS, MODEL OF THOUGHT COMPLEXITY, MODEL OF CURIOSITY, MODEL OF INTERNAL FAMILY SYSTEMS OF UNNAMED BUT RECOGNIZED INFLUENCES, General Character Disposition, Primary Company Name, Position in the Company, Company's Work, Associated Company Name, Relation to Primary Company, Associated Company's Work, Products and/or Services Offered, Emotional Processing, Memory Processing, Decision-making Mechanism, Social Interaction Understanding, Anticipating Others' Behavior, Action Guidance, Symbolic or Representational Stories or Experiences, Future Vision and Philosophical Stance, Important Collaborative Relationships, Primary Aims and Targets' and Summary should be a one sentence version of this. image_prompt is descriptions for dalle and should emphasize character details as well as backgrounds and contexts that provide many clues about the agent. PERSONA SHOULD BE VERY VERBOSE. Note: All agents work at {company_name}."
  }
  narrative_prompt = {"role": "user", "content": description}

  response = openai.ChatCompletion.create(
      model="gpt-4-1106-preview",
      messages=[prompt_message, narrative_prompt],
      max_tokens=max_tokens,
      temperature=temperature,
      top_p=top_p,
      response_format={"type": "json_object"})

  return response['choices'][0]['message']['content'].strip()


def add_new_agent(agent_name, description):
  """Adds a new agent and generates an image for them."""
  new_persona_json = generate_persona(agent_name, description)
  try:
    new_persona = json.loads(new_persona_json)
    email = agent_name.replace(" ", "").lower() + f"@{domain_name}"
    timestamp = datetime.datetime.now().isoformat()

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
      image_response = generate_image_with_dalle(image_prompt)
      if image_response:
        image_url = image_response['data'][0]['url']
        image_path = os.path.join(os.path.dirname(__file__), "pics",
                                  f"{new_agent['unique_id']}.png")
        download_and_save_image(image_url, image_path)
        new_agent['photo_path'] = image_path

    return new_agent
  except json.JSONDecodeError:
    raise ValueError("Failed to decode JSON from LLM response.")


def revise_agent_bio():
  print("Revising agent bios based on new instructions...")
  text_files = glob.glob('new_agent_files/*.txt')
  print(f"Found {len(text_files)} text files to process.")
  new_context = input(
      "Please enter the new context for the agents (e.g., 'works for an ad agency'): "
  )

  for text_file in text_files:
    print(f"Processing {text_file}...")
    agent_name, description = read_description(text_file)
    print(f"Original Description for {agent_name}: {description[:60]}..."
          )  # Print a portion of the original description for debugging
    revised_bio = change_context(description, new_context)
    print(f"Revised Description for {agent_name}: {revised_bio[:60]}..."
          )  # Print a portion of the revised bio for debugging
    if revised_bio != description:  # Check if the bio has been revised
      update_agent_bio(text_file, agent_name, revised_bio)
      print(f"Updated {text_file} with new context.")
    else:
      print(f"No changes made to {text_file}, skipping.")


def change_context(description, new_context):
  try:
    prompt = f"Rewrite the following bio with the context that this person now works for an ad agency named '{company_name}': {description}"
    print(f'prompt: {prompt[:42]}')

    # Initialize a chat session with gpt-3.5-turbo
    chat_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role":
            "system",
            "content":
            "You are a highly skilled AI trained to rewrite bios with new context."
        }, {
            "role": "user",
            "content": prompt
        }],
        temperature=0.7,
        max_tokens=300,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0)

    # Extract the revised description from the chat response
    revised_description = chat_response['choices'][0]['message'][
        'content'].strip()
    print(f'Revised Description: {revised_description[:42]}')
    return revised_description
  except Exception as e:
    print(f"An error occurred while trying to revise the bio: {e}")
    return description


def update_agent_bio(file_path, agent_name, revised_bio):
  with open(file_path, 'w') as file:
    file.write(f"{agent_name}\n{revised_bio}")


if __name__ == "__main__":
  choice = input(
      "Choose an action:\n1. Add / Refine Agents\n2. Revise Agent Bios\nEnter choice (1 or 2): "
  )
  if choice == '1':
    # Logic for adding new agents (not modified in this snippet)
    print("Add / Refine Agents option selected.")
  elif choice == '2':
    revise_agent_bio()
  else:
    print(
        "Invalid choice. Please run the script again and select either 1 or 2."
    )
