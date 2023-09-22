import re
import time
import json
import os
import threading
import logging
from shortcode import handle_document_short_code


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

  def reset_for_new_thread(self):
    self.invoked_agents.clear()
    self.conversation_structure = {}
    self.conversation_history = ""

  def _create_dynamic_prompt(self,
                           agent_manager,
                           agent_name,
                           order,
                           total_order,
                           structured_response=None,
                           modality=None):  # Add modality parameter
    order_explanation = ", ".join(
        [resp[0] for resp in self.conversation_structure.get("responses", [])])
    order_context = f"You are role-playing as the {agent_name}. This is the {order}th response in a conversation with {total_order} interactions. The agent sequence is: '{order_explanation}'."
    persona = agent_manager.get_agent_persona(agent_name)
    persona_context = f"You are {agent_name}. {persona}" if persona else f"You are {agent_name}."

    instructions = self.instructions['default']['main_instructions']

    if structured_response:
        instructions += self.instructions['default']['structured_response_guidelines']
        instructions += f"\n\n=== STRUCTURED RESPONSE GUIDELINES ===\n{structured_response}\n=== END OF GUIDELINES ==="

    # Check for modality-specific instructions
    if modality and modality in self.instructions['summarize']:
        instructions = self.instructions['summarize'][modality]  # Override the instruction with modality-specific one

    return f"{persona_context}. {instructions}. Act as this agent:"


  def get_agent_names_from_content_and_emails(self, content, recipient_emails,
                                              agent_manager, gpt_model):
    agent_queue = []

    for email in recipient_emails:
      agent = agent_manager.get_agent_by_email(email)
      if agent:
        agent_queue.append((agent["id"], len(agent_queue) + 1))

    explicit_tags = []
    try:
      explicit_tags = re.findall(r"!ff\((\w+)\)(?:!(\d+))?",
                                 content) + re.findall(
                                     r"!\((\w+)\)(?:!(\d+))?", content)
      explicit_tags = [(name, int(num) if num else None)
                       for name, num in explicit_tags
                       if name.lower() != "style"]
    except Exception as e:
      logging.error(f"Regex Error: {e}")
      logging.error(f"Content: {content}")

    for agent_name, order in explicit_tags:
      agent = agent_manager.get_agent(agent_name, case_sensitive=False)
      if agent:
        existing_entry = next(
            ((name, ord) for name, ord in agent_queue if name == agent_name),
            None)
        if existing_entry:
          agent_queue.remove(existing_entry)
        agent_queue.append(
            (agent_name, order if order is not None else len(agent_queue) + 1))

    if len(agent_queue) == 1:
      agent_queue[0] = (agent_queue[0][0], 1)
    elif not any([agent[1] for agent in agent_queue]):
      agent_queue = [(agent[0], idx + 1)
                     for idx, agent in enumerate(agent_queue)]

    agent_queue = sorted(agent_queue, key=lambda x: x[1])[:self.max_agents]

    return agent_queue

  def get_response_for_agent(self,
                           agent_manager,
                           gpt_model,
                           agent_name,
                           order,
                           total_order,
                           content,
                           additional_context=None):

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
                "Error: agent_selector - handle_document_short_code returned None.")
            return False
        structured_response = result.get('structured_response')
        new_content = result.get('new_content')

        # Handle Summarize Type
        if result['type'] == 'summarize':
            modality = result.get('modality', 'default')
            additional_context = self.instructions['summarize'].get(modality,
                                                                     self.instructions['summarize']['default'])

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

                dynamic_prompt = self._create_dynamic_prompt(agent_manager, agent_name,
                                                             order, total_order,
                                                             additional_context_chunk,
                                             modality=modality)

                response = gpt_model.generate_response(dynamic_prompt, chunk,
                                                       self.conversation_history, is_summarize=True)

                responses.append(response)
                self.conversation_history += f"\n{agent_name} said: {response}"

        # Handle Default Type
        else:
            structured_response_json = {}
            if structured_response and structured_response.strip():
                try:
                    structured_response_dict = json.loads(structured_response)
                    structured_response_type = structured_response_dict.get('type', None)
                    structured_response_content = structured_response_dict.get(
                        'structured_response', None)
                    if structured_response_type and structured_response_content:
                        additional_context = f"\nGuidelines for crafting response:\n{json.dumps(structured_response_content, indent=4)}"
                        content = new_content
                except json.JSONDecodeError:
                    logging.warning("Unable to parse structured response as JSON.")
                    additional_context = structured_response

            dynamic_prompt = self._create_dynamic_prompt(agent_manager, agent_name,
                                                         order, total_order,
                                                         additional_context,
                                             modality=modality)
            response = gpt_model.generate_response(dynamic_prompt, content,
                                                   self.conversation_history, is_summarize=True)
            responses.append(response)
            self.conversation_history += f"\n{agent_name} said: {response}"

        

        final_response = " ".join(responses)
        signature = f"\n\n- GENERATIVE AI AGENT: {agent_name}"
        final_response += signature

        self.conversation_structure.setdefault("responses", []).append(
            (agent_name, final_response))
        logging.info(f"Generated response for {agent_name}: {final_response}")

        self.last_agent_response = final_response

        return final_response
