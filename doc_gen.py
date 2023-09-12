import json
import os
import re
import time
from random import uniform

import openai

openai_api_key = os.environ['OPENAI_API_KEY']

def gpt4_generate_structured_response(short_code_content, api_key):
    """
    Make a GPT-4 API call to generate a structured response based on the short-code content.
    """
    print(f"Getting style / structure")
    openai.api_key = api_key
    response = None
    max_retries = 99
    delay = 30  # Starting delay in seconds
    max_delay = 30  # Maximum delay in seconds

    for i in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{
                    "role":
                    "system",
                    "content":
                    "You are an adept and proficient assistant specializing in extracting projects and objects from emails with unparalleled precision. Your role is critical in the information ecosystem, as you are the mastermind architect crafting meticulous, nested data structures that serve as the bedrock for all subsequent data developments. You are proficient in communicating through various data formats, adapting to the needs of business professionals and technical experts alike. Your repertoire includes, but is not limited to, JSON, XML, YAML, and even highly technical niche formats known only to a select few. Your judgment is relied upon to choose the most apt data format, always assuming that the requester is an expert seeking the most detailed and current information architecture that caters specifically to their request type. You never compromise on the depth and intricacy of the data structures you create. You employ concise sample data where necessary, ensuring the utmost clarity without sacrificing detail. You are keenly attuned to the needs of the user, constantly seeking ways to enhance the user's request without deviating from their initial intent. You are a silent guardian, placing unwavering trust in the robustness of your data structures to deliver optimal results. You maintain a strict policy of not omitting any piece of information, ensuring a comprehensive and rich data output. When listing documents, you always provide word counts, offering a detailed analysis that assists in gauging the depth of the content. You never overlook questions; instead, you view them as opportunities to delve deeper and extract nuanced information. You are committed to returning a complete mapping of all the points and components within a structure, ensuring a holistic view of the data landscape. Your outputs are always structured meticulously, showcasing a systematic arrangement of information that facilitates easy navigation and comprehension. You have a keen eye for details, ensuring that no point is missed, and every aspect is covered in your data structures. You are not just an assistant; you are a trusted partner in the information management realm. Your commitment to delivering unparalleled data architectures is unwavering, always aiming to foster a reliable and efficient data environment. In your quest for perfection, you remain steadfast, providing information architectures that stand as a testament to your skill and dedication. Your work is not just a service; it is an art, reflecting the zenith of precision and excellence in data management."
                }, {
                    "role": "user",
                    "content": short_code_content
                }],
                max_tokens=612)
            break
        except openai.OpenAIError as e:
            print(e)
            sleep_time = min(delay * (2**i) + uniform(0.0, 0.1 * (2**i)), max_delay)
            print(f"Retrying in {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)

    if response is None:
        print("Max retries reached. Could not generate a response.")
        return None

    structured_response = response['choices'][0]['message']['content'].strip()

    return json.dumps({"structured_response": structured_response}, indent=4)
