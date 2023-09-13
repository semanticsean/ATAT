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
                # Check and truncate content and conversation_history if total tokens exceed the maximum limit
                total_tokens = len(content.split()) + len(conversation_history.split()) + 4000
                if additional_context:
                    total_tokens += len(additional_context.split())
                if note:
                    total_tokens += len(note.split())

                if total_tokens > 8000:
                    excess_tokens = total_tokens - 8000
                    conversation_history = " ".join(conversation_history.split()[:-excess_tokens])

                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{
                        "role": "system",
                        "content": dynamic_prompt
                    }, {
                        "role": "user",
                        "content": full_content
                    }],
                    max_tokens=4000,
                    top_p=0.7,  # variable
                    frequency_penalty=0.5,  # variable
                    presence_penalty=0.5,  # variable
                    temperature=0.3  # variable
                )
                break

            except openai.OpenAIError as e:
                print(e)
                sleep_time = min(delay * (2**i) + uniform(0.0, 0.1 * (2**i)), max_delay)
                print(f"Retrying in {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
            else:
                break

        if response is None:
            print("Max retries reached. Could not generate a response.")
            return None

        return response['choices'][0]['message']['content']
