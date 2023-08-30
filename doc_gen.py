import json
import os
import re
import time
from random import uniform

import openai

openai_api_key = os.environ['OPENAI_API_KEY']


def handle_document_pseudo_code(email_content, some_other_argument):
  """
    Detect the !!document! pseudo-code in the email content.
    If found, generates a structured response.
    """
  match = re.search(r"!!document!\((.*?)\)", email_content, re.DOTALL)
  if not match:
    return None, email_content

  pseudo_code_content = match.group(1).strip()
  structured_response = gpt4_generate_structured_response(
      pseudo_code_content, openai_api_key)

  # Remove the pseudo-code from the original email content
  new_email_content = re.sub(r"!!document!\(.*?\)",
                             "",
                             email_content,
                             flags=re.DOTALL).strip()

  return structured_response, new_email_content


def gpt4_generate_structured_response(pseudo_code_content, api_key):
  """
    Make a GPT-4 API call to generate a structured response based on the pseudo-code content.
    """
  openai.api_key = api_key
  response = None
  max_retries = 99
  delay = 30  # Starting delay in seconds
  max_delay = 30  # Maximum delay in seconds

  for i in range(max_retries):
    try:
      response = openai.ChatCompletion.create(
          model="gpt-4",
          messages=[{
              "role":
              "system",
              "content":
              "You are a helpful assistant that extracts projects and objects from emails."
          }, {
              "role": "user",
              "content": pseudo_code_content
          }],
          max_tokens=1000)
      break
    except openai.OpenAIError as e:
      print(e)
      sleep_time = min(delay * (2**i) + uniform(0.0, 0.1 * (2**i)), max_delay)
      print(f"Retrying in {sleep_time:.2f} seconds.")
      time.sleep(sleep_time)

  if response is None:
    print("Max retries reached. Could not generate a response.")
    return None

  structured_response = response['choices'][0]['message']['content'].strip()

  return json.dumps({"structured_response": structured_response}, indent=4)
