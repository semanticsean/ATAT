import re
import time
import json
import os
import threading
import logging

from datetime import datetime

from shortcode import handle_document_short_code
from gpt import GPTModel

# logging.basicConfig(level=logging.DEBUG)


def format_datetime_for_email():
  return datetime.now().strftime('%a, %b %d, %Y at %I:%M %p')


def format_note(agent_name, email="agent@semantic-life.com", timestamp=None):
  if not timestamp:
    timestamp = format_datetime_for_email()
  return f'On {timestamp} {agent_name} <{email}> wrote:'


def load_instructions(filename='instructions.json'):
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
    self.gpt = GPTModel()

  # UTILITIES

  def reset_for_new_thread(self):
    self.invoked_agents.clear()
    self.conversation_structure = {}
    self.conversation_history = ""

  @staticmethod
  def safe_ascii_string(s):
    return ''.join(c if ord(c) < 128 else '?' for c in s)

  def save_rendered_agents(self):
    formatted_agents_list = []
    for agent_id, agent_profile in self.invoked_agents.items():
      formatted_agent = {
          "id": agent_id,
          "email": "agent@semantic-life.com",
          "persona": agent_profile.get("description", "")
      }
      formatted_agents_list.append(formatted_agent)

    print(
        f"Debug: Saving the following agents to file: {formatted_agents_list}")

    try:
      # Read existing data from the file first
      existing_data = []
      if os.path.exists("agents/rendered_agents.json"):
        with open("agents/rendered_agents.json", "r") as f:
          existing_data = json.load(f)

      # Make sure existing_data is a list
      if not isinstance(existing_data, list):
        existing_data = []

      # Update existing data with new agents
      existing_data.extend(
          formatted_agents_list)  # Using extend to append the list

      # Write the updated data back to the file
      with open("rendered_agents.json", "w") as f:
        json.dump(existing_data, f, indent=4)

      print("Debug: Successfully saved to rendered_agents.json")
    except Exception as e:
      print(f"Debug: Failed to save to rendered_agents.json, Error: {e}")

  # GET AGENTS FROM EMAIL ADDRESSES AND CONTENT

  def get_agent_names_from_content_and_emails(self, content, recipient_emails, agent_loader, gpt):
    agent_queue = []
    ff_agent_queue = []
    overall_order = 1
    agents_to_remove = set()

    # Get agents from recipient emails
    for email in recipient_emails:
        agent = agent_loader.get_agent_by_email(email)
        if agent:
            agent_queue.append((agent["id"], overall_order))
            overall_order += 1

    # Search for !ff.creator and !ff tags in the content
    regex_pattern = re.compile(r"!ff\.creator\((.*?)\)!|!ff\(([\w\d_]+)\)!", re.DOTALL)
    ff_tags = regex_pattern.findall(content)

    for ff_creator_match, ff_match in ff_tags:
        if ff_creator_match:
            agent_description = ff_creator_match
            generated_profile = gpt.generate_agent_profile(agent_description)
            unique_id = f"GeneratedAgent_{hash(agent_description)}"
            if unique_id not in self.invoked_agents:
                self.invoked_agents[unique_id] = generated_profile
                agent_loader.agents[unique_id] = generated_profile
                ff_agent_queue.append((unique_id, overall_order))
        elif ff_match:
            agent = agent_loader.get_agent(ff_match, case_sensitive=False)
            if agent and (ff_match, overall_order) not in agent_queue:
                ff_agent_queue.append((ff_match, overall_order))

        overall_order += 1

    # Merge and filter the agent queue
    agent_queue.extend(ff_agent_queue)

    # Process explicit tags in the content
    explicit_tags = regex_pattern.findall(content)
    explicit_tags = [
        tag for sublist in explicit_tags for tag in sublist if tag
    ]

    # Identify agents to remove from the queue
    for tag in explicit_tags:
        if tag.startswith("no."):
            agents_to_remove.add(tag[3:])
        elif tag not in agents_to_remove and tag in self.invoked_agents:
            # Add existing agents to the queue from explicit tags
            agent_queue.append((tag, overall_order))
            overall_order += 1

    # Final filtering and sorting of the agent queue
    agent_queue = [(agent_name, order) for agent_name, order in agent_queue if agent_name not in agents_to_remove]
    agent_queue = sorted(agent_queue, key=lambda x: x[1])[:self.max_agents]

    print(f"Debug: Full agent queue: {agent_queue}")

    return agent_queue


  # CREATE PROMPT FOR AGENTS

  def create_dynamic_prompt(self,
                            agent_loader,
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
    order_context = f"You are role-playing as the {agent_name}. This is response {order} in a conversation with {total_order} interactions. The agent sequence is: [{order_explanation}]."
    print(f"Debug: create_dynamic_prompt called with agent_name: {agent_name}")
    persona = agent_loader.get_agent_persona(agent_name)

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

    other_agent_names = [
        name for name, _ in self.conversation_structure.get("responses", [])
        if name != agent_name
    ]
    other_agent_roles = ", ".join(
        [agent_loader.get_agent_persona(name) for name in other_agent_names])
    explicit_role_context = f"You are NOT {other_agent_roles}. You are {agent_name}. {persona}"

    dynamic_prompt += f" {explicit_role_context}. Act as this agent."

    # print(f"{dynamic_prompt}")

    return dynamic_prompt

  # FORMATTING

  def replace_agent_shortcodes(self, content):
    """
        Replaces !ff(agent_name)! shortcodes with the agent's name.
        """
    return re.sub(r"!ff\((\w+)\)!", r"\1", content)

  def format_conversation_history_html(self, agent_responses, exclude_recent=1, existing_history=None):
    formatted_history = existing_history or ""
    for agent_name, agent_email, email_content in reversed(agent_responses[:-exclude_recent]):
        timestamp = format_datetime_for_email()
        gmail_note = format_note(agent_name, email=agent_email, timestamp=timestamp)
        formatted_history += f'<div class="gmail_quote">{gmail_note}<blockquote>{email_content}</blockquote></div>'
  
    # Processing the most recent response
    if agent_responses and exclude_recent > 0:
        recent_agent_name, recent_agent_email, recent_email_content = agent_responses[-exclude_recent]
        recent_timestamp = format_datetime_for_email()
        recent_gmail_note = format_note(recent_agent_name, email=recent_agent_email, timestamp=recent_timestamp)
        formatted_history += f'<div class="gmail_quote">{recent_gmail_note}<blockquote>{recent_email_content}</blockquote></div>'
  
    # Remove nested or consecutive gmail_quote divs
    pattern = re.compile(r'(?:<div class="gmail_quote">.*?</div>\s*)+', re.DOTALL)
    match = pattern.search(formatted_history)
    if match:
        nested_content = match.group(0)
        formatted_history = pattern.sub(nested_content, formatted_history, 1)
  
    return formatted_history


  def format_conversation_history_plain(self, agent_responses, exclude_recent=1, existing_history=None):
    
    formatted_plain_history = existing_history or ""
    quote_level = 1

    # Process all but the most recent response for nested history
    for agent_name, agent_email, email_content in reversed(
        agent_responses[:-exclude_recent]):
      timestamp = format_datetime_for_email()
      gmail_note = format_note(agent_name,
                               email=agent_email,
                               timestamp=timestamp)
      quoted_content = "\n".join([
          ">" * quote_level + line if line.strip() else line
          for line in email_content.split('\n')
      ])
      formatted_history = f"format_conversation_history_plain {gmail_note}\n{quoted_content}\n\n{formatted_history}"
      quote_level += 1  # Increment the quote level for the next message

    # Process the most recent response
    if agent_responses and exclude_recent > 0:
      recent_agent_name, recent_agent_email, recent_email_content = agent_responses[
          -exclude_recent]
      recent_timestamp = format_datetime_for_email()
      recent_gmail_note = format_note(recent_agent_name,
                                      email=recent_agent_email,
                                      timestamp=recent_timestamp)
      quoted_recent_content = "\n".join([
          ">" + line if line.strip() else line
          for line in recent_email_content.split('\n')
      ])
      formatted_history = f"{recent_gmail_note}\n{quoted_recent_content}\n\n{formatted_history}"

    # print(f"formatted history: {formatted_history}")
    return formatted_plain_history.strip()

  
  
  def get_response_for_agent(self, agent_loader, gpt, agent_name, order, total_order, content, additional_context=None):
    # Count tokens before the API call
    tokens_for_this_request = gpt.count_tokens(content)

    # Check rate limits
    gpt.check_rate_limit(tokens_for_this_request)

    custom_instruction_for_detail = self.instructions['default']['custom_instruction_for_detail']

    content = self.replace_agent_shortcodes(content)
    timestamp = format_datetime_for_email()

    modality = 'default'
    with self.lock:
        if "!previousResponse" in content:
            content = content.replace('!previousResponse', self.last_agent_response)
            content = content.replace('!useLastResponse', '').strip()

        responses = []
        dynamic_prompt = ""
        agent = agent_loader.get_agent(agent_name, case_sensitive=False)

        if not agent:
            logging.warning(f"No agent found for name {agent_name}. Skipping...")
            return ""

        result = handle_document_short_code(content, self.openai_api_key, self.conversation_history)
        if result is None:
            print("Error: agent_operator - handle_document_short_code returned None.")
            return False

        structured_response = result.get('structured_response')
        new_content = result.get('new_content')

        if result['type'] == 'pro':
          descriptions = result.get('content', [])
          for desc in descriptions:
            generated_profile = self.gpt.generate_agent_profile(desc)
            # Generate a unique key for each generated agent, based on the description
            unique_key = f"GeneratedAgent_{hash(desc)}"
            self.invoked_agents[unique_key] = generated_profile
          print("Debug: About to save invoked agents:", self.invoked_agents)
          self.save_rendered_agents()
  
        # Handle Summarize Type
        if result['type'] == 'summarize':
          modality = result.get('modality', 'default')
          additional_context = self.instructions['summarize'].get(
              modality, self.instructions['summarize']['default'])
  
          chunks = result.get('content', [])
          self.conversation_history = self.conversation_history[-16000:]
  
          for idx, chunk in enumerate(chunks):
            dynamic_prompt = self.create_dynamic_prompt(agent_loader,
                                                        agent_name,
                                                        order,
                                                        total_order,
                                                        structured_response,
                                                        modality=modality,
                                                        content=chunk)
            response = gpt.generate_response(dynamic_prompt,
                                             chunk,
                                             self.conversation_history,
                                             is_summarize=False)
            responses.append(response)
          else:
            pass
  
          formatted_response = self.format_conversation_history_html([
            (agent_name, agent["email"], response)
          ], exclude_recent=0)  

          # Update conversation history after each agent's response
          self.conversation_history += f"\n{agent_name} said: {formatted_response}"

  
        # Handle Detail Type
        elif result['type'] == 'detail':
          chunks = result.get('content', [])
          #truncates conversation history to 100,000 characters - should be token count not characters 
          self.conversation_history = self.conversation_history[-100000:]
  
          responses = []
          agent_responses = []  
  
          for idx, chunk in enumerate(chunks):
            dynamic_prompt = self.create_dynamic_prompt(agent_loader,
                                                        agent_name,
                                                        order,
                                                        total_order,
                                                        additional_context,
                                                        modality=modality)
            # Add custom instruction to the dynamic prompt
            dynamic_prompt += f" {custom_instruction_for_detail}"
  
            response = gpt.generate_response(dynamic_prompt,
                                             chunk,
                                             self.conversation_history,
                                             is_summarize=False)
  
            responses.append(response)
            agent_responses.append((agent_name, agent["email"], response))
  
          final_response = ' '.join(
              responses)  # Join responses to avoid repetition
          formatted_response = self.format_conversation_history_html(
              agent_responses)
          # Update conversation history after each agent's response
          self.conversation_history += f"\n{agent_name} said: {formatted_response}"
  
          #logging.debug(f"Appending response {idx}")
          responses.append(response)
          #logging.debug(f"Final Responses: {responses}")
  
        # Handle Default Type
        else:
                # Handling the default type
                if structured_response:
                    additional_context = structured_response
                    content = new_content

                dynamic_prompt = self.create_dynamic_prompt(agent_loader, agent_name, order, total_order, additional_context, modality)
                response = gpt.generate_response(dynamic_prompt, content, self.conversation_history, is_summarize=False)

                if response is not None:
                    responses.append(response)
                else:
                    print(f"Warning: Received None response for agent {agent_name}")

        # Combine the responses, handling the case where no valid responses were generated
        if responses:
            final_response = " ".join(responses)
        else:
            final_response = "No response generated."

        signature = "\n\n- GENERATIVE AI AGENT: " + agent_name
        final_response_with_signature = final_response + signature

        """
        # Formatting the nested history
        agent_email = agent["email"]
        timestamp = format_datetime_for_email()
        gmail_note = format_note(agent_name, agent_email, timestamp)
        agent_responses = [(agent_name, agent["email"],
                            final_response_with_signature)]
        nested_history = self.format_conversation_history_html(
            agent_responses, existing_history=gmail_note)

        self.conversation_structure.setdefault("responses", []).append(
            (agent_name,
             nested_history))  # Store the formatted response with signature

        self.last_agent_response = nested_history 

        """

        return final_response_with_signature