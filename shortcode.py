import json
import re
import quopri
from doc_gen import gpt4_generate_structured_response
from html import unescape
from bs4 import BeautifulSoup


def auto_split_content(content, char_limit=11000):
  """
    Split the content based on character count and paragraph breaks.
    """
  chunks = []
  while content:
    # If the content is under the char_limit, append it to chunks and break
    if len(content) <= char_limit:
      chunks.append(content)
      break

    # Find the last paragraph break before the char_limit
    split_idx = content.rfind('\n', 0, char_limit)

    # If we didn't find a break, split at the char_limit
    split_idx = split_idx if split_idx != -1 else char_limit

    # Append the chunk to our list
    chunks.append(content[:split_idx])

    # Remove the chunked content
    content = content[split_idx:].strip()

  return chunks


def handle_document_short_code(email_content,
                               api_key,
                               conversation_history=None,
                               last_agent_response=""):
  # Decode quoted-printable content
  email_content = quopri.decodestring(email_content).decode()

  # Unescape HTML entities
  email_content = unescape(email_content)

  # Remove HTML tags
  email_content = BeautifulSoup(email_content, 'html.parser').get_text()

  # Initialize the result dictionary
  result = {'type': None, 'content': None, 'new_content': email_content}

  # Handling !detail short-code using unique delimiters
  # ... (This part remains the same, no changes here)

  # Updated Regex pattern for summarize to account for optional spaces
  summarize_matches = re.findall(
      r"!\s*summarize\s*\.\s*(.*?)\s*_start\s*!\s*(.*?)\s*!\s*summarize\s*_stop\s*!",
      email_content, re.DOTALL | re.IGNORECASE)
  if summarize_matches:
    modality, summarize_content = summarize_matches[0]
    summarize_content = summarize_content.strip()
    # ... (This part remains the same, no changes here)
    return result

  # Ensuring result is a dictionary before returning
  return {'type': None, 'content': None, 'new_content': email_content}


def split_content_into_chunks(content, max_char_count=9000):
  chunks = []
  # Split the content into sentences
  sentences = re.split('(?<=[.!?]) +', content.strip())
  current_chunk = ""
  for sentence in sentences:
    if len(current_chunk) + len(sentence) + 1 <= max_char_count:
      current_chunk += (" " + sentence).strip()
    else:
      chunks.append(current_chunk.strip())
      current_chunk = sentence.strip()
  # After processing all sentences, if current_chunk is not empty, add it as a chunk
  if current_chunk:
    chunks.append(current_chunk.strip())
  return chunks
