import openai
from openai.error import OpenAIError
import os
import time
from random import uniform

openai.ChatCompletion.create(
  model="gpt-4",
  messages=[    
        {"role": "system", "content": "You are a helpful assistant that extracts projects and objects from emails."},
        {"role": "user", "content": "Extract the projects and objects from the following emails:"}
    ],
  functions=[
        {
          "name": "extract_projects_and_objects",
          "parameters": {
            "type": "object",
            "properties": {
              "emails": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "content": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          },
          "output": {
            "type": "object",
            "properties": {
              "projects": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "name": {
                      "type": "string"
                    },
                    "objects": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  }
                }
              }
            }
          }
        }
    ],
  function_call={"name": "extract_projects_and_objects", "input": {"emails": [{"content": "email 1 content"}, {"content": "email 2 content"}]}}
)


class GPTModel:

    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def generate_response(self, prompt, content):
        print("Generating Response")
        response = None
        max_retries = 99
        delay = 30  # Starting delay in seconds
        max_delay = 30  # Maximum delay in seconds
        for i in range(max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{
                        "role": "system",
                        "content": prompt
                    }, {
                        "role": "user",
                        "content": content
                    }],
                    max_tokens=4000,
                    top_p=0.6,
                    frequency_penalty=0.25,
                    presence_penalty=0.25,
                    temperature=0.8
                )
                break
            except OpenAIError as e:
                print(e)
                sleep_time = min(delay * (2 ** i) + uniform(0.0, 0.1 * (2 ** i)), max_delay)
                print(f"Retrying in {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
        if response is None:
            print("Max retries reached. Could not generate a response.")
            return None
        return response['choices'][0]['message']['content']
