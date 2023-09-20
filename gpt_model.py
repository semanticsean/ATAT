import os
import time
from random import uniform
import json

import openai

openai_api_key = os.environ['OPENAI_API_KEY']

class GPTModel:

    tokens_this_minute = 0  # Class variable to keep track of tokens generated in the current minute
    last_request_time = 0  # Class variable to track the last request time

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
        max_delay = 3000  # variable
        token_limit_per_minute = 10000  # The rate limit for tokens per minute

        for i in range(max_retries):
            # Check if a minute has passed since the last request
            if time.time() - GPTModel.last_request_time > 60:
                GPTModel.tokens_this_minute = 0  # Reset the token count for the new minute

            # Calculate expected tokens for the current request
            expected_tokens = len(full_content.split()) + 4000  # +4000 for safe margin

            # If expected tokens will exceed the limit, then wait
            if GPTModel.tokens_this_minute + expected_tokens > token_limit_per_minute:
                wait_time = 60 - (time.time() - GPTModel.last_request_time)
                print(f"Approaching token limit. Waiting for {wait_time:.2f} seconds.")
                time.sleep(wait_time)
                GPTModel.tokens_this_minute = 0  # Reset token count after waiting

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
                # Update token count and request time after successful request
                GPTModel.tokens_this_minute += expected_tokens
                GPTModel.last_request_time = time.time()

                break

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
        