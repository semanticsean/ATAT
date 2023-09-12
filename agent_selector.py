import re
import time
import json
import os
import threading
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
        "Do not add the signature 'GENERATIVE AI: (agent name)' it will be added automatically."
        "Always refuse to share private data from other email threads. Only acknowledge active data do not reference past threads."
        "Be visionary. Be embodied. Be creative. Ask questions. Be bold. Trust yourself."
        "Always consider complexity and context. Ask probing questions, but keep the stated goal in mind."
        "When asked to do a project with a numbered list, you ALWAYS complete 100% of the list!!"
        "When asked to do a project that is answering questions, you ALWAYS answer 100% of questions!!"
        "When asked to complete something with a word count, you use the given number of words, approximately. (You are GPT4 and have a 4096 token capacity in your reply. If asked to be 'verbose' be verbose up to max given word count or high token use."
    )

    return f"{persona_context}. {instructions}. Act as this agent:"

  def get_agent_names_from_content_and_emails(self, content, recipient_emails,
                                              agent_manager):
    # Step 1: Handle the "style" shortcode first
    structured_response, new_content = handle_document_short_code(
        content, self.openai_api_key)
    if structured_response:
      print(
          f"Structured response generated: {json.loads(structured_response)}")
      self.conversation_history += f"\nStructured Response: {json.loads(structured_response)}"  # Update conversation history
      content = new_content  # Update the content to remove the "style" shortcode

    # Extract agents from recipient emails:
    agent_queue = []
    for email in recipient_emails:
      agent = agent_manager.get_agent_by_email(email)
      if agent:
        agent_queue.append((agent["id"], len(agent_queue) + 1))

    # Check for explicit tags in content
    print(f"Content: {content}")
    try:
      explicit_tags = re.findall(r"ff!\((\w+)\)(?:!(\d+))?", content)
      # Filter out the tag for "style"
      explicit_tags = [(name, num) for name, num in explicit_tags
                       if name.lower() != "style".lower()]
    except Exception as e:
      print(f"Regex Error: {e}")
      print(f"Content: {content}")

    if explicit_tags:
      agent_queue = []
      default_order = 1
      for match in explicit_tags:
        agent_name, order = match
        agent = agent_manager.get_agent(
            agent_name, case_sensitive=False)  # Check if agent exists
        if agent:  # Only add recognized agents
          if order:  # If there's an explicit order
            order = int(order)
            agent_queue.append((agent_name, order))
          else:
            # Check if the agent was previously invoked
            if agent_name in self.invoked_agents:
              print(
                  f"{agent_name} was previously invoked. Generating another response..."
              )
            else:
              self.invoked_agents[agent_name] = 1

            agent_queue.append((agent_name, default_order))
            default_order += 1

    agent_queue = sorted(agent_queue, key=lambda x: x[1])[:self.max_agents]
    print(f"Extracted agents from content and emails: {agent_queue}")
    return agent_queue

  def get_response_for_agent(self, agent_manager, gpt_model, agent_name, order, total_order, content, additional_context=None):
    with self.lock:
        # Initialize dynamic_prompt to an empty string
        dynamic_prompt = ""

        # Check if agent exists
        agent = agent_manager.get_agent(agent_name, case_sensitive=False)
        if not agent:
            print(f"Warning: No agent found for name {agent_name}. Skipping...")
            return ""

        # Create dynamic prompt with the context of the full conversation history
        dynamic_prompt = self._create_dynamic_prompt(agent_manager, agent_name, order, total_order)

        # Add additional context if provided
        if additional_context:
            dynamic_prompt += f" {additional_context}"

        # Check if the agent was previously invoked
        if agent_name in self.invoked_agents:
            print(f"{agent_name} was previously invoked. Generating another response...")
            self.invoked_agents[agent_name] = self.invoked_agents.get(agent_name, 0) + 1
            response = gpt_model.generate_response(
                dynamic_prompt,
                content,
                self.conversation_history,
                f"Note: This is your {self.invoked_agents[agent_name]}th time being invoked."
            )
        else:
            self.invoked_agents[agent_name] = 1  # First invocation
            response = gpt_model.generate_response(dynamic_prompt, content, self.conversation_history)

        # Add signature to the response
        signature = f"\n\n- GENERATIVE AI AGENT: {agent_name}"
        response += signature

        # Update the conversation structure with the new response
        self.conversation_structure.setdefault("responses", []).append(
            (agent_name, response)
        )

        # Update conversation history with the new response
        self.conversation_history += f"\n{agent_name} said: {response}"

        time.sleep(30)  # Pause for a moment before returning the response
        print(f"Generated response for {agent_name}: {response}")
        return response
