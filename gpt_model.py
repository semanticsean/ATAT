import os
import time
from random import uniform, randint
import json
import datetime

import openai

openai_api_key = os.environ['OPENAI_API_KEY']

class GPTModel:

    def __init__(self):
        openai.api_key = openai_api_key
        self.tokens_this_minute = 0
        self.token_reset_time = datetime.datetime.now() + datetime.timedelta(minutes=1)

    def _reset_tokens(self):
        now = datetime.datetime.now()
        if now >= self.token_reset_time:
            self.tokens_this_minute = 0
            self.token_reset_time = now + datetime.timedelta(minutes=1)

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
    
        # Trim the full_content to fit within the character limit
        if len(full_content) > 16000:
            full_content = full_content[-16000:]
    
        response = None
        max_retries = 99
        delay = 10  # Initial delay duration in seconds
    
        for i in range(max_retries):
            self._reset_tokens()  # Check and reset the token counter if needed
    
            tokens_for_request = len(full_content.split()) + 3800  # Reduced buffer to 2,000 tokens
    
            if self.tokens_this_minute + tokens_for_request > 10000:
                sleep_seconds = (self.token_reset_time - datetime.datetime.now()).seconds + 1
                print(f"Tokens per minute exceeded. Sleeping for {sleep_seconds} seconds.")
                time.sleep(sleep_seconds)
                self._reset_tokens()
    
            try:
                message_tokens = len(full_content.split())
                if message_tokens > 8100:
                    max_tokens = 8192 - message_tokens
                else:
                    max_tokens = 4000
    
                request_payload = {
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": dynamic_prompt
                        },
                        {
                            "role": "user",
                            "content": full_content
                        }
                    ],
                    "max_tokens": max_tokens,
                    "top_p": 0.7,
                    "frequency_penalty": 0.2,
                    "presence_penalty": 0.2,
                    "temperature": 0.6
                }

                response = openai.ChatCompletion.create(**request_payload)
                self.tokens_this_minute += tokens_for_request  # Update the token counter
    
                break
    
            except openai.OpenAIError as e:
                print(e)
    
                # Handle rate limit error specifically
                if "Rate limit reached" in str(e):
                    sleep_duration = float(re.search(r"Please try again in (\d+\.?\d*)ms", str(e)).group(1)) / 1000
                    print(f"Rate limit exceeded. Sleeping for {sleep_duration:.2f} seconds.")
                    time.sleep(sleep_duration)
                    continue  # Skip the rest of the loop iteration
    
                jitter = randint(1000, 3000) / 1000.0  # Random jitter between 0 and 1 second
                sleep_time = min(delay, 60) + jitter  # Adding jitter to delay
                print(f"Retrying in {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                delay *= 2  # Double the delay duration for exponential backoff
    
        if response is None:
            print("Max retries reached. Could not generate a response.")
            return None
    
        return response['choices'][0]['message']['content']