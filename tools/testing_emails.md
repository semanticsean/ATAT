# test routine - send these emails 



✅  multi-agent multi-human to / cc handling / history nesting  (non ff) / writes to processed_threads 

_multiple humans cc'd and respond before agents respond_

agent1 - please tell me a joke about AI.

agent2 - please tell me a joke about working in education technology. 


✅  pdf test (text only right now)

what does this pdf say? 


✅  detail / split 

agent1,

please tell me about the history of america in a whitepaper in this multi-pass llm construction. put clear ALL CAPS section headers in each section.

!detail_start!
an introduction written in social media engagement / attention grabbing ideas.

!split!

an ascii style graph of the historical timeline of the founding of america and key events in our history.

!split!

a summary of the constitution.

!split!
our story in an emoji-based "graphic novel" made of only emojis with some subheadings for the various scenes describing key moments.

!detail_stop!


✅  ff / ff creator 
agent1 - what is the most important question for grant applicants to answer when writing nonprofit grants?

!ff(agent2)! what do you think??

!ff(agent3)! what have we not thought of?

!ff(agent4)! what grants should we apply for?

!ff(agent2)! what grant are we most likely to get? what questions are in their grant application? or what are most likely to be on the application? 

!ff(agent1)! please draft an answer for each question for our nonprofit. 


# ff creator 
_!ff.creator!(Embody an agent who ... description)_

An important note is, until the code is improved, ff.creator requires the use of both !ff.creator(Embody)! 




✅  summarize  -- summarize to json / other formats 
_!summarize_start!_
_!summarize_stop!_
OR
_!summarize.modality_start!_
_!summarize_stop!_

agent1, please convert the constitution to json:

!summarize.json_start!

We the People of the United States, in Order to form a more perfect Union, establish Justice, insure domestic Tranquility, provide for the common defence, promote the general Welfare, and secure the Blessings of Liberty to ourselves and our Posterity, do ordain and establish this Constitution for the United States of America.
Article. I.
Section. 1.

  All legislative Powers herein granted shall be vested in a Congress of the United States, which shall consist of a Senate and House of Representatives.
  Section. 2.
  
  The House of Representatives shall be composed of Members chosen every second Year by the People of the several States, and the Electors in each State shall have the Qualifications requisite for Electors of the most numerous Branch of the State Legislature.
  
  No Person shall be a Representative who shall not have attained to the Age of twenty five Years, and been seven Years a Citizen of the United States, and who shall not, when elected, be an Inhabitant of that State in which he shall be chosen.
  
  ...
  
  
  !summarize_stop! 
  

