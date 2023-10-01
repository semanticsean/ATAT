import os
import time
import json
import openai
import tiktoken

openai_api_key = os.environ['OPENAI_API_KEY']

class GPTModel:

    def __init__(self):
        openai.api_key = openai_api_key
        self.last_api_call_time = 0
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text):
        return len(self.encoding.encode(text))

    def generate_response(self,
                           dynamic_prompt,
                           content,
                           conversation_history,
                           additional_context=None,
                           note=None,
                           is_summarize=False):
        print("Generating Response from gpt-4 call")
        response = None
        max_retries = 99
        delay = 60
        max_delay = 3000
        tokens_limit = 1024 if is_summarize else 4000
        base_value = 8192 - tokens_limit if is_summarize else 4192
        print(f"Set tokens_limit to {tokens_limit} based on is_summarize={is_summarize}.")

        full_content = f"{content}\n\n{conversation_history}"
        if additional_context:
            full_content += f"\n{additional_context}"
        if note:
            full_content += f"\n{note}"

        # Calculate total tokens for the request
        total_tokens = self.count_tokens(full_content + dynamic_prompt)
        if total_tokens > 8192:
            tokens_limit = max(52, tokens_limit - (total_tokens - 8192))

        current_time = time.time()
        elapsed_time = current_time - self.last_api_call_time

        if elapsed_time < 60:
            sleep_duration = 60 - elapsed_time
            print(f"Sleeping for {sleep_duration:.2f} seconds to avoid rate limits.")
            time.sleep(sleep_duration)

        # Calculate the maximum tokens allowed for the conversation content.
        max_tokens_allowed = base_value - len(content.split()) - len(
            dynamic_prompt.split())
        if additional_context:
            max_tokens_allowed -= len(additional_context.split())
        if note:
            max_tokens_allowed -= len(note.split())

        # Check and truncate conversation_history if total tokens exceed the maximum limit
        while len(conversation_history.split()) > max_tokens_allowed:
            # Check if there's a newline character in the conversation_history
            if "\n" not in conversation_history:
                print(
                    "WARNING: No newline character found in conversation_history. Breaking out of truncation loop."
                )
                break

            # Drop the oldest message (assumes each message in the history is separated by a newline)
            conversation_history = "\n".join(conversation_history.split("\n")[1:])

        # Update the full_content after potentially truncating the conversation_history
        full_content = f"{content}\n\n{conversation_history}"
        if additional_context:
            full_content += f"\n{additional_context}"
        if note:
            full_content += f"\n{note}"

        print(f"Token limit for this request: {tokens_limit}")

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

                print("\n--- API Request Payload ---")
                print((json.dumps(request_payload, indent=4))[:140])

                response = openai.ChatCompletion.create(
                    **request_payload)  # Updated this line

                print("\n--- API Response ---")
                print(json.dumps(response, indent=4)[:142])

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
