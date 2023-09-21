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
    self.last_agent_response = ""

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
    persona_context = f"You are {agent_name} with this persona: {persona}" if persona else f"You are {agent_name}."

    general_instructions = (
        f"{order_context} You are a helpful assistant tasked with facilitating a meaningful conversation. "
        "Adhere to the guidelines and structure provided to you. "
        "Engage in a manner that is respectful and considerate, keeping in mind the needs and expectations of the recipients. "
        "Remember to maintain a balance between creativity and formality. "
        "As an AI, always disclose your nature and ensure to provide detailed and substantial responses. "
        "Stay on topic and avoid introducing unrelated information. If the user's query is a question, ensure to provide a clear and direct answer. "
        "Ensure your responses are well-formatted and avoid regurgitating the user's instructions verbatim. "
        "Avoid referencing past threads and always prioritize the safety and privacy of personal data. "
        "Do not mention people, synthetic agents, or others who are not in the current email thread unless expressly mentioned. "
        "The user knows you are an AI developed by OpenAI and does not need to be told."
    )

    instructions = general_instructions

    if structured_response:
      instructions += (
          "\n\nIMPORTANT: Your response must strictly adhere to the following "
          "structure/information architecture. Please ensure to comply fully "
          "and completely in all cases: ")
      instructions += f"\n\n=== STRUCTURED RESPONSE GUIDELINES ===\n{structured_response}\n=== END OF GUIDELINES ==="

    return f"{persona_context}. {instructions}. Now please dutifully act as that agent in that context:"

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

    responses = []
    with self.lock:

      # Check if the !previousResponse keyword exists
      if "!previousResponse" in content:
        # If it exists, replace it with the last agent's response
        content = content.replace('!previousResponse',
                                  self.last_agent_response)
        content = content.replace('!useLastResponse', '').strip()

    responses = []
    dynamic_prompt = ""
    agent = agent_manager.get_agent(agent_name, case_sensitive=False)

    if not agent:
      logging.warning(f"No agent found for name {agent_name}. Skipping...")
      return ""

    logging.debug(f"Content before parsing: {content}")

    result = handle_document_short_code(content, self.openai_api_key,
                                        self.conversation_history)
    if result is None:
      print(
          "Error: agent_selector - handle_document_short_code returned None.")
      return False

    structured_response = result.get('structured_response')
    new_content = result.get('new_content')

    modality_instructions = None
    if result['type'] == 'summarize':
      modality = result.get('modality')
      if modality == "json":
        additional_context = (
            "You are a SUMMARIZER agent. You summarize into data structures. You summarize content into JSON and JSON only. You make an appropriate JSON structure and populate it with requisite information."
            "Please provide a JSON-only response. Try to be consistent in using JSON, but not at the cost of clarity of schema and ontology. Now summarize this as JSON without losing information and key facts and facets:"
        )
      elif modality == "meeting":
        additional_context = (
            "You are tasked with summarizing a meeting agenda. "
            "Highlight the key points and main topics discussed.")
      # ... (other modalities can be added similarly)
      elif modality == "llminstructions":
        additional_context = (
            "You are tasked with summarizing instructions for the LLM model. "
            "Maintain clarity and precision, ensuring that the essence of the instructions is retained. "
            "Avoid redundancy and ensure that the summary is actionable. "
            "Remember, LLM instructions must be concise yet comprehensive, so prioritize essential details. "
            "Ideal formatting includes using clear, directive language and bullet points or numbered lists for steps or guidelines. "
            "Ensure that any conditions, prerequisites, or exceptions are clearly highlighted. "
            "Your goal is to provide a summarized version that an LLM user can quickly understand and act upon without losing any critical information from the original instructions."
        )

      else:
        additional_context = (
            "You are tasked with summarizing the content. "
            "Provide a concise and clear summary. Don't be so concise that you sacrifice information integrity. You are a data scientist."
        )

    if result['type'] == 'detail':
      logging.debug("Handling detail shortcode with split content.")
      chunks = result.get('content')
      if not isinstance(chunks, list):
        chunks = []

      self.conversation_history = self.conversation_history[-16000:]

      for idx, chunk in enumerate(chunks):
        additional_context_chunk = (
            f"This is part {idx + 1} of {len(chunks)} detail responses."
            "Maintain consistency and avoid redundant comments. "
            "Stay focused and avoid digressions. "
            "Answer queries clearly and directly, ensuring well-formatted responses without simply repeating instructions. "
            "For open-ended questions, provide comprehensive answers; for concise queries, be succinct. "
            "Directly address forms or applications without discussing the instructions. "
            "Remember your audience is human and desires meaningful answers. "
            "Stick to word counts; when unspecified, be verbose. "
            "Answer numerical questions precisely, e.g., provide actual budgets rather than discussing them. "
            "Avoid placeholders and always be genuinely creative. "
            "Aim for detailed, relevant content, preferring excess over scarcity. "
            "When necessary, provide justified solutions. "
            "Refrain from posing questions unless asked. "
            "Communicate with charisma and clarity. "
            "If playing an eccentric role, commit fully. "
            "For forms or applications, retain section headers, numbering, and questions above your response. "
            "For example, if asked 'Organization's Name?', answer as 'Organization's Name? \n\n ACME Corporation'."
        )

        dynamic_prompt_chunk = self._create_dynamic_prompt(
            agent_manager, agent_name, order + idx, total_order + len(chunks),
            additional_context_chunk or additional_context)

        response = gpt_model.generate_response(dynamic_prompt_chunk, chunk,
                                               self.conversation_history)
        responses.append(response)
        self.conversation_history += f"\n{agent_name} said: {response}"

    elif result['type'] == 'summarize':
      # Handling summarize shortcode with split content
      summarized_chunks = result.get('content', [])
      logging.info(
          f"Identified {len(summarized_chunks)} chunks using !summarize shortcode: {summarized_chunks}"
      )
      self.conversation_history = self.conversation_history[-16000:]

      for idx, chunk in enumerate(summarized_chunks):
        dynamic_prompt = self._create_dynamic_prompt(agent_manager, agent_name,
                                                     order, total_order,
                                                     additional_context)
        response = gpt_model.generate_response(dynamic_prompt, chunk,
                                               self.conversation_history)
        responses.append(response)
        self.conversation_history += f"\n{agent_name} said: {response}"

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

      dynamic_prompt = self._create_dynamic_prompt(
          agent_manager, agent_name, order, total_order, modality_instructions
          or additional_context)
      response = gpt_model.generate_response(dynamic_prompt, content,
                                             self.conversation_history)
      responses.append(response)
      self.conversation_history += f"\n{agent_name} said: {response}"

    final_response = " ".join(responses)
    signature = f"\n\n- GENERATIVE AI AGENT: {agent_name}"
    final_response += signature

    self.conversation_structure.setdefault("responses", []).append(
        (agent_name, final_response))
    logging.info(f"Generated response for {agent_name}: {final_response}")

    # Update the last agent's response
    self.last_agent_response = final_response
    print(
        "=== Processing entire content (not chunks) in get_response_for_agent ==="
    )
    print(f"Content (first 100 characters): {content[:100]}...")

    return final_response
