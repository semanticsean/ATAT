import re
import time
import json
import os
import threading
import logging
from shortcode import handle_document_short_code
from gpt_model import GPTModel


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
                             content=None):  # Added content parameter

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
      instructions = self.instructions['summarize'][
          modality]  # Override the instruction with modality-specific one

    # Creating the dynamic prompt in the specified order
    dynamic_prompt = f"{order_context}"

    # Inserting the email content
    if content:
      dynamic_prompt += f"YOU ARE ON AN EMAIL THREAD. YOU ONLY RESPOND AS THE APPROPRIATE AGENT. THE EMAIL YOU NEED TO RESPOND TO IS AS FOLLOWS: '''{content}'''."

    dynamic_prompt += f" {instructions}. {persona_context}. Act as this agent."

    return dynamic_prompt

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

      # Handle Summarize Type
      if result['type'] == 'summarize':
        modality = result.get('modality', 'default')
        additional_context = self.instructions['summarize'].get(
            modality, self.instructions['summarize']['default'])

        chunks = result.get('content', [])
        self.conversation_history = self.conversation_history[-16000:]
        logging.info(f"Number of chunks: {len(chunks)}")
        for i, c in enumerate(chunks):
          logging.info(f"Chunk {i}: {c[:50]}...")

        for idx, chunk in enumerate(chunks):
          if modality in self.instructions['summarize']:
            additional_context_chunk = self.instructions['summarize'][
                'additional_context_chunk'].format(part_number=idx + 1,
                                                   total_parts=len(chunks))
          else:
            additional_context_chunk = additional_context

          dynamic_prompt = self._create_dynamic_prompt(
              agent_manager,
              agent_name,
              order,
              total_order,
              additional_context_chunk,
              modality=modality)

          response = gpt_model.generate_response(dynamic_prompt,
                                                 chunk,
                                                 self.conversation_history,
                                                 is_summarize=True)

          responses.append(response)
          self.conversation_history += f"\n{agent_name} said: {response}"

      # Handle Detail Type
      elif result['type'] == 'detail':
        chunks = result.get('content', [])
        self.conversation_history = self.conversation_history[-16000:]
        logging.info(f"Number of chunks for detail: {len(chunks)}")
        for i, c in enumerate(chunks):
          logging.info(f"Chunk {i}: {c[:50]}...")

        for idx, chunk in enumerate(chunks):
          dynamic_prompt = self._create_dynamic_prompt(agent_manager,
                                                       agent_name,
                                                       order,
                                                       total_order,
                                                       additional_context,
                                                       modality=modality)

          response = gpt_model.generate_response(dynamic_prompt,
                                                 chunk,
                                                 self.conversation_history,
                                                 is_summarize=False)

          responses.append(response)
          self.conversation_history += f"\n{agent_name} said: {response}"

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
        self.conversation_history += f"\n{agent_name} said: {response}"
        time.sleep(60)

      final_response = " ".join(responses)
      signature = f"\n\n- GENERATIVE AI AGENT: {agent_name}"
      final_response += signature

      self.conversation_structure.setdefault("responses", []).append(
          (agent_name, final_response))
      logging.info(f"Generated response for {agent_name}: {final_response}")

      self.last_agent_response = final_response

      print("Dynamic Prompt:", dynamic_prompt)
      print("Content:", content)

      return final_response
