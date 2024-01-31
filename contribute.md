# OpenAI SDK 1.0 Update
Update the application to leverage OpenAI SDK version 1.0.


# Big Picture 
Refactor gpt.py and new_agent.py for compatibility with OpenAI SDK 1.0, incorporating function calling and instructor logic. Update agents to integrate with Assistants. 

Engage community feedback for a structured class-based refactor, including robust testing and database integration. Simultaneously refactor to be properly pythonic, smarter class structure, proper docstrings and comments; remove early-stage solo developer cruft. 

Develop a robust email constructor to handle various client types, history management, and CSS. Overhaul email formatting and structure to address issues with quoted printable, Gmail quotes, divs, and email construction loops. 

Integrate with LLAMA and other models, model selection per agent. Local model fork for a "slowcal" (slow and local) AI model.

Incorporate comprehensive testing in every method/function.

Progressive/regressive inbox checking system based on activity levels. Implement adaptive rate limiting based on the model type and agent-specific API settings, including temperature and max tokens.

Add security / Auth / passphrases in email to ensure only desired user can utilie functionality. Also time-based / temporary agents. 

Token / credit counting regime. 


### API Specific 
Pass custom LLM settings for each API call based on agent record details, e.g. add custom temp, max_tokens, etc. to each agent record; and write shortcode to control custom LLM controls through shortcode. 

Create API so other apps can send, receive, and control multi-agent emails, e.g. voice-to-email. "Send me an email that says..." Also get agent details from an API. 


# Onboarding 
Revise onboarding to include company name capture, shaping agent profiles around company-specific user configurations. Modify onboarding so the "semantic-life.com" domain name is replaced by whatever the user chooses, including new_agents.py. 


# Smaller Functionality 
Implement automated emails for daily briefs, follow-ups, and task list management.

Enhance agent context awareness and prevent duplicate/triplicate responses, especially in detailed responses.

Enhance context and date awareness, incorporating news update functionalities.

Enhance thread reconciliation and introduce unit testing scripts.

Add awareness of sender and masked email to dynamic_prompt. 

Integrate ABE as a shortcode/function call within the system.

Adapt the system for GitHub collabortion from Replit development. 

Enhance shortcode detection as an agent operation, transitioning from regex to function calls. 

Improve thread_reconciler.py for self-healing data storage, transitioning from JSON to a database system.

Change agent rendering to a front-end workflow rather than folder of text files. In the short term, check to see if all text files are "rendered" rather than current check which is if agents.json is empty. For now you can manually run new_agent.py to add more agents with new / updated files, but watch out for duplicates in agents.json. 

Fix agents.json relationships rendering / cheap trick to clean up inconsistent output. Should be formatted with instructor / function calling. 

Integrate AI agents with the ability to run ABE and other advanced tools.

# HTML in Email and CSS in Flask 

Resolve issues arising when more than one agent is included in CC or @@ fields.

Address and fix issues in CSS Grid design.

Click for profiles for each agent in the Flask app and implement authentication for private access.

Streamline onboarding through the Flask app.

Move configuration, agent creation, and other functionalities to the Flask web interface with user feedback indicators.

# Bug Fixes and Enhancements

Address looping issues in ff agents and discrepancies between embody vs. creator.

Rectify issues with ff creator not functioning as expected.

Fix inconsistencies in summarize.json and consider function calling for better performance.

Improve shortcode detection and repair incorrect usage through intermediary LLM rather than relying on regex.
