# critical

Update to OpenAI SDK 1.0. 

Refactor 

Email formatting / structure in general, quoted printable, gmail quotes, gmail not divs, email construction loop -- all needs refactored. 

new_agent.py needs to be openai sdk 1.0 and function calling + instructor 

add automated emails for daily / morning briefs / followup / consistent task list management. 

update instructions to get company name during onboarding and build profile around every agent working there / user config. 

Would love to see equivalent of custom gpts on an offline commodity box running a local model. a "slowcal" model -- slow and local. 

Fix CSS Grid 


Integrate with Assistants / GPTs / custom trains / HF 

breaking on: 

n > 1 agent in cc's 

n > 1 agent in @@ 

Profiles for each agent in flask app 

Auth for flask app access so can be private. 

Onboarding through flask app. 

Smooth out Deploy on Replit so it's < 1 minute to deploy 25 agents once the email credentials, aliases, and agent rendering are done. 



🚩 FF LOOPING AGENTS 

🚩 embody vs. creator 

🚩 summarize json not working consistently / should be function calling? 

🚩 have intermediary llm handle shortcode detection and even repair of incorrect shortcode vs. brittle regex 

🚩 agent confusion / context awareness of each other


🚩 duplicate and triplicate responses, especially in detail
🚩 email formatting needs to be its own class / set of tools 
🚩 atlas awareness 
🚩 create airbnb manager 
🚩 new orion 
🚩 processed threads letters / rebuilder 
🚩 actual unit test scripts 
🚩 minify 
🚩 centralize 
🚩 ff creator doesn't work  
🚩 re-structure extant agents when migrating 
🚩 update readme 
🚩 sender name included in information 
🚩 remove old new agent from gpt 
🚩 test all again 


🚩 Rendered Agents replying twice, not writing to json, not labeled properly in headers 

Certain agent instructions prevent summarize.json from working. 

Handle very large files / text 

Integrate with RAG/E (RAG + Embeddings), local or API 



ff / creator need better logic for handling multiple agents / calling multiple agents / calling the same agent more than once if explicitly doing that to be fluid / natural. 


Most important: API so other apps can sync to email rapidly. 

Rewrite ABE with function calling / structured output / instructor. 


Integrate AB/E "ABE" - election and polling generator as a shortcode / function call. 

Integrate new agent as a shortcode -> function call. 

Adadpt to work on GH and local. 

Add self-awareness of name and email to the prompt. Was buggy / don't want to pass emails to LLM model right now. 

Make shortcode detection an agent operation for detection and then write out to function call not regex. 


# next steps 

Refactor with community feedback and guidance. Needs proper class structure, testing, and utlimately to read off of a database and accept API hooks for agents instead of just static JSON. 

Improve thread_recionciler.py and self-healing of data storage, move processed_threads.json to a db. update onboarding so no risk in plugging into older email inboxes with hundreds / thousands of old messages to index, and prevent uninentional triggering of send emails in that process. 

Build a stand-alone email constructor including handling of various client types, history management, history css. Read history from a local db that is in sync with remove server, in most robust case. 

LLAMA and other API integrations, probably HF. 

Give agents the ability to run ABE. 

Integrating chain / brain tools. 



Go full George Hotz - test in every method / function, 100% testing all the time. 

Move config, new agent, other actions to web interface through flask with loading indicators, etc. 

testing infrastructure. 

add multimodal from gmail image retrievals 

include profile picture that's generated 

build out display cards flask integration

adaptive rate limiting based on the model 

inform agents of one another 

progressive / regressive checking time based on inbox activity (more activity check more often, vice versa)

add agent profile pics to signatures 
add images from gmail url 
api / assistants 
response judge 
exponential back off answers 
exponential back of checking server imap 
deploy to replit stablize 
backup everything 
inform agents of one another in summaries script 
functioncalling / instructor integration 
agents over api 
make each agent call their own api type and settings incl. temp, maxt, etc.
handle multiple 

context awareness
current date awareness
newsupdate awareness 

