import re
import time
import json
import os
import threading
import logging
import quopri
from shortcode import handle_document_short_code
from gpt_model import GPTModel
from datetime import datetime
import logging

#logging.basicConfig(level=logging.DEBUG)


# Sample function to mock the datetime formatting
def format_datetime_for_email():
  return datetime.now().strftime('%a, %b %d, %Y at %I:%M %p')


# Sample function to format Gmail-style note
def format_note(agent_name, email="email@example.com", timestamp=None):
  if not timestamp:
    timestamp = format_datetime_for_email()
  return f'On {timestamp} {agent_name} <{email}> wrote:'


def load_instructions(filename='agents/instructions.json'):
  with open(filename, 'r') as file:
    return json.load(file)


class AgentSelector:

  def __init__(self, max_agents=12):
    self.lock = threading.Lock()
    self.openai_api_key = os.environ['OPENAI_API_KEY']
    self.max_agents = max_agents
    self.conversation_structure = {}
    self.conversation_history = ""
    self.invoked_agents = {}
    self.last_agent_response = ""
    self.instructions = load_instructions()
    self.gpt_model = GPTModel()

  def reset_for_new_thread(self):
    self.invoked_agents.clear()
    self.conversation_structure = {}
    self.conversation_history = ""

  def replace_agent_shortcodes(self, content):
    """
        Replaces !ff(agent_name)! shortcodes with the agent's name.
        """
    return re.sub(r"!ff\((\w+)\)!", r"\1", content)

  def _create_dynamic_prompt(self,
                             agent_manager,
                             agent_name,
                             order,
                             total_order,
                             structured_response=None,
                             modality=None,
                             content=None):

    order_explanation = ", ".join([
        f"('{resp[0]}', {resp[1]})"
        for resp in self.conversation_structure.get("responses", [])
    ])

    # Order and Persona Context
    order_context = f"You are role-playing as the {agent_name}. This is the {order}th response in a conversation with {total_order} interactions. The agent sequence is: [{order_explanation}]."
    persona = agent_manager.get_agent_persona(agent_name)
    persona_context = f"You are {agent_name}. {persona}" if persona else f"You are {agent_name}."

    # Main Instructions
    instructions = self.instructions['default']['main_instructions']

    # Structured Response
    if structured_response:
      instructions += self.instructions['default'][
          'structured_response_guidelines']
      instructions += f"\n\n=== STRUCTURED RESPONSE GUIDELINES ===\n{structured_response}\n=== END OF GUIDELINES ==="

    # Check for modality-specific instructions
    if modality and modality in self.instructions['summarize']:
      instructions = self.instructions['summarize'][modality]

      # If there's an additional_context_chunk for the modality, append it
      if 'additional_context_chunk' in self.instructions['summarize']:
        additional_context_chunk = self.instructions['summarize'][
            'additional_context_chunk'].format(part_number=1, total_parts=1)
        instructions += " " + additional_context_chunk

    # Creating the dynamic prompt in the specified order
    dynamic_prompt = f"{order_context}"

    # Inserting the email content
    if content:
      dynamic_prompt += f"YOU ARE ON AN EMAIL THREAD. YOU ONLY RESPOND AS THE APPROPRIATE AGENT. THE EMAIL YOU NEED TO RESPOND TO IS AS FOLLOWS: '''{content}'''."

    dynamic_prompt += f" {instructions}. {persona_context}. Act as this agent."

    print(f"{dynamic_prompt}")

    return dynamic_prompt

  @staticmethod
  def safe_ascii_string(s):
    return ''.join(c if ord(c) < 128 else '?' for c in s)

  def format_conversation_history_html(self,
                                       history,
                                       agent_name,
                                       email,
                                       timestamp,
                                       existing_history=None):
    gmail_note = format_note(agent_name, email, timestamp)
    if history is not None:
      history = AgentSelector.safe_ascii_string(history)
    else:
      history = ""

    decoded_history = quopri.decodestring(history).decode('utf-8')
    nested_history = f'<blockquote>{existing_history}{decoded_history}</blockquote>'
    formatted_message = f'<div>{gmail_note}</div>{nested_history}'
    return formatted_message

  def format_conversation_history_plain(self, history, agent_name, email,
                                        timestamp):
    gmail_note = format_note(agent_name, email, timestamp)
    decoded_history = quopri.decodestring(history).decode('utf-8')
    decoded_history = re.sub(r'<[^>]+>', '', decoded_history)
    lines = decoded_history.split('\n')
    nested_history = '\n'.join(
        [f'>{line}' for line in self.conversation_history.split('\n')]) + '\n'
    output_lines = [f'>{line}' for line in lines]
    return f"{gmail_note}\n{nested_history}" + '\n'.join(output_lines)

  def get_agent_names_from_content_and_emails(self, content, recipient_emails,
                                              agent_manager, gpt_model):
    agent_queue = []
    ff_agent_queue = []
    overall_order = 1  # To keep track of the overall order

    for email in recipient_emails:
      agent = agent_manager.get_agent_by_email(email)
      if agent:
        agent_queue.append((agent["id"], overall_order))
        overall_order += 1

    explicit_tags = []
    try:
      regex_pattern = re.compile(
          r"!ff\(([\w\d_]+)\)!|!<span>ff</span>\(([\w\d_]+)\)!")
      explicit_tags = regex_pattern.findall(content)
      explicit_tags = [
          tag for sublist in explicit_tags for tag in sublist if tag
      ]
    except Exception as e:
      logging.error(f"Regex Error: {e}")
      logging.error(f"Content: {content}")

    for agent_name in explicit_tags:
      agent = agent_manager.get_agent(agent_name, case_sensitive=False)
      if agent:
        ff_agent_queue.append((agent_name, overall_order))
        overall_order += 1

    print(f"Debug: agent_queue before merging: {agent_queue}")
    print(f"Debug: ff_agent_queue before merging: {ff_agent_queue}")

    agent_queue.extend(ff_agent_queue)  # Merge the lists
    agent_queue = sorted(
        agent_queue,
        key=lambda x: x[1])[:self.max_agents]  # Sort by the overall order

    return agent_queue

  def get_response_for_agent(self,
                             agent_manager,
                             gpt_model,
                             agent_name,
                             order,
                             total_order,
                             content,
                             additional_context=None):

    # Count tokens before the API call
    tokens_for_this_request = self.gpt_model.count_tokens(content)

    # Check rate limits
    self.gpt_model.check_rate_limit(tokens_for_this_request)

    content = self.replace_agent_shortcodes(content)

    timestamp = format_datetime_for_email()

    modality = 'default'
    with self.lock:
      if "!previousResponse" in content:
        content = content.replace('!previousResponse',
                                  self.last_agent_response)
        content = content.replace('!useLastResponse', '').strip()

      responses = []
      dynamic_prompt = ""
      agent = agent_manager.get_agent(agent_name, case_sensitive=False)

      if not agent:
        logging.warning(f"No agent found for name {agent_name}. Skipping...")
        return ""

      result = handle_document_short_code(content, self.openai_api_key,
                                          self.conversation_history)
      if result is None:
        print(
            "Error: agent_selector - handle_document_short_code returned None."
        )
        return False
      structured_response = result.get('structured_response')
      new_content = result.get('new_content')

      # Timestamp for formatting note
      timestamp = format_datetime_for_email()

      # Handle Summarize Type
      if result['type'] == 'summarize':
        modality = result.get('modality', 'default')
        additional_context = self.instructions['summarize'].get(
            modality, self.instructions['summarize']['default'])

        chunks = result.get('content', [])
        self.conversation_history = self.conversation_history[-16000:]

        for idx, chunk in enumerate(chunks):
          dynamic_prompt = self._create_dynamic_prompt(agent_manager,
                                                       agent_name,
                                                       order,
                                                       total_order,
                                                       structured_response,
                                                       modality=modality,
                                                       content=chunk)
          response = gpt_model.generate_response(dynamic_prompt,
                                                 chunk,
                                                 self.conversation_history,
                                                 is_summarize=False)
          responses.append(response)
        else:
          additional_context_chunk = additional_context

        formatted_response = self.format_conversation_history_html(
            response, agent_name, agent["email"], timestamp)

        self.conversation_history += f"\n{agent_name} said: {formatted_response}"

      # Handle Detail Type
      elif result['type'] == 'detail':
        chunks = result.get('content', [])
        self.conversation_history = self.conversation_history[-16000:]
        logging.info(f"Number of chunks for detail: {len(chunks)}")
        for i, c in enumerate(chunks):
          logging.info(f"Chunk {i}: {c[:50]}...")

        custom_instruction_for_detail = "THIS IS A MULTI-PART LOOP ASSEMBLING A LARGE MESSAGE IN CHUNKS. IN THIS CASE DO NOT RESPOND AS THOUGH IT IS AN EMAIL IN SPITE OF PRIOR INSTRUCTIONS, JUST PROVIDE THE CONTENT. IF ANSWERING FORM QUESTIONS ANSWER THEM THOROUGHLY AND PLACE THE QUESTION YOU ARE ANSWERING ABOVE THE ANSWER, RESTATING IT."
        responses = []

        for idx, chunk in enumerate(chunks):
          dynamic_prompt = self._create_dynamic_prompt(agent_manager,
                                                       agent_name,
                                                       order,
                                                       total_order,
                                                       additional_context,
                                                       modality=modality)

          # Add the custom instruction to the dynamic prompt
          dynamic_prompt += f" {custom_instruction_for_detail}"

          response = gpt_model.generate_response(dynamic_prompt,
                                                 chunk,
                                                 self.conversation_history,
                                                 is_summarize=False)

          formatted_response = self.format_conversation_history_html(
              response, agent_name, agent["email"], timestamp)

          self.conversation_history += f"\n{agent_name} said: {formatted_response}"

          #logging.debug(f"Appending response {idx}")
          responses.append(response)
        #logging.debug(f"Final Responses: {responses}")

      # Handle Default Type
      else:
        structured_response_json = {}
        if structured_response and structured_response.strip():
          try:
            structured_response_dict = json.loads(structured_response)
            structured_response_type = structured_response_dict.get(
                'type', None)
            structured_response_content = structured_response_dict.get(
                'structured_response', None)
            if structured_response_type and structured_response_content:
              additional_context = f"\nGuidelines for crafting response:\n{json.dumps(structured_response_content, indent=4)}"
              content = new_content
          except json.JSONDecodeError:
            logging.warning("Unable to parse structured response as JSON.")
            additional_context = structured_response

        dynamic_prompt = self._create_dynamic_prompt(agent_manager,
                                                     agent_name,
                                                     order,
                                                     total_order,
                                                     additional_context,
                                                     modality=modality)
        response = gpt_model.generate_response(dynamic_prompt,
                                               content,
                                               self.conversation_history,
                                               is_summarize=False)

        responses.append(response)
        formatted_response = self.format_conversation_history_html(
            response, agent_name, agent["email"], timestamp)

        self.conversation_history += f"\n{agent_name} said: {formatted_response}"
        time.sleep(30)

      final_response = " ".join(responses)
      formatted_final_response = self.format_conversation_history_html(
          final_response, agent_name, agent["email"], timestamp)
      signature = f"\n\n- GENERATIVE AI AGENT: {agent_name}"
      formatted_final_response += signature  # Append the signature

      self.conversation_structure.setdefault("responses", []).append(
          (agent_name,
           formatted_final_response))  # Store the formatted response
      #logging.info(f"Generated response for {agent_name}: {formatted_final_response}")

      self.last_agent_response = formatted_final_response

      #print("Dynamic Prompt:", dynamic_prompt)
      #print("Content:", content)

      return final_response
