import os
import time
import openai
import tiktoken
import re
import pickle
from random import uniform

# Ensure you have imported OpenAI library correctly
from openai import OpenAI

openai_api_key = os.environ['OPENAI_API_KEY']

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
            self.api_calls_in_current_window = state.get('api_calls', 0)
        except FileNotFoundError:
            self.first_api_call_time_in_current_window = 0
            self.tokens_used_in_current_window = 0
            self.api_calls_in_current_window = 0

    def save_state(self):
        state = {
            'first_time': self.first_api_call_time_in_current_window,
            'tokens_used': self.tokens_used_in_current_window,
            'api_calls': self.api_calls_in_current_window
        }
        with open("api_state.pkl", "wb") as f:
            pickle.dump(state, f)

    def count_tokens(self, text):
        return len(self.encoding.encode(text))

    def check_rate_limit(self, tokens_needed):
        current_time = time.time()
        if current_time - self.first_api_call_time_in_current_window >= 62:
            self.first_api_call_time_in_current_window = current_time
            self.tokens_used_in_current_window = 0
            self.api_calls_in_current_window = 0

        remaining_tokens = 8000 - self.tokens_used_in_current_window
        remaining_api_calls = 2000 - self.api_calls_in_current_window

        if tokens_needed > remaining_tokens or remaining_api_calls <= 0:
            sleep_time = 62 - (current_time - self.first_api_call_time_in_current_window)
            print(f"Rate limit would be exceeded. Sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)
            self.first_api_call_time_in_current_window = time.time()
            self.tokens_used_in_current_window = 0
            self.api_calls_in_current_window = 0

        self.tokens_used_in_current_window += tokens_needed
        self.api_calls_in_current_window += 1
        self.save_state()

    # GENERATE RESPONSE

    def generate_response(self, dynamic_prompt, content, conversation_history, additional_context=None, note=None, is_summarize=False):
        print("Generating Response from GPT-4 call")

        # Initialize full_content before the while loop
        full_content = f"{content}\n\n{conversation_history}"
        if additional_context:
            full_content += f"\n{additional_context}"
        if note:
            full_content += f"\n{note}"

        max_retries = 99
        delay = 62
        max_delay = 3000
        api_buffer = 50
        truncate_chars = 1000
        max_tokens_hard_limit = 96000
        tokens_limit = 512

        while True:
            total_tokens = self.count_tokens(full_content + dynamic_prompt) + api_buffer
            if total_tokens + tokens_limit <= max_tokens_hard_limit:
                print(f"Content is within hard limit at {total_tokens + tokens_limit} tokens.")
                break

            if len(conversation_history) > truncate_chars:
                conversation_history = conversation_history[-(len(conversation_history) - truncate_chars):]
                full_content = f"{content}\n\n{conversation_history}"
            elif len(full_content) > truncate_chars:
                full_content = full_content[:-truncate_chars]
            else:
                print("Content is too short to truncate further. Exiting.")
                return "Error: Content too short for further truncation."

        # Re-check the rate limit with the new token limit
        total_tokens = self.count_tokens(full_content + dynamic_prompt) + api_buffer + tokens_limit
        self.check_rate_limit(total_tokens)

        client = OpenAI(api_key=openai_api_key)

        response = None
        for i in range(max_retries):
            try:
                prompt = full_content + "\n" + dynamic_prompt
                request_payload = {
                    "model": "gpt-4-1106-preview",
                    "prompt": prompt,
                    "max_tokens": tokens_limit,
                    "temperature": 0.6,
                    "top_p": 0.5,
                    "frequency_penalty": 0.2,
                    "presence_penalty": 0.2
                }
                response = client.completions.create(**request_payload)
                print(request_payload)
                break
            except openai.OpenAIError as e:
                print("OpenAI Error:", e)
                sleep_time = max(min(delay * (2**i) + uniform(5, 0.1 * (2**i)), max_delay), 30)
                print(f"Retrying in {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)

        if response is None or not response.choices:
            print("Max retries reached or no choices returned. Could not generate a response.")
            return "Error: Unable to generate response from GPT-4."

        generated_text = response.choices[0].text if response.choices[0].text.strip() else "Error: Empty response from GPT-4."
        self.last_api_call_time = time.time()

        print(generated_text)
        
      
        return generated_text


