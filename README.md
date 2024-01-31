📊 A/B+E Polling System: Includes the ABE script for creating synthetic polling systems, facilitating the generation of agent profiles and responses in structured formats.

Looking for collaborators and sponsors, see contribute.md. 

supports personas and utility agents. 

Get a gut check 

Assemble a team when you can't afford 




# (@@) - ATAT - Email Client for AI Agents - 💪🏼🦾

ATAT simplifies adoption of Human-to-AI, AI-to-AI interactions over one of the largest and most important communication stacks: email. 

That means a powerful agent - or fleet of agents - can be accessed with the "fw" button or a "cc" on an email thread. ATAT enables multiplayer / mixture via email. Training new users is as simple as teaching them to fw or cc. Using MoE operations is now as simple as "@ and then @ again". 

(a.k.a. MoE for normies.)

🚀 Rapid Agent Deployment: Simplifies the rollout of a diverse fleet of AI agents, allowing for quick integration into existing email systems, significantly reducing setup time. The new agent script results in a fairly sophisticated agent with a DALLE generated profile photo, which is automatically integrated into the Agent Dashboard. 

Which is easier: deploying a new in-development chatbot across an enterprise, or adding a new email address? @@

Get all the benefits of email when testing a new AI: like archiving, traceability, security, identity management, access pathways, in-place policies, and familiarity for people of all technical experience and comfort levels. 

Your least savvy user can absolutely use the "fw" button. 

🤖 Agent-Centric Communication: ATAT is specially designed for AI agents, offering a unique platform for Human-to-AI and AI-to-AI interactions over email, a crucial communication channel. Includes automatic Agent Dashboard that displays agent descriptions and links to their email addresses. Dashboard is mobile friendly. ATAT is not built to pretend to be you or ghost compose your emails for you. 

🦾🦾 Multi-Agent Collaboration: Allows simultaneous engagement of multiple AI agents, facilitating a "mixture of experts" approach for enhanced problem-solving and decision-making. Each agent is influenced not only be an agentic profile, but a social graph of relationships that influence their decision-making. Anecdotally, this generates more realistic results in role-playing. 

🛠️ Shortcode System: Provides powerful shortcodes like !detail, !summarize, and !ff, enabling AI agents to perform complex, multi-step tasks with simple commands, and call complex chains of agents from a single email. In the roadmap, the goal is to enable shortcodes as a mecanism to enable shortcodes in emails to serve as function call operators, so average users can quickly integrate function calls into long-chain multi-part operations. The @@ shortcode allows you to reference any agent, whether they have an email alias or not, and the @@.creator shortcode enables you to embody a new agent inline from the email. 

⏰ Email is the GOAT of Slow Responses: With email as the medium, responses that take a day are acceptable, leveraging the platform's slow nature to benefit legacy hardware and provide global access to LLMs. Text streaming chatbots and real-time voice assistants are good for instant feedback; text messages are good for quick feedback; email is the best for long, slow responses that need to be archived forever and compliant with policies. 

I did a lot of market testing of bots and saw that many of the most powerful use cases of LLMs are far too slow for a chatbot, at least right now. Email is wonderfully slow. Elegantly slow. You have 24 hours of compute to get to the customer's ideal output. What will you build? 

💡 Easy Setup on Replit: Offers a straightforward setup process on Replit, making it possible to have a functional AI agent email system running in just minutes. You need to add OPENAI_API_KEY and SMTP / IMAP credentials in Secrets, but then you can use pre-baked agents to have an Agent Dashboard deployed in a minute or so. Adding a new email address, and optionally aliases on top of it, should also only take a few minutes. 

📝 PDF Reading Capability: Enables AI agents to read and interpret text from PDFs, expanding the range of document formats the agents can handle.

🎨 Dashboard uses CSS so you can customize look and feel very easily. 

⏳⚡️ TIME TRAVEL. The inspiration behind @@ - being able to summon an agent from within an email - comes from my own struggles with being on the spectrum and having a weak model for how people will feel when I say things. I've always wanted to "time travel" to see their reaction and be able to adjust if it's not good. Now I can. @@ 



# Getting Started 

ATAT is built to work out of the box on Replit. Please see contribute.md, where a request for help adapting it to GH and for local deployment is included. 

(Deploying is a bit different. Contact me for help or paid hosting. x.com/seanmcdonaldxyz)


## 1. Set Secrets
On Replit, fork the repl and add your Secrets. This example uses a popular email service. 

{
  "SMTP_SERVER": "smtp.gmail.com",
  "IMAP_SERVER": "imap.gmail.com",
  "SMTP_PORT": "587",
  "SMTP_USERNAME": "your agent email address at your domain name",
  "SMTP_PASSWORD": "for Google (TM) Workspace this is an 'app password'",
  "OPENAI_API_KEY": "sk-...
  "
}

## 2. Add Email Address / Get Credentials Aliases 
If you are using the pre-baked agents, go to agents/agents.json and add the id of each agent as an email alias to your email management system. In Google (TM) Workspace, this is called "Add Alternate Emails".

The password for Workspace has to be an 'app password' https://support.google.com/accounts/answer/185833?hl=en. 

## 3. Run 
Deployment may require additional config, but Run should work out of the gate. 

The Flask server will open the Card site showing all agents automatically on Replit. Open the Webview pane if it doesn't open automatically. 


# ⚠️ Critical:
###  Do NOT add an existing email address, as you may trigger unwanted emails being sent to senders in your history. Create a NEW ACCOUNT and only use that. 

(If you want to use an existing dev or sandbox account, run thread-reconciler.py in /tools to index processed_threads.json.)


# Features 
AI-Focused Email Client: Tailored specifically for AI agents, enhancing their communication capabilities and availability to do real work with nothing more than a "fw" or "cc". 

Email Addresses for AI Agents: Enable dozens of agents through a single new email address using email aliases. Nothing more than IMAP / SMTP required.* Keep archives of all conversations, and secure AI by boxing it into your existing email security infrastructure. 

Automated Agent Management: Manage multiple AI personas effortlessly. Once the client is running, it can handle a queue of messages, or sleep and check every 10 minutes for new messages. 

Advanced Shortcode System: Empower your AI agents with unique, powerful shortcodes for complex tasks. Run multi-chunk API calls with !detail! request part one !split! request part two !detail!. See Shortcode section for details. 

Agents can read PDFs but text only. 


# 🦾 NEW AGENT 
new_agent.py in /agents will create new agents from the content and naming instructions in the folder of text files, /new_agent_files. This script allows you to add new agents to your synthetic polling system by providing a text description. It leverages the OpenAI GPT model to generate detailed personas based on the provided information. The generated personas are then added to the list of agents for polling. This script also includes functionality to generate images using DALL-E for the agents and save them for display on the HTML page.

To provide background on agents and iterate through bulk agent creation, the text files containing agent descriptions in a folder named new_agent_files control the process. Each text file should contain the agent's name and a description. Images associated with the new agents will be generated using DALL-E and saved in the pics folder within the project directory.

📝 Text File Format for New Agents:
To add new agents, follow this simple file structure in new_agent_files:

First Line: Agent Name
Rest of the Document: In-depth agent description


# 🎩 A/B+E ("ABE") 
ABE Script: Synthesize polling systems with JSON and HTML outputs for agent profiles and a static html page accessible via the flask app. 

This script is designed to create a synthetic polling system using the OpenAI GPT model to generate responses to a set of questions. The generated responses are saved in a structured JSON format, and a static HTML page is created to display the agent profiles along with their answers. Additionally, this script copies images associated with the agents to a local folder for display on the HTML page.

ABE runs through all the agents by default. 


# 🎩 CARDS 
cards.py is a simple flask server that reads agents.json to generate a dashboard of all the agents with links to their email addresses for easy access. 


# Shortcode Details 

## Shortcode Functionalities:
The shortcode.py module in the Atat system introduces several advanced functionalities to enhance the processing of email content. These functionalities are triggered through specific shortcodes embedded in the email text. Here's an overview of the available shortcodes:

## @@ - Engage an agent from inline 

Functionality: The @@ shortcode allows for the simultaneous dispatch of emails to multiple agents, effectively creating a hybrid multi-agent model. This is particularly useful in scenarios where a collaborative response from different personas is required.

Usage: Embed @@(agent name) or @@.creator(Embody and agent who...) in the email content, followed by agent identifiers. The system interprets this as a command to engage multiple agents in the email response process.

NOTE: "Embody" must be present. 

## @@ Creator:

Functionality: This shortcode dynamically generates a new agent in real time. It's a powerful tool for on-the-fly customization, allowing the system to adapt and create new personas based on evolving conversation needs.

Usage: Use @@.creator(Embody an agent...) followed by persona specifications or modification instructions. The system then processes these instructions to instantiate a new agent persona. For now "Embody" must be present for creator to work. 

## Detail:

Functionality: The Detail shortcode is used to chunk API calls for long-form content. It ensures that large blocks of text are broken down into more manageable segments, facilitating efficient processing and response generation.

Usage: Enclose the long-form content within !detail_start! and !detail_stop!. The system will automatically chunk the content between these markers.

## Summarize:

Functionality: Summarize enables the condensation of verbose content into a concise summary. It's equipped with modifiers defined in its instructions dynamics, allowing for customization of the summary output based on specific needs.

Usage: The shortcode !summarize! triggers this functionality. Modifiers can be added to tailor the summary's focus, length, and style.

### Modifiers:

### Explanation: Modifiers are additional instructions that can be appended to shortcodes like Summarize to further refine the output. They dictate the system's approach in processing the content, such as emphasizing certain aspects over others or adjusting the verbosity of the response.
 
### Examples: Modifiers like !summarize.json!, !summarize.marketing!, and !summarize.budget! instruct the system to format the summarized content in a specific way, be it JSON structure, marketing-oriented language, or budget format.



# 📜 License
This project is proudly under the MIT License. Feel free to adapt, use, and share it in your AI endeavors.



