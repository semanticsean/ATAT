import os
import time
import json
import openai
import tiktoken
import re
from random import uniform
import pickle  # for serialization

openai_api_key = os.environ['OPENAI_API_KEY']


class GPTModel:

  def __init__(self):
    openai.api_key = openai_api_key
    self.load_state()  # Load state variables
    self.encoding = tiktoken.get_encoding("cl100k_base")
    self.api_calls_in_current_window = 0

  def load_state(self):
    try:
      with open("api_state.pkl", "rb") as f:
        state = pickle.load(f)
      self.first_api_call_time_in_current_window = state.get('first_time', 0)
      self.tokens_used_in_current_window = state.get('tokens_used', 0)
      self.api_calls_in_current_window = state.get('api_calls', 0)  # New state
    except FileNotFoundError:
      self.first_api_call_time_in_current_window = 0
      self.tokens_used_in_current_window = 0
      self.api_calls_in_current_window = 0  # New state

  def save_state(self):
    state = {
        'first_time': self.first_api_call_time_in_current_window,
        'tokens_used': self.tokens_used_in_current_window,
        'api_calls': self.api_calls_in_current_window  # New state
    }
    with open("api_state.pkl", "wb") as f:
      pickle.dump(state, f)

  def count_tokens(self, text):
    return len(self.encoding.encode(text))

  def check_rate_limit(self, tokens_needed):
    current_time = time.time()

    # Check if it's a new rate-limiting window
    if current_time - self.first_api_call_time_in_current_window >= 62:
      self.first_api_call_time_in_current_window = current_time
      self.tokens_used_in_current_window = 0
      self.api_calls_in_current_window = 0

    # Calculate remaining tokens and API calls in the current window
    remaining_tokens = 8000 - self.tokens_used_in_current_window
    remaining_api_calls = 2000 - self.api_calls_in_current_window

    # If either limit would be exceeded, sleep until the next window
    if tokens_needed > remaining_tokens or remaining_api_calls <= 0:
      sleep_time = 62 - (current_time -
                         self.first_api_call_time_in_current_window)
      print(
          f"Rate limit would be exceeded. Sleeping for {sleep_time:.2f} seconds."
      )
      time.sleep(sleep_time)
      self.first_api_call_time_in_current_window = time.time()
      self.tokens_used_in_current_window = 0
      self.api_calls_in_current_window = 0

    self.tokens_used_in_current_window += tokens_needed
    self.api_calls_in_current_window += 1
    self.save_state()

  def generate_response(self,
                      dynamic_prompt,
                      content,
                      conversation_history,
                      additional_context=None,
                      note=None,
                      is_summarize=False):
    print("Generating Response from gpt-4 call")

    max_retries = 99
    delay = 62
    max_delay = 3000

    full_content = f"{content}\n\n{conversation_history}" 
    if additional_context:
        full_content += f"\n{additional_context}"
    if note:
        full_content += f"\n{note}"

    # Remove '>'' and '=' if they occur more than once in sequence
    full_content = re.sub(r'>>+', '', full_content)
    full_content = re.sub(r'==+', '', full_content)

    # Always remove '=3D'
    full_content = full_content.replace('=3D', '')

    # Remove email addresses with specified domain endings
    email_pattern = r'\S+@\S+\.(com|net|co|org|ai)'
    full_content = re.sub(email_pattern, '', full_content)

    
    api_buffer = 50
    truncate_chars = 1000

    max_tokens_hard_limit = 8100
    tokens_limit = 1500  # max tokens for the response

    while True:
        total_tokens = self.count_tokens(full_content + dynamic_prompt) + api_buffer
        if total_tokens + tokens_limit <= max_tokens_hard_limit:
            print(f"Content is within hard limit at {total_tokens + tokens_limit} tokens.")
            break
        if len(conversation_history) > truncate_chars:
            print(f"Total tokens: {total_tokens}, reducing conversation history by {truncate_chars} chars...")
            conversation_history = conversation_history[-(len(conversation_history) - truncate_chars):]
        elif len(full_content) > truncate_chars:
            print(f"Total tokens: {total_tokens}, reducing full content by {truncate_chars} chars...")
            full_content = full_content[:-truncate_chars]
        else:
            print("Content is too short to truncate further. Exiting.")
            return None
        full_content = f"{content}\n\n{conversation_history}"
        if additional_context:
            full_content += f"\n{additional_context}"
        if note:
            full_content += f"\n{note}"
        elif len(full_content) > truncate_chars:
            print(f"Total tokens: {total_tokens}, reducing full content by {truncate_chars} chars...")
            full_content = full_content[:-truncate_chars]
        else:
            print("Content is too short to truncate further. Exiting.")
            return None

    # Change this line to set a default of 1500 tokens
    tokens_limit = 1500

    # Re-check the rate limit with the new token limit
    total_tokens = self.count_tokens(full_content + dynamic_prompt) + api_buffer + tokens_limit
    self.check_rate_limit(total_tokens)

    response = None
    for i in range(max_retries):
      try:
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
            tokens_limit,
            "top_p":
            0.7,
            "frequency_penalty":
            0.2,
            "presence_penalty":
            0.2,
            "temperature":
            0.6
        }

        #print("\n--- API Request Payload ---")
        #print((json.dumps(request_payload, indent=4)))

        response = openai.ChatCompletion.create(**request_payload)

        #print("\n--- API Response ---")
        #print(json.dumps(response, indent=4)[:142])

        break

      except openai.OpenAIError as e:
        print(e)
        sleep_time = max(
            min(delay * (2**i) + uniform(5, 0.1 * (2**i)), max_delay), 30)
        print(f"Retrying in {sleep_time:.2f} seconds.")
        time.sleep(sleep_time)

    if response is None:
      print("Max retries reached. Could not generate a response.")
      return None

    self.last_api_call_time = time.time()

    return response['choices'][0]['message']['content']
