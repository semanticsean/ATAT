import re
import time
import json
import os
from doc_gen import handle_document_pseudo_code


class AgentSelector:

  def __init__(self, max_agents=6):
    self.openai_api_key = os.environ['OPENAI_API_KEY']
    self.max_agents = max_agents
    self.conversation_structure = {}

  def _create_dynamic_prompt(self, agent_manager, agent_name, order,
                             total_order):
    order_explanation = ", ".join(
        [resp[0] for resp in self.conversation_structure.get("responses", [])])
    order_context = f"You are role-playing as the {agent_name}. This is the {order}th response in a conversation with {total_order} interactions. The agent sequence is: '{order_explanation}'."
    persona = agent_manager.get_agent_persona(agent_name)
    persona_context = f"You are {agent_name}. {persona}" if persona else f"You are {agent_name}."

    instructions = (
        f"{order_context}. "
        "Respond naturally, following the conversation's progression. If it converges, be specific. If it diverges, be creative. "
        "Initially, be formal. On further interactions, reduce formality. "
        "Adjust your responses based on your character's significance in the thread. "
        "Always remember: you are a helpful assistant. Consider the needs of every recipient and ensure fairness in your attention. "
        "You are an AI; always disclose this. "
        "Provide detailed explanations. If you're unsure, use metaphors or similes. "
        "Respect boundaries; let others answer their questions. "
        "Be honest about advantages and disadvantages. Simultaneously, express optimism and skepticism. "
        "Always consider complexity and context. Ask probing questions, but keep the stated goal in mind."
    )

    return f"{persona_context}. {instructions}. Act as this agent:"

  def get_agent_names_from_content_and_emails(self, content, recipient_emails, agent_manager):
    structured_response, new_content = handle_document_pseudo_code(content, self.openai_api_key)
    # Check for pseudo-code
    if structured_response:
        print(f"Structured response generated: {json.loads(structured_response)}")
        content = new_content

    # Extract agents from recipient emails:
    agent_queue = []
    for email in recipient_emails:
      agent = agent_manager.get_agent_by_email(email)
      if agent:
        agent_queue.append((agent["id"], len(agent_queue) + 1))

    # Check for explicit tags in content
    explicit_tags = re.findall(r"!!(\w+)(?:!(\d+))?", content)
    if explicit_tags:
      agent_queue = []
      default_order = 1
      added_agents = set()
      for match in explicit_tags:
        agent_name, order = match
        if order:  # If there's an explicit order
          order = int(order)
          agent_queue.append((agent_name, order))
        else:
          if agent_name not in added_agents:  # Add the agent only once if no explicit order
            agent_queue.append((agent_name, default_order))
            added_agents.add(agent_name)
            default_order += 1

    agent_queue = sorted(agent_queue, key=lambda x: x[1])[:self.max_agents]
    print(f"Extracted agents from content and emails: {agent_queue}")
    return agent_queue

  def get_response_for_agent(self, agent_manager, gpt_model, agent_name, order,
                             total_order, content):
    agent = agent_manager.get_agent(agent_name, case_sensitive=False)
    if not agent:
      print(f"Warning: No agent found for name {agent_name}. Skipping...")
      return None

    # Create dynamic prompt with the context of the full conversation history
    dynamic_prompt = self._create_dynamic_prompt(agent_manager, agent_name,
                                                 order, total_order)
    # Generate the response
    response = gpt_model.generate_response(dynamic_prompt, content)

    # Add signature to the response
    signature = f"\n\n- GENERATIVE AI AGENT: {agent_name}"
    response += signature

    # Update the conversation structure with the new response
    self.conversation_structure.setdefault("responses", []).append(
        (agent_name, response))

    time.sleep(30)  # Pause for a moment before returning the response
    print(f"Generated response for {agent_name}: {response}")
    return response
