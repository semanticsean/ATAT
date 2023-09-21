import json
import re
from doc_gen import gpt4_generate_structured_response


def auto_split_content(content, char_limit=3000):
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
  """
    This function handles both the !detail and !summarize shortcodes.
    """
  # Initialize the result dictionary
  result = {'type': None, 'content': None, 'new_content': email_content}

  # Handling !detail short-code using unique delimiters
  detail_matches = re.findall(r"!detail_start!(.*?)!detail_stop!",
                              email_content, re.DOTALL)
  if detail_matches:
    detailed_responses = []
    for match in detail_matches:
      detail_content = match.strip()

      # Check if the content has the !previousResponse keyword and replace it
      if "!previousResponse" in detail_content:
        detail_content = detail_content.replace('!previousResponse',
                                                last_agent_response)

      # Split content based on !split and treat each section as a separate chunk
      split_sections = re.split(r'!split!', detail_content)
      detailed_responses.extend(
          [section.strip() for section in split_sections if section.strip()])

    new_email_content = re.sub(r"!detail_start!(.*?)!detail_stop!",
                               "",
                               email_content,
                               flags=re.DOTALL).strip()
    result['type'] = 'detail'
    result['content'] = detailed_responses
    result['new_content'] = new_email_content
    return result

  # Handling !summarize short-code using unique delimiters
  summarize_matches = re.findall(
      r"!summarize\.(.*?)_start!(.*?)!summarize_stop!", email_content,
      re.DOTALL)
  if summarize_matches:
    modality, summarize_content = summarize_matches[0]
    summarize_content = summarize_content.strip()

    # Check if the content has the !previousResponse keyword and replace it
    if "!previousResponse" in summarize_content:
      summarize_content = summarize_content.replace('!previousResponse',
                                                    last_agent_response)

    # Check if the summarize_content is too long and needs splitting
    if len(summarize_content) > 3000:  # or any other limit you prefer
      summarized_responses = auto_split_content(summarize_content)
    else:
      summarized_responses = [summarize_content]

    new_email_content = re.sub(
        r"!summarize\.(.*?)_start!(.*?)!summarize_stop!",
        "",
        email_content,
        flags=re.DOTALL).strip()
    result['type'] = 'summarize'
    result['content'] = summarized_responses
    result['modality'] = modality
    result['new_content'] = new_email_content
    return result

  # Ensuring result is a dictionary before returning
  if not isinstance(result, dict):
    result = {'type': None, 'content': None, 'new_content': email_content}

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
