import requests

import json
import os
import openai
import re
import argparse

openai.api_key = os.getenv("OPENAI_API_KEY")
company_name = os.environ['COMPANY_NAME']

current_script_directory = os.path.dirname(os.path.realpath(__file__))

agents_json_path = os.path.join(current_script_directory, '..', 'agents',
                                'agents.json')

content_json_path = os.path.join(current_script_directory, '..', 'static',
                                 'content.json')

image_static_path = os.path.join(current_script_directory, '..', 'static',
                                 'atat.png')


def generate_company_description():
  with open(agents_json_path, "r") as file:
    agents = json.load(file)
  prompts = [agent["image_prompt"] for agent in agents]
  combined_prompts = " ".join(prompts)

  response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[{
          "role": "system",
          "content": "You are a knowledgeable assistant."
      }, {
          "role":
          "user",
          "content":
          f"Provide a one-paragraph description of the company and industry based on the following agent descriptions: {combined_prompts}"
      }],
      temperature=0.7,
      max_tokens=1024)
  return response.choices[-1].message['content'].strip()


def generate_web_copy(company_info):
  response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[{
          "role": "system",
          "content": "You are a knowledgeable assistant."
      }, {
          "role":
          "user",
          "content":
          f"Write an introduction for a website representing a team of AI agents working in {company_info}. THREE SENTENCES MAX. CONVINCE THE USER TO ENGAGE THE AGENTS BASED ON THE VALUE PROPOSITIONS. IT'S WEB COPY."
      }],
      temperature=0.7,
      max_tokens=512)
  return response.choices[-1].message['content'].strip()


def generate_new_header_image(description):
  response = openai.Image.create(
      model="dall-e-3",
      prompt=f"Create a header image for a website about {description}.",
      n=1,
      size="1024x1024")
  image_data = response.data[0]["url"]

  image_path = image_static_path
  download_and_save_image(image_data, image_path)
  return image_path


def download_and_save_image(url, path):
  response = requests.get(url)
  if response.status_code == 200:
    with open(path, 'wb') as file:
      file.write(response.content)


def update_website_meta(title, h1, h2, footer, meta_details, social_image_url,
                        logo_url):
  header_info = {
      "title": title,
      "h1": h1,
      "h2": h2,
      "footer": footer,
      "meta": meta_details,
      "social_image_url": social_image_url,
      "logo_url": logo_url
  }
  with open(content_json_path, "w") as file:
    json.dump(header_info, file, indent=4)


def update_website_meta(data):
  with open(content_json_path, "w") as file:
    json.dump(data, file, indent=4)


def generate_headers_with_gpt4(description, company_name):
  messages = [{
      "role":
      "system",
      "content":
      "You are a highly skilled copywriter and web developer. Generate web content including title, H1, H2, footer, open graph title (ogTitle), open graph description (ogDescription), Twitter title, Twitter description, and web copy. web_copy is marketing copy one paragraph max. Explain that people can email all of these AI agents in the web_copy. Format your response as JSON. The structure must be exactly {'title': '', 'h1': '', 'h2': '', 'footer': '', 'ogTitle': '', 'ogDescription': '', 'twitterTitle': '', 'twitterDescription': '', 'meta': {}, 'social_image_url': '', 'logo_url': '', 'web_copy': ''}"
  }, {
      "role":
      "user",
      "content":
      f"Create web content for {company_name}, a company that specializes in {description}."
  }]

  response = openai.ChatCompletion.create(model="gpt-4-1106-preview",
                                          messages=messages,
                                          temperature=0.7,
                                          max_tokens=1000,
                                          top_p=1.0,
                                          frequency_penalty=0,
                                          presence_penalty=0)

  try:

    match = re.search(r'\{.*\}', response.choices[-1].message['content'],
                      re.DOTALL)
    if match:
      json_str = match.group(0)
      content_json = json.loads(json_str)
      print("Extracted JSON:", json_str)
      return content_json
    else:
      print("No JSON found in the response.")
      return None
  except (json.JSONDecodeError, KeyError) as e:
    print(f"Failed to extract and decode JSON. Error: {e}. Returning None.")
    return None


def main(social_image_url="default_social_image_url",
         logo_url="default_logo_url"):
  description = generate_company_description()
  header_image_path = generate_new_header_image(description)
  web_copy = generate_web_copy(description)

  content_json = generate_headers_with_gpt4(description, company_name)
  if content_json is None:
    print("Error: Failed to generate header content with GPT-4.")
    return

  if content_json is None:
    content_json = {}

  metadata = {
      "header_image": header_image_path,
      "web_copy": web_copy,
      "social_image_url": social_image_url,
      "logo_url": logo_url
  }

  merged_content = {**content_json, **metadata}
  update_website_meta(merged_content)
  print("Website content and metadata updated successfully.")


if __name__ == "__main__":

  parser = argparse.ArgumentParser(
      description='Update website content and metadata.')
  parser.add_argument('--social_image_url',
                      type=str,
                      default="default_social_image_url")
  parser.add_argument('--logo_url', type=str, default="default_logo_url")
  args = parser.parse_args()

  main(args.social_image_url, args.logo_url)
