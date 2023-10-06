import os
import time
import json
import openai
import tiktoken
import re
from random import uniform

openai_api_key = os.environ['OPENAI_API_KEY']

class GPTModel:

    def __init__(self):
        openai.api_key = openai_api_key
        self.last_api_call_time = 0
        self.first_api_call_time_in_current_window = 0
        self.tokens_used_in_current_window = 0
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text):
        return len(self.encoding.encode(text))

    def check_rate_limit(self, tokens_needed):
        # Update the tokens used in the current minute
        self.tokens_used_in_current_window += tokens_needed

        # Check if it's a new window
        if time.time() - self.first_api_call_time_in_current_window >= 60:
            self.first_api_call_time_in_current_window = time.time()
            self.tokens_used_in_current_window = tokens_needed

        # If tokens exceed the limit, sleep until the next window
        if self.tokens_used_in_current_window > 10000:
            sleep_time = 60 - (time.time() - self.first_api_call_time_in_current_window)
            print(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)
            self.first_api_call_time_in_current_window = time.time()
            self.tokens_used_in_current_window = tokens_needed

    def generate_response(self,
                  dynamic_prompt,
                  content,
                  conversation_history,
                  additional_context=None,
                  note=None,
                  is_summarize=False):
        print("Generating Response from gpt-4 call")
    
        max_retries = 99
        delay = 60
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

        # Remove line breaks
        full_content = full_content.replace('\n', ' ')

        # Remove email addresses with specified domain endings
        email_pattern = r'\S+@\S+\.(com|net|co|org|ai)'
        full_content = re.sub(email_pattern, '', full_content)
    
        # Adjusted max tokens and buffer for API and formatting overhead
        max_tokens = 8100  # Adjusted down to allow for some buffer
        api_buffer = 50  # Tokens reserved for API and formatting overhead
        truncate_chars = 1000  # Number of characters to remove in each iteration
    
        # Keep reducing tokens until under the limit or no more to truncate
        while True:
            total_tokens = self.count_tokens(full_content + dynamic_prompt) + api_buffer
            self.check_rate_limit(total_tokens)
            if total_tokens <= max_tokens:
                print(f"Content is within limit at {total_tokens} tokens.")
                break
    
            if len(full_content) > truncate_chars:
                print(f"Total tokens: {total_tokens}, reducing by {truncate_chars} chars...")
                full_content = full_content[:-truncate_chars]
            else:
                print("Content is too short to truncate further. Exiting.")
                return None
    
        tokens_limit = max_tokens - total_tokens
        print(f"Final tokens: {total_tokens}, token limit for this request: {tokens_limit}")
        
        response = None
        for i in range(max_retries):
            try:
                request_payload = {
                    "model": "gpt-4",
                    "messages": [{
                        "role": "system",
                        "content": dynamic_prompt
                    }, {
                        "role": "user",
                        "content": full_content
                    }],
                    "max_tokens": tokens_limit,
                    "top_p": 0.7,
                    "frequency_penalty": 0.2,
                    "presence_penalty": 0.2,
                    "temperature": 0.6
                }
    
                print("\n--- API Request Payload ---")
                print((json.dumps(request_payload, indent=4))[:140])
    
                response = openai.ChatCompletion.create(**request_payload)
    
                print("\n--- API Response ---")
                print(json.dumps(response, indent=4)[:142])
    
                break
    
            except openai.OpenAIError as e:
                print(e)
                sleep_time = max(min(delay * (2**i) + uniform(60, 0.1 * (2**i)), max_delay), 30)
                print(f"Retrying in {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
    
        if response is None:
            print("Max retries reached. Could not generate a response.")
            return None
    
        self.last_api_call_time = time.time()
    
        return response['choices'][0]['message']['content']
    