import json
import os
import re
import time
from random import uniform

import openai

openai_api_key = os.environ['OPENAI_API_KEY']


def gpt4_generate_structured_response(short_code_content, api_key):
  """
    Make a GPT-4 API call to generate a structured response based on the short-code content.
    """
  print(f"Getting style / structure")
  openai.api_key = api_key
  response = None
  max_retries = 99
  delay = 30  # variable
  max_delay = 30  # variable

  for i in range(max_retries):
    try:
      response = openai.ChatCompletion.create(
          model="gpt-4",
          messages=[{
              "role":
              "system",
              "content":
              "You are a highly specialized AI assistant whose expertise lies in crafting detailed and complex data structures from the content given in short codes. Analyze the following short code content meticulously and craft a detailed and comprehensive data structure from it."
          }, {
              "role": "user",
              "content": short_code_content
          }],
          max_tokens=256)
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
