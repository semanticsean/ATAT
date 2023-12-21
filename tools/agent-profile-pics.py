import json
import openai
import os
import requests
import re


def load_personas(file_path):
  with open(file_path, 'r', encoding='utf-8') as file:
    return json.load(file)


def save_personas(personas, file_path):
  with open(file_path, 'w', encoding='utf-8') as file:
    json.dump(personas, file, indent=4, ensure_ascii=False)


def generate_image_description(persona):
  name = persona.get('name', 'Unknown Name')
  job_title = persona.get('job_title', 'Unknown Job Title')
  summary = persona.get('summary', 'No summary provided.')

  description = (
      f"Create a polished and approachable headshot of a single AI agent named '{name}', serving in the capacity of '{job_title}'. This AI agent is described as '{summary}'. The photograph should exude a warm, inviting atmosphere akin to the relaxed professionalism of California's business culture. The agent's attire should be tastefully formal, with a hint of laid-back confidence, suitable for an engaged parent advocate within a private school setting. Position the agent in an environment that suggests a high-end corporate space, yet with a touch of the personal, echoing the individual's connection to educational and leadership pursuits. The background should subtly reflect this setting, possibly hinting at an open, airy office with views of a natural landscape, to convey openness and a forward-thinking attitude. Lighting should be natural and bright, reminiscent of a sunny California day, which casts a gentle glow and creates a friendly and optimistic tone. The final image should be free of text and appear as a single, cohesive piece that could seamlessly fit into a corporate website or promotional material, emphasizing reliability and a proactive spirit. The faces should always be human-ish but in an illustrated / animated style, not realistic. Reminder: NEVER EVER GENERATE TEXT. IMAGES ONLY! thanks."
  )

  keywords = persona.get('keywords', [])
  if keywords:
    description += " Keywords: " + ", ".join(keywords)

  return description


def download_image(url, path):
  response = requests.get(url)
  if response.status_code == 200:
    with open(path, 'wb') as file:
      file.write(response.content)


def generate_dalle_image(prompt):
  print(f"Making DALL-E API call with prompt: {prompt}")
  response = openai.Image.create(model="dall-e-3",
                                 prompt=prompt,
                                 size="1024x1024",
                                 quality="hd",
                                 n=1)
  return response['data'][0]['url']


def sanitize_filename(name):
  """Sanitize the agent name to be used in a filename."""
  return re.sub(r'[^a-zA-Z0-9\-_]', '', name.replace(' ', '_'))


def update_personas_with_images(personas, image_folder):
  if not os.path.exists(image_folder):
    os.makedirs(image_folder)

  for persona in personas:
    prompt = generate_image_description(persona)
    image_url = generate_dalle_image(prompt)
    sanitized_name = sanitize_filename(persona['name'])
    image_filename = f"{sanitized_name}_{persona['unique_id']}.png"
    image_path = os.path.join(image_folder, image_filename)
    download_image(image_url, image_path)
    persona['photo_path'] = image_path
    print(f"Image filename: {image_filename}")


def main():
  api_key = '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'
  openai.api_key = api_key

  file_path = 'personas.json'
  image_folder = 'profile-pics'
  personas = load_personas(file_path)

  update_personas_with_images(personas, image_folder)

  save_personas(personas, file_path)


if __name__ == "__main__":
  main()
