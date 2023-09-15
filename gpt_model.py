import os
import time
from random import uniform

import openai

openai_api_key = os.environ['OPENAI_API_KEY']


class GPTModel:

  def __init__(self):
    openai.api_key = openai_api_key

  def generate_response(self,
                        dynamic_prompt,
                        content,
                        conversation_history,
                        additional_context=None,
                        note=None):
    print("Generating Response")
    full_content = f"{content}\n\n{conversation_history}"
    if additional_context:
      full_content += f"\n{additional_context}"
    if note:
      full_content += f"\n{note}"

    response = None
    max_retries = 99
    delay = 30  # variable
    max_delay = 30  # variable

    for i in range(max_retries):
      try:
        # ... (rest of the method for generating the response)
        # Correcting the syntax error in the return statement
        return response['choices'][0]['message']['content']
      except openai.OpenAIError as e:
        print(e)
        sleep_time = min(delay * (2**i) + uniform(0.0, 0.1 * (2**i)),
                         max_delay)
        print(f"Retrying in {sleep_time:.2f} seconds.")
        time.sleep(sleep_time)
      else:
        break

    if response is None:
      print("Max retries reached. Could not generate a response.")
      return None

    return response['choices'][0]['message']['content']
