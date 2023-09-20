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
            "As an AI, always disclose your nature and ensure to provide detailed and substantial responses. "
            "Stay on topic and avoid introducing unrelated information. If the user's query is a question, ensure to provide a clear and direct answer. "
            "Ensure your responses are well-formatted and avoid regurgitating the user's instructions verbatim. "
            "Avoid referencing past threads and always prioritize the safety and privacy of personal data."
            "Do not mention people, synthetic agents, or others who are not in the current email thread, unless expressly mentioned."
            "The user knows you are an AI developed by OpenAI, and does not need to be told."
        )
    
        if structured_response:
            instructions += (
                "\n\nIMPORTANT: Your response must strictly adhere to the following "
                "structure/information architecture. Please ensure to comply fully "
                "and completely in all cases: ")
            instructions += f"\n\n=== STRUCTURED RESPONSE GUIDELINES ===\n{structured_response}\n=== END OF GUIDELINES ==="
    
        return f"{persona_context}. {instructions}. Act as this agent:"
    

    def get_agent_names_from_content_and_emails(self, content, recipient_emails,
                                                agent_manager, gpt_model):
        # Extract agents from recipient emails:
        agent_queue = []
        for email in recipient_emails:
            agent = agent_manager.get_agent_by_email(email)
            if agent:
                agent_queue.append((agent["id"], len(agent_queue) + 1))

        # Check for explicit tags in content
        explicit_tags = []
        try:
            explicit_tags = re.findall(r"!ff\((\w+)\)(?:!(\d+))?", content) + \
                            re.findall(r"!\((\w+)\)(?:!(\d+))?", content)
            explicit_tags = [(name, int(num) if num else None)
                            for name, num in explicit_tags
                            if name.lower() != "style"]
        except Exception as e:
            logging.error(f"Regex Error: {e}")
            logging.error(f"Content: {content}")

        # Update the agent_queue with explicit tags if they exist
        for agent_name, order in explicit_tags:
            agent = agent_manager.get_agent(agent_name, case_sensitive=False)
            if agent:
                # If the agent is already in the queue, adjust its order
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

        # Sort the agent_queue based on the order
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
            responses = []  # List to hold responses for each split section
            dynamic_prompt = ""
            agent = agent_manager.get_agent(agent_name, case_sensitive=False)
    
            if not agent:
                logging.warning(f"No agent found for name {agent_name}. Skipping...")
                return ""
    
            logging.debug(f"Content before parsing: {content}")
    
            result = handle_document_short_code(content, self.openai_api_key,
                                                self.conversation_history)
            structured_response = result.get('structured_response')
            new_content = result.get('new_content')
    
            if result['type'] == 'detail':  # Handling the detail shortcode with split content
                logging.debug("Handling detail shortcode with split content.")
                
                chunks = result.get('content', [])
    
                # Logging the split chunks
                logging.info(f"Identified {len(chunks)} chunks using !detail and !split shortcodes: {chunks}")
                
                for idx, chunk in enumerate(chunks):
                    # Add custom note for !detail calls 
                    additional_context_chunk = (
                        f"This is part {idx + 1} of {len(chunks)} detail responses. "
                        "Ensure internal consistency and avoid introductions or redundant comments. "
                        "Stay on topic and avoid introducing unrelated information. "
                        "Provide clear and direct answers to queries. "
                        "Ensure your responses are well-formatted. "
                        "Avoid regurgitating the user's instructions verbatim. "
                        "Provide detailed and substantial responses. "
                        "If a question is open-ended, provide a verbose and robust answer, ensuring a minimum of one paragraph. "
                        "For succinct questions expecting quick answers, adjust your response length appropriately. "
                        "If there's a form or an application, directly answer or fill it out without discussing the instructions. "
                        "Always remember that the audience is human, desiring meaningful and substantial answers. "
                        "Adhere to any provided word counts; if none are given, err on the side of verbosity. "
                        "Provide precise numerical answers to specific numerical queries; for instance, if asked to create a budget, produce the budget itself rather than discussing it. "
                        "Never use placeholders or indicate that something is 'coming soon'. "
                        "When asked to be creative, be genuinely inventive. "
                        "The goal is to provide users with raw, thoughtful, on-point, and creative content that they can react to; it's preferable to produce too much content than too little. "
                        "Where appropriate, think through solutions and include justifications as part of your response. "
                        "Avoid posing questions unless specifically asked to do so. "
                        "Communicate with charisma and clarity. "
                        "If directed to perform as an eccentric agent, fully embrace that role."
                    )
                    
                    dynamic_prompt = self._create_dynamic_prompt(agent_manager,
                                                                 agent_name,
                                                                 order,
                                                                 total_order,
                                                                 additional_context_chunk or additional_context)
                    # Generate the response for this chunk
                    response = gpt_model.generate_response(dynamic_prompt, chunk, self.conversation_history)
                    responses.append(response)
                    
                    # Update conversation history for each chunk
                    self.conversation_history += f"\n{agent_name} said: {response}"
                
            else:  # Handling the content normally (without split)
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
                response = gpt_model.generate_response(dynamic_prompt, content,
                                                       self.conversation_history)
                responses.append(response)
                self.conversation_history += f"\n{agent_name} said: {response}"
    
            # Joining all the responses together
            final_response = " ".join(responses)
    
            signature = f"\n\n- GENERATIVE AI AGENT: {agent_name}"
            final_response += signature
    
            self.conversation_structure.setdefault("responses", []).append(
                (agent_name, final_response))
    
            logging.info(f"Generated response for {agent_name}: {final_response}")
    
            return final_response
    