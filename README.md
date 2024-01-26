# Email Server for Agents: README

add cards.py explanation 
new agent explanation 
pdf2text 
rename files / functions 


## Overview:
The system is designed to act as an email server for agents. It processes incoming emails, sends responses, and manages agents and their personas. The system leverages the OpenAI GPT model to generate dynamic responses based on agent personas. It works by using aliases. It's primarily built for Google Workspace integration for initial testing, but should be compatible with almost all clients, and has been tested with Hey.com, and privately hosted IMAP / SMTP.


## Capacitites 

1. Do very long processes (i.e. multi-step API calls) without the user sitting at a chatbot or discord / slack terminal waiting. Run 24 hour responses, or more. It's normal for an email to take a day to get back.
2. Take advantage of existing email infrastructure, security, archiving, etc.
3. Make Mixture-of-Experts coordination easy by making it an email thread -- just cc as many experts as you want to hear from.
4. Shortcodes give superpowers, in particular writing long-form multi-pass content.
5. 



# CRITICAL WARNING: DO NOT USE THIS SCRIPT ON EXISTING EMAIL INBOXES, OR YOU MAY SEND UNINTENDED EMAILS. USE ONLY ON A NEW DEDICATED ACCOUNT. 



Shortcode Functionalities:
The shortcode.py module in the Atat system introduces several advanced functionalities to enhance the processing of email content. These functionalities are triggered through specific shortcodes embedded in the email text. Here's an overview of the available shortcodes:

Fast Forward (ff):
Functionality: The Fast Forward shortcode allows for the simultaneous dispatch of emails to multiple agents, effectively creating a hybrid multi-agent model. This is particularly useful in scenarios where a collaborative response from different personas is required.
Usage: Embed !ff! in the email content, followed by agent identifiers. The system interprets this as a command to engage multiple agents in the email response process.
Fast Forward Creator:
Functionality: This shortcode dynamically generates a new agent in real time. It's a powerful tool for on-the-fly customization, allowing the system to adapt and create new personas based on evolving conversation needs.
Usage: Use !ff_creator! followed by persona specifications or modification instructions. The system then processes these instructions to instantiate a new agent persona.
Detail:
Functionality: The Detail shortcode is used to chunk API calls for long-form content. It ensures that large blocks of text are broken down into more manageable segments, facilitating efficient processing and response generation.
Usage: Enclose the long-form content within !detail_start! and !detail_stop!. The system will automatically chunk the content between these markers.
Summarize:
Functionality: Summarize enables the condensation of verbose content into a concise summary. It's equipped with modifiers defined in its instructions dynamics, allowing for customization of the summary output based on specific needs.
Usage: The shortcode !summarize! triggers this functionality. Modifiers can be added to tailor the summary's focus, length, and style.
Modifiers:
Explanation: Modifiers are additional instructions that can be appended to shortcodes like Summarize to further refine the output. They dictate the system's approach in processing the content, such as emphasizing certain aspects over others or adjusting the verbosity of the response.
Examples: Modifiers like !summarize.json!, !summarize.marketing!, and !summarize.budget! instruct the system to format the summarized content in a specific way, be it JSON structure, marketing-oriented language, or budget format.
Integration in shortcode.py:
The shortcodes are integrated into the shortcode.py module, which acts as an intermediary processor for email content. This module recognizes and interprets the shortcodes, invokes the relevant functionalities, and seamlessly integrates the outputs into the email response flow. Its design ensures that the addition of these advanced features does not disrupt the fundamental email processing and agent interaction mechanisms of the Atat system.

## Modules:

### email_client.py:
- Manages operations related to the email server.
- Connects to an IMAP server to process incoming emails.
- Sends out emails.
- Ensures connection to the IMAP server is alive and handles errors.

### agent_operator.py:
- Handles agent selection and dynamic prompt creation.
- Manages conversation history and structure.

### shortcode.py:
- Provides functionality to handle specific shortcodes within email content.
- Splits content into manageable chunks based on character limits or sentence boundaries.

### newagent.py:
- Provides tools to create a new agent based on an existing agent's persona.

### gpt.py:
- Interfaces with the OpenAI GPT model to generate responses.
- Constructs API payload, sends it to OpenAI, and handles possible errors.

### doc_gen.py:
- Generates structured responses, possibly in JSON format, based on shortcode content.

### agents.json:
- Contains definitions for different agents, including their unique IDs, emails, and persona descriptions.

### agent_loader.py:
- Manages and retrieves details about agents.
- Offers tools for agent lookup, persona retrieval, and email verification.

### main.py:
- Orchestrates the entire system by loading the necessary modules and starting the email server.

## How to Run:
To execute the system, run the `main.py` script, which initializes the agent manager, GPT model, and email server, then starts the email server to begin processing emails.

## email_client.py Overview:
**Purpose:** This module appears to handle the operations related to an email client, including connecting to an IMAP server, processing incoming emails, and sending emails.

**Key Functions:**
- `__init__`: Initializes the email server with necessary credentials.
- `connect_to_imap_server`: Connects to the IMAP server.
- `disconnect_from_imap_server`: Disconnects from the IMAP server.
- 'process_single_email': Processes new emails from the IMAP server.
- `send_email`: Sends an email.
- 'process_new_emails' - Processes inbox
- `run_server_loop`: Runs the server loop, periodically checking for new emails and processing them.
- `check_imap_connection`: Checks if the IMAP connection is still alive.
- `load_processed_threads`: Loads already processed email threads.
- `restart_system`: Handles system restarts.

**Features:**
- **Error Handling:** There are mechanisms to handle errors, including the ability to restart the system after a failure.
- **SMTP Connection:** Uses a context manager for SMTP connections, ensuring that the SMTP server connection is always properly closed.
- **Threaded Email Processing:** Keeps track of processed email threads to avoid re-processing.
- **External Libraries:** Uses libraries such as imaplib, smtplib, and email for email processing.


## agent_operator.py Overview:
**Purpose:** This module manages agent selection, handling of conversations, and dynamic prompt creation for the AI agents.

**Key Classes & Methods:**
- `AgentSelector`:
  - `__init__`: Initializes the AgentSelector with a maximum number of agents and other settings.
  - `reset_for_new_thread`: Resets the invoked agents and conversation history.
  - `_create_dynamic_prompt`: Creates a dynamic prompt for the agents based on the context.
  - `_invoke_agent`: Invokes an agent to generate a response for a given content.
  - `_invoke_doc_generation_agent`: Invokes an agent to generate a document based on the given content and structure.
  - `_fetch_agent`: Fetches an agent for the conversation.
  - `handle_conversation_turn`: Handles a turn in the conversation, invoking the relevant agents and returning their responses.
  - `handle_document_short_code`: A method to handle document shortcode.

**Features:**
- **Dynamic Prompt Creation:** Generates dynamic prompts for the agents based on the conversation's context and the agent's persona.
- **Conversation Management:** Manages the conversation history and structure, ensuring that the agents respond in a coherent and structured manner.
- **Agent Invocation:** Allows for the invocation of specific agents for generating responses or documents.
- **Structured Response Handling:** Provides support for structured responses, allowing the agents to generate responses based on specific guidelines or structures.
- **External Libraries:** Uses libraries such as re, json, and threading. It also appears to leverage other modules, like shortcode.

## shortcode.py Overview:
**Purpose:** This module provides functionality to handle specific shortcodes within email content and split large content into manageable chunks.

**Key Functions:**
- `auto_split_content`: Splits the content based on a character limit and paragraph breaks.
- `handle_document_short_code`: Handles the !detail shortcode and splits the content based on the !split delimiter. It also manages the !style shortcode.
- `split_content_into_chunks`: Splits content into chunks based on sentence boundaries, ensuring that each chunk doesn't exceed a specified maximum character count.

**Features:**
- **Content Splitting:** Provides methods to split large content into smaller chunks, either based on character counts, paragraph breaks, or sentence boundaries.
- **Shortcode Handling:** Processes specific shortcodes, such as !detail and !style, and modifies the email content accordingly.
- **External Libraries:** Uses the re and json libraries. Also, it leverages the doc_gen module.


## newagent.py Overview:
**Purpose:** This module offers tools to create a new agent persona based on an existing agent's persona, given certain modification instructions.

**Key Functions:**
- `read_description`: Reads a description from either a file or directly from the provided string.
- `backup_file`: Creates a backup of a specified file.
- `restore_backup`: Restores the backup of a specified file.
- `generate_persona`: Generates a new persona description based on a base persona and modification instructions. Uses the openai API to achieve this.
- `validate_json`: Validates the JSON data of agents against a predefined schema.
- `add_new_agent`: Adds a new agent to the agents' list based on an existing agent's ID and modification instructions.

**Features:**
- **Persona Generation:** Allows for the dynamic generation of new agent personas based on modification instructions and existing personas.
- **Validation:** Validates the agents' JSON data against a predefined schema to ensure data integrity.
- **Backup & Restore:** Before making changes to the agents' list, it backs up the original file. If there's an issue with the new data, it restores from the backup.
- **External Libraries:** Uses libraries such as json, shutil, openai, and jsonschema.

## gpt.py Overview:
**Purpose:** This module provides an interface for generating responses from the GPT model by creating a payload and sending it to the OpenAI API.

**Key Classes & Methods:**
- `GPTModel`:
  - `__init__`: Initializes the GPT model with the OpenAI API key.
  - `generate_response`: Generates a response using the GPT model based on the provided dynamic prompt, content, conversation history, and any additional context or notes. This method also handles possible errors during the API call by implementing retries with exponential backoff.

**Features:**
- **Response Generation:** Allows for the generation of AI responses based on dynamic prompts and conversation history.
- **Error Handling:** Implements retries with exponential backoff in case of API errors or rate limiting.
- **Payload Creation:** Constructs the payload to be sent to the OpenAI API, ensuring that it doesn't exceed token limits and truncating the conversation history if necessary.
- **External Libraries:** Uses the openai library to interface with the OpenAI API.

## doc_gen.py Overview:
**Purpose:** This module provides tools to generate structured responses, possibly in JSON format, based on the content provided in shortcodes.

**Key Functions:**
- `gpt4_generate_structured_response`: This function interfaces with the GPT-4 API to produce a structured response based on the provided shortcode content. It constructs the appropriate payload, sends it to the OpenAI API, handles possible errors, and returns the structured response.

**Features:**
- **Structured Response Generation:** Enables the creation of structured responses, often in JSON format, based on specific content.
- **Error Handling:** Implements retries with exponential backoff in case of API errors or rate limiting.
- **Payload Creation:** Constructs the payload to be sent to the OpenAI API, ensuring that it doesn't exceed token limits and truncating content if necessary.
- **External Libraries:** Utilizes the openai library to communicate with the OpenAI API.

## agents.json Overview:
**Contents:** The `agents.json` file contains a list of agent definitions. Each agent has the following attributes:
- `id`: A unique identifier for the agent.
- `email`: An email associated with the agent.
- `persona`: A description of the agent's persona, characterizing how they should behave or respond.

**Sample Agents:**
- `eagerparent`:
  - email: eagerparent@semantic-life.com
  - persona: This agent is portrayed as a cheerful and highly intelligent parent of a private school kid who is always curious and seeking new knowledge. They are adventurous, positive, full of energy, and enthusiastic about new programs.
  
- `frictionparent`:
  - email: frictionparent@semantic-life.com
  - persona: This agent is portrayed as a drab and dour parent disappointed with the public school their student attends. They are frustrated, believe the school is over-priced, and are not satisfied with the school's performance in math and science.

## agent_loader.py Overview:
**Purpose:** This module offers tools for managing and retrieving details about different agents, such as their names, personas, and emails.

**Key Classes & Methods:**
- `AgentManager`:
  - `__init__`: Initializes the agent manager and loads the agent data.
  - `get_agent_names`: Retrieves the names (IDs) of all agents.
  - `load_agents`: Loads agent data from the agents.json file.
  - `get_agent`: Retrieves the data for a specific agent based on its ID, with an option for case-sensitive or case-insensitive lookup.
  - `is_agent_email`: Checks if a given email address belongs to any of the agents.
  - `get_agent_persona`: Retrieves the persona description of a specific agent based on its ID.
  - `get_agent_by_email`: Retrieves the agent data based on a given email address.

**Features:**
- **Agent Lookup:** Allows for the retrieval of agent data based on their ID or email.
- **Persona Retrieval:** Provides functionality to get the persona description of a specific agent.
- **Email Verification:** Can verify if a given email address belongs to any of the defined agents.

