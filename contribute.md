# critical
🚩 FF LOOPING AGENTS 
🚩 line breaks in ff history not working right 
🚩 embody vs. creator 
🚩 CARDS not integrated 
🚩 multiplayer putting response inside quoted content 
🚩 explain multi-part nature 
🚩 summarize json not working 
🚩 prompt control for detail shortcodes / not an email /
🚩 summarize not working 
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


Most important: API so other apps can sync to email rapidly. 


Integrate AB/E "ABE" - election and polling generator as a shortcode / function call. 

Integrate new agent as a shortcode -> function call. 

Adadpt to work on GH and local. 

Add self-awareness of name and email to the prompt. Was buggy / don't want to pass emails to LLM model right now. 

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

