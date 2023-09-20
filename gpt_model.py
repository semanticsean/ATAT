import os
import time
from random import uniform
import json

import openai

openai_api_key = os.environ['OPENAI_API_KEY']


class GPTModel:

  def __init__(self):
    openai.api_key = openai_api_key
    self.last_api_call_time = 0


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

    current_time = time.time()
    elapsed_time = current_time - self.last_api_call_time

    # If it hasn't been 60 seconds since the last API call, wait for the remaining time
    if elapsed_time < 60:
        sleep_duration = 60 - elapsed_time
        print(f"Sleeping for {sleep_duration:.2f} seconds to avoid rate limits.")
        time.sleep(sleep_duration)

    response = None
    max_retries = 99
    delay = 60  # variable
    max_delay = 3000  # variable

    for i in range(max_retries):
      try:
        # Check and truncate content and conversation_history if total tokens exceed the maximum limit
        total_tokens = len(content.split()) + len(
            conversation_history.split()) + 4000
        if additional_context:
          total_tokens += len(additional_context.split())
        if note:
          total_tokens += len(note.split())

        if total_tokens > 8000:
          excess_tokens = total_tokens - 8000
          conversation_history = " ".join(
              conversation_history.split()[:-excess_tokens])

        request_payload = {
            "model":
            "gpt-4",
            "messages": [{
                "role": "system",
                "content": dynamic_prompt
            }, {
                "role": "user",
                "content": full_content
            }],
            "max_tokens":
            4000,
            "top_p":
            0.7,
            "frequency_penalty":
            0.2,
            "presence_penalty":
            0.2,
            "temperature":
            0.6
        }

        print("\n--- API Request Payload ---")
        print(json.dumps(request_payload, indent=4))

        response = openai.ChatCompletion.create(**request_payload)

        print("\n--- API Response ---")
        print(json.dumps(response, indent=4))

        break

      except openai.OpenAIError as e:
        print(e)
        sleep_time = max(
            min(delay * (2**i) + uniform(0.0, 0.1 * (2**i)), max_delay), 30)
        print(f"Retrying in {sleep_time:.2f} seconds.")
        time.sleep(sleep_time)
      else:
        break

    if response is None:
      print("Max retries reached. Could not generate a response.")
      return None

    # Update the last_api_call_time at the end of the API call
    self.last_api_call_time = time.time()

    return response['choices'][0]['message']['content']
