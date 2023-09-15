import re
import time
import json
import os
import threading
import logging
from shortcode import handle_document_short_code


class AgentSelector:

  def __init__(self, max_agents=12):
    self.lock = threading.Lock()
    self.openai_api_key = os.environ['OPENAI_API_KEY']
    self.max_agents = max_agents
    self.conversation_structure = {}
    self.conversation_history = ""
    self.invoked_agents = {}

  def reset_for_new_thread(self):
    self.invoked_agents.clear()
    self.conversation_structure = {}
    self.conversation_history = ""

  def _create_dynamic_prompt(self,
                             agent_manager,
                             agent_name,
                             order,
                             total_order,
                             structured_response=None):
    order_explanation = ", ".join(
        [resp[0] for resp in self.conversation_structure.get("responses", [])])
    order_context = f"You are role-playing as the {agent_name}. This is the {order}th response in a conversation with {total_order} interactions. The agent sequence is: '{order_explanation}'."
    persona = agent_manager.get_agent_persona(agent_name)
    persona_context = f"You are {agent_name}. {persona}" if persona else f"You are {agent_name}."

    instructions = (
        f"{order_context}. "
        "You are a helpful assistant tasked with facilitating a meaningful conversation. "
        "Adhere to the guidelines and structure provided to you. "
        "Engage in a manner that is respectful and considerate, "
        "keeping in mind the needs and expectations of the recipients. "
        "Remember to maintain a balance between creativity and formality. "
        "As an AI, always disclose your nature and ensure to provide detailed and substantial responses."
        "Avoid referencing past threads and always prioritize the safety and privacy of personal data."
        "The user knows you are an AI developed by OpenAI, and does not need to be told."
    )

    if structured_response:
      instructions += (
          "\n\nIMPORTANT: Your response must strictly adhere to the following "
          "structure/information architecture. Please ensure to comply fully "
          "The user knows you are an AI developed by OpenAI, and does not need to be told."
          "and completely in all cases: ")
      instructions += f"\n\n=== STRUCTURED RESPONSE GUIDELINES ===\n{structured_response}\n=== END OF GUIDELINES ==="

    return f"{persona_context}. {instructions}. Act as this agent:"

  def get_agent_names_from_content_and_emails(self, content, recipient_emails,
                                              agent_manager, gpt_model):
    # Step 1: Handle the "style" shortcode first
    structured_response, new_content = handle_document_short_code(
        content, self.openai_api_key, self.conversation_history
    )  # Adjusted to unpack two values instead of three

    structured_response_json = json.dumps(
        structured_response) if structured_response else None

    logging.debug(
        f"Structured response before parsing: {structured_response_json}")

    if structured_response and structured_response.get('type') == 'detail':
      logging.debug(
          "Structured response equals 'detail', handling accordingly.")
      responses = []
      chunks = structured_response.get('content', [])

      for chunk in chunks:
        dynamic_prompt = self._create_dynamic_prompt(agent_manager, agent_name,
                                                     order, total_order,
                                                     additional_context)
        response = gpt_model.generate_response(dynamic_prompt, chunk,
                                               self.conversation_history)
        responses.append(response)
      final_response = " ".join(responses)
      content = final_response

    print(f"Structured response generated: {structured_response_json}")
    self.conversation_history += f"\nStructured Response: {structured_response_json}"

    # Extract agents from recipient emails:
    agent_queue = []
    for email in recipient_emails:
      agent = agent_manager.get_agent_by_email(email)
      if agent:
        agent_queue.append((agent["id"], len(agent_queue) + 1))

    # Check for explicit tags in content
    print(f"Content: {content}")
    try:
      explicit_tags = re.findall(r"!ff\((\w+)\)(?:!(\d+))?", content)
      explicit_tags = [(name, num) for name, num in explicit_tags
                       if name.lower() != "style".lower()]
      logging.debug(f"Extracted explicit tags: {explicit_tags}")
    except Exception as e:
      logging.error(f"Regex Error: {e}")
      logging.error(f"Content: {content}")

    if explicit_tags:
      agent_queue = []
      default_order = 1
      for match in explicit_tags:
        if len(match) != 2:
          logging.warning(f"Skipping invalid explicit tag: {match}")
          continue
        agent_name, order = match

        agent = agent_manager.get_agent(agent_name, case_sensitive=False)
        if agent:
          if order:
            order = int(order)
            agent_queue.append((agent_name, order))
          else:
            if agent_name in self.invoked_agents:
              print(f"{agent_name} is invoked. Generating a response...")
            else:
              self.invoked_agents[agent_name] = 1
            agent_queue.append((agent_name, default_order))
            default_order += 1

    agent_queue = sorted(agent_queue, key=lambda x: x[1])[:self.max_agents]
    logging.debug(f"Explicit tags: {explicit_tags}")

    logging.debug(f"Final agent queue: {agent_queue}")

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
      dynamic_prompt = ""
      agent = agent_manager.get_agent(agent_name, case_sensitive=False)

      if not agent:
        logging.warning(f"No agent found for name {agent_name}. Skipping...")
        return ""

      logging.debug(f"Content before parsing: {content}")

      structured_response, new_content, _ = handle_document_short_code(
          content, self.openai_api_key, self.conversation_history
)

      logging.debug("Checking if structured_response equals 'detail'")

      print(type(structured_response))
      print(structured_response)

      if structured_response == 'detail':
        logging.debug(
            "Structured response equals 'detail', handling accordingly.")
        responses = []
        chunks = structured_response.get('content', [])

        for chunk in chunks:
          dynamic_prompt = self._create_dynamic_prompt(agent_manager,
                                                       agent_name, order,
                                                       total_order,
                                                       additional_context)
          response = gpt_model.generate_response(dynamic_prompt, chunk,
                                                 self.conversation_history)
          responses.append(response)
        final_response = " ".join(responses)
        content = final_response
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

        dynamic_prompt = self._create_dynamic_prompt(agent_manager, agent_name,
                                                     order, total_order,
                                                     additional_context)
        content = gpt_model.generate_response(dynamic_prompt, content,
                                              self.conversation_history)

      signature = f"\n\n- GENERATIVE AI AGENT: {agent_name}"
      content += signature

      self.conversation_structure.setdefault("responses", []).append(
          (agent_name, content))
      self.conversation_history += f"\n{agent_name} said: {content}"

      time.sleep(30)
      logging.info(f"Generated response for {agent_name}: {content}")
      logging.debug(f"Structured response type: {type(structured_response)}")
      logging.debug(f"Structured response content: {structured_response}")

      return content
