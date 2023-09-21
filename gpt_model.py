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
        print("GPTModel Initialized")

    def generate_response(self, dynamic_prompt, content, conversation_history, additional_context=None, note=None):
        print("Generating Response from gpt-4 call")

        current_time = time.time()
        elapsed_time = current_time - self.last_api_call_time

        # If it hasn't been 60 seconds since the last API call, wait for the remaining time
        if elapsed_time < 60:
            sleep_duration = 60 - elapsed_time
            print(f"Sleeping for {sleep_duration:.2f} seconds to avoid rate limits.")
            time.sleep(sleep_duration)

        while True:
            full_content = f"{content}\n\n{conversation_history}"
            if additional_context:
                full_content += f"\n{additional_context}"
            if note:
                full_content += f"\n{note}"

            max_tokens_allowed = 4192 - len(content.split()) - len(dynamic_prompt.split())
            if additional_context:
                max_tokens_allowed -= len(additional_context.split())
            if note:
                max_tokens_allowed -= len(note.split())

            # If there's still room, break out of the loop
            if len(full_content.split()) <= max_tokens_allowed:
                break

            # Try to truncate conversation_history first
            if len(conversation_history.split("\n")) > 1:
                conversation_history = "\n".join(conversation_history.split("\n")[1:])
                continue

            # If truncating conversation_history isn't enough, try to truncate additional_context
            if additional_context and len(additional_context.split("\n")) > 1:
                additional_context = "\n".join(additional_context.split("\n")[1:])
                continue

            # Finally, try to truncate note if needed
            if note and len(note.split("\n")) > 1:
                note = "\n".join(note.split("\n")[1:])
                continue

            # If we reach here, it means we can't truncate further
            print("Cannot truncate content further to fit API call.")
            return "Error: Content is too long. Please shorten your input."

        conversation_history = ""  # Clear conversation history to make space

        is_error_logged = False

        while len(conversation_history.split()) > max_tokens_allowed:
            if not is_error_logged:
                print("Truncating conversation history...")
                is_error_logged = True
            # Drop half of the messages in the history
            conversation_history = "\n".join(
                conversation_history.split("\n")
                [len(conversation_history.split("\n")) // 2:])

        print("Finalizing content for API request.")
        full_content = f"{content}\n\n{conversation_history}"
        if additional_context:
            full_content += f"\n{additional_context}"
        if note:
            full_content += f"\n{note}"

        response = None
        max_retries = 99
        delay = 60  # variable
        max_delay = 3000  # variable

        for i in range(max_retries):
            try:
                if len(full_content.split()) > max_tokens_allowed:
                    # Truncate from the beginning of the content
                    full_content = " ".join(full_content.split()[-max_tokens_allowed:])

                request_payload = {
                    "model": "gpt-4",
                    "messages": [{
                                "role": "system",
                                "content": dynamic_prompt
                            }, {
                                "role": "user",
                                "content": full_content
                            }],
                            "max_tokens": 4000,
                            "top_p": 0.7,
                            "frequency_penalty": 0.2,
                            "presence_penalty": 0.2,
                            "temperature": 0.6
                        }

                print("\n--- API Request Payload ---")
                print(json.dumps(request_payload, indent=4))

                response = openai.ChatCompletion.create(
                    **request_payload)  # Updated this line

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
        print(f"Updated last API call time to: {self.last_api_call_time}")

        return response['choices'][0]['message']['content']
