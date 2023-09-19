import json
import os
import re
import logging
from doc_gen import gpt4_generate_structured_response


def handle_document_short_code(email_content,
                               api_key,
                               conversation_history=None):

  # Handling !style short-code
  match = re.search(r"!style\((.*?)\)", email_content, re.DOTALL)
  if match:
    short_code_content = match.group(1).strip()
    structured_response = gpt4_generate_structured_response(
        short_code_content, api_key)
    new_email_content = re.sub(r"!style\(.*?\)",
                               "",
                               email_content,
                               flags=re.DOTALL).strip()

    logging.info(
        f"Style shortcode: {structured_response}, {new_email_content}")
    return structured_response, new_email_content, None

  # Handling !detail short-code
  detail_matches = re.findall(r"!detail\((.*?)\)", email_content, re.DOTALL)
  if detail_matches:
    detailed_responses = []
    for match in detail_matches:
      detail_content = match.strip()
      if not detail_content:
        last_message = conversation_history.split(
            '\n')[-1] if conversation_history else ""
        detail_content = last_message

      # Split the content at !split shortcodes first
      split_sections = re.split(r'!split', detail_content)

      detailed_responses.extend(split_sections)

    new_email_content = re.sub(r"!detail\(.*?\)",
                               "",
                               email_content,
                               flags=re.DOTALL).strip()

    logging.info(
        f"Detail shortcode matched: {str(detailed_responses)[:11]}, {new_email_content[:11]}"
    )

    return {
        'type': 'detail',
        'content': detailed_responses,
        'new_content': new_email_content
    }

  return {}, email_content, None


def split_content_into_chunks(content, max_char_count=6000):
  chunks = []

  # Split the content at !split shortcodes first
  split_sections = re.split(r'!split', content)

  for section in split_sections:
    # Further split each section into sentences
    sentences = re.split('(?<=[.!?]) +', section.strip())

    current_chunk = ""
    for sentence in sentences:
      if len(current_chunk) + len(sentence) + 1 <= max_char_count:
        current_chunk += (" " + sentence).strip()
      else:
        chunks.append(current_chunk.strip())
        current_chunk = sentence.strip()

    # After processing a section, if current_chunk is not empty, add it as a chunk
    if current_chunk:
      chunks.append(current_chunk.strip())
      current_chunk = ""

  return chunks
