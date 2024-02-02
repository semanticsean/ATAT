# Collaborators / Co-Owner 

I'm looking for collaborators, sponsors, and potentially, a co-owner of the project. 😁

Ideally someone with vast experience in email clients and the nuances and countless edge cases therein. 😬😭

Statista estimates 347.3 Billion emails were sent last year. Let's enable AI agents to increase the quality and capacity of email in minutes of setup, so users can have swarms of agents quickly and easily. 🤝


# Big Picture Roadmap 

Fix multiple problems with history construction including email quoting / mimetype / encoding / and multi-agent decomposition of style (and logic). Develop a robust email constructor to handle various client types, history management, and CSS. Overhaul email formatting and structure to address issues with quoted printable, Gmail quotes, divs, and email construction loops. Remove kludge from email history and conversation history formatting. 

Refactor gpt.py and new_agent.py for compatibility with OpenAI SDK 1.0, incorporating function calling and instructor logic. Update agents to integrate with Assistants. 

Make gpt.py capable of using different APIs for different agents, e.g. a LLAMA agent, a Mixtral Agent, and OpenAI agent, each defined by their agent-level config. Make parameters per-agent, and expose API call parameters as a shortcode so user can request either specific parameters or a library of humanized terms like "fast and speedy" or "max" for a multi-pass MoE with a judge and editor who force feedback and refinement loops. 

Integrate a watermarking system. 

Build a community and get feedback for a plan to do a large-scale refactor, including robust testing and database integration. Simultaneously refactor to be properly pythonic, class structures, proper docstrings and comments; remove early-stage solo developer cruft and move from print statements to logging, centralize logging. 

Build a synthetic email server that has testing data persistently available for full-system and feature testing with red light / green light high-level test to ensure system integrity with changes. Once this is done the code can be refactored into less monolithic code. 

Add security / Auth / passphrases in email to ensure only desired user can utilie functionality. Also time-based / temporary agents. 

Token / credit counting regime. 

Response judgement by llm and new rules. Agent judge for whether or not to respond. Time throttling / don't respond if have responded within x amount of time. 


### API Specific 
Pass custom LLM settings for each API call based on agent record details, e.g. add custom temp, max_tokens, etc. to each agent record; and write shortcode to control custom LLM controls through shortcode. 

Create API so other apps can send, receive, and control multi-agent emails, e.g. voice-to-email. "Send me an email that says..." Also get agent details from an API. 

Centralize configs / limits / deal with model variation in limits.


# Onboarding 
Revise onboarding to include company name capture, shaping agent profiles around company-specific user configurations. Modify onboarding so the "semantic-life.com" domain name is replaced by whatever the user chooses, including new_agents.py. 


# Smaller Functionality 
Implement automated emails for daily briefs, follow-ups, and task list management.

Progressive/regressive inbox checking system based on activity levels. Implement adaptive rate limiting based on the model type and agent-specific API settings, including temperature and max tokens.

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

Relationship data is formatting inconsistently. 

PDF emails break quoting. 

Address looping issues in ff agents and discrepancies between embody vs. creator.

Rectify issues with ff creator not functioning as expected.

Fix inconsistencies in summarize.json and consider function calling for better performance.

Improve shortcode detection and repair incorrect usage through intermediary LLM rather than relying on regex.
