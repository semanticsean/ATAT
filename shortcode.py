import json
import os
import re
from random import uniform
from doc_gen import gpt4_generate_structured_response

def handle_document_short_code(email_content, api_key):
    """
    Detect the !style short-code in the email content.
    If found, generates a structured response.
    """
    # Regex pattern to find the !style short-code
    match = re.search(r"!style\((.*?)\)", email_content, re.DOTALL)
    if not match:
        return None, email_content

    short_code_content = match.group(1).strip()
    structured_response = gpt4_generate_structured_response(
        short_code_content, api_key)

    new_email_content = re.sub(r"!style\(.*?\)",
                               "",
                               email_content,
                               flags=re.DOTALL).strip()

    return structured_response, new_email_content
