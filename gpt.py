import os
import time
import openai
openai.api_base = 'http://127.0.0.1:5000/v1'
#https://api.openai.com/v1
import tiktoken
import re
import pickle

from random import uniform

openai_api_key = os.environ['OPENAI_API_KEY']
domain_name = os.environ.get('DOMAIN_NAME', 'semantic-life.com')  



class GPTModel:

  def __init__(self):
    openai.api_key = openai_api_key
    self.load_state()  # Load state variables
    self.encoding = tiktoken.get_encoding("cl100k_base")
    self.api_calls_in_current_window = 0

  # UTILITIES

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

  # GENERATE RESPONSE

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

    # Increased total token limit for the payload
    max_tokens_hard_limit = 96000

    # New max tokens for the response
    tokens_limit = 4096

    while True:
      total_tokens = self.count_tokens(full_content +
                                       dynamic_prompt) + api_buffer
      if total_tokens + tokens_limit <= max_tokens_hard_limit:
        print(
            f"Content is within hard limit at {total_tokens + tokens_limit} tokens."
        )
        break
      if len(conversation_history) > truncate_chars:
        print(
            f"Total tokens: {total_tokens}, reducing conversation history by {truncate_chars} chars..."
        )
        conversation_history = conversation_history[-(
            len(conversation_history) - truncate_chars):]
        full_content = f"{content}\n\n{conversation_history}"  # Update here
      elif len(full_content) > truncate_chars:
        print(
            f"Total tokens: {total_tokens}, reducing full content by {truncate_chars} chars..."
        )
        full_content = full_content[:-truncate_chars]
        # No need to re-assemble full_content here; it's already updated
      else:
        print("Content is too short to truncate further. Exiting.")
        return None

      if additional_context:
        full_content += f"\n{additional_context}"
      if note:
        full_content += f"\n{note}"

      elif len(full_content) > truncate_chars:
        print(
            f"Total tokens: {total_tokens}, reducing full content by {truncate_chars} chars..."
        )
        full_content = full_content[:-truncate_chars]
      else:
        print("Content is too short to truncate further. Exiting.")
        return None

    # Change this line to set a default of 1500 tokens
    tokens_limit = 1500

    # Re-check the rate limit with the new token limit
    total_tokens = self.count_tokens(
        full_content + dynamic_prompt) + api_buffer + tokens_limit
    self.check_rate_limit(total_tokens)

    response = None
    for i in range(max_retries):
      try:
        request_payload = {
            "model":
            "gpt-4-1106-preview",
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
            0.5,
            "frequency_penalty":
            0.2,
            "presence_penalty":
            0.2,
            "temperature":
            0.6
        }

        #print("\n--- API Request Payload ---")
        # print((json.dumps(request_payload, indent=4)))

        response = openai.ChatCompletion.create(**request_payload)

        #print("\n--- API Response ---")
        # print(json.dumps(response, indent=4)[:142])

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


  def generate_agent_profile(self, description):
      """
      Generates a profile for a new agent based on the provided description.
      """
      # Construct the prompt for generating the agent profile
      prompt = f"Generate a detailed profile for an AI agent with the following characteristics: {description}"

      # Call the GPT model to generate the profile
      generated_profile = self.generate_response(prompt, "", "", is_summarize=False)

      # Parse the generated profile to extract relevant information
      # Note: The parsing logic here depends on how the response is structured.
      # You might need to adapt this based on the actual response format.
      profile_info = self.parse_generated_profile(generated_profile)

      # Construct the agent profile dictionary
      agent_profile = {
          "description": profile_info.get("description", ""),
          "name": profile_info.get("name", "Generated Agent"),
          "email": profile_info.get("email", f"generated_agent@{domain_name}"),
          # Add other relevant attributes from the profile
      }
      return agent_profile

  def parse_generated_profile(self, generated_text):
      """
      Parses the generated text to extract profile information.
      This is a placeholder function and should be implemented based on 
      the expected format of the generated profile text.
      """
      # Example parsing logic (this is just a placeholder)
      profile_info = {}
      if "Name:" in generated_text:
          profile_info["name"] = generated_text.split("Name:")[1].split("\n")[0].strip()
      if "Email:" in generated_text:
          profile_info["email"] = generated_text.split("Email:")[1].split("\n")[0].strip()
      if "Description:" in generated_text:
          profile_info["description"] = generated_text.split("Description:")[1].split("\n")[0].strip()

      return profile_info
