import os
import time
from random import uniform

import openai

# Read OpenAI API key from environment variable
openai_api_key = os.environ['OPENAI_API_KEY']


class GPTModel:

  def __init__(self):
    # Set the API key
    openai.api_key = openai_api_key

  def generate_response(self, prompt, content, conversation_history="", additional_context=None):
    print("Generating Response")
    full_content = f"{content}\n\n{conversation_history}"
    response = None
    max_retries = 99
    delay = 30  # Starting delay in seconds
    max_delay = 30  # Maximum delay in seconds
    for i in range(max_retries):
      try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": full_content
                }
            ],
            max_tokens=4000,
            top_p=0.5,
            frequency_penalty=0.25,
            presence_penalty=0.25,
            temperature=0.5
        )
        break
      except openai.OpenAIError as e:
        print(e)
        sleep_time = min(delay * (2**i) + uniform(0.0, 0.1 * (2**i)),
                         max_delay)
        print(f"Retrying in {sleep_time:.2f} seconds.")
        time.sleep(sleep_time)
    if response is None:
      print("Max retries reached. Could not generate a response.")
      return None
    return response['choices'][0]['message']['content']