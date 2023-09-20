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


def handle_document_short_code(email_content, api_key, conversation_history=None, last_agent_response=""):
    """
    This modified function will handle the !detail shortcode and split the content based on the !split delimiter.
    """
    # Initialize the result dictionary
    result = {'type': None, 'content': None, 'new_content': email_content}
    
    # ... [rest of the function up to the Handling !detail short-code section]

    # Handling !detail short-code
    detail_matches = re.findall(r"!detail\((.*?)\)!detail", email_content, re.DOTALL)
    if not detail_matches:
        detail_matches = re.findall(r"!detail\((.*?)$", email_content, re.DOTALL)

    if detail_matches:
        detailed_responses = []
        for match in detail_matches:
            detail_content = match.strip()

            # Check if the content has the !previousResponse keyword and replace it
            if "!previousResponse" in detail_content:
                detail_content = detail_content.replace('!previousResponse', last_agent_response)

            # Split content based on !split and treat each section as a separate chunk
            split_sections = re.split(r'!split', detail_content)
            detailed_responses.extend([section.strip() for section in split_sections if section.strip()])

        new_email_content = re.sub(r"!detail\((.*?)\)!detail", "", email_content, flags=re.DOTALL)
        if not new_email_content:
            new_email_content = re.sub(r"!detail\((.*?)$", "", email_content, flags=re.DOTALL).strip()
        result['type'] = 'detail'
        result['content'] = detailed_responses
        result['new_content'] = new_email_content
        print(f"Split sections: {split_sections}")
        return result
    
    return result


def split_content_into_chunks(content, max_char_count=6000):
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
