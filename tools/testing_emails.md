# test routine - send these emails 


✅  multi-agent multi-human to / cc handling / history nesting  (non ff) / writes to processed_threads 

_multiple humans cc'd and respond before agents respond_

agent1 - please tell me a joke about AI.

agent2 - please tell me a joke about working in education technology. 


✅  pdf test (text only right now)

what does this pdf say? 


✅  detail / split 

please tell me about the history of america in a whitepaper in this multi-pass llm construction. put clear ALL CAPS section headers in each section.

BE VERY VERY VERBOSE. REPEAT THE HEADING AT THE TOP OF EACH SECTION.

!detail_start!
Heading: INTRODUCTION
an introduction written in social media engagement / attention grabbing ideas.
15 ideas in bullet points.

!split!
Heading: TIMELINE
an ascii diagram / flow chart style of the historical timeline of the founding of america and key events in our history.
15 items included.

!split!
heading: SUMMARY
a summary of the constitution.
at least 10 paragraphs

!split!
heading: CREATIVE STORY OF THE CONSTITUTION BEING WRITTEN AS A CHILDREN'S STORY
50 bullet points
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

I'm working on a new creative project and need some roleplaying. Please render this agent and have it answer the question below.

!ff.creator(Embody a playful vampire who is friends with a dolphin in a children's book style who speaks in comical vampire voice.)!

Mr. Vampire, what is your favorite game to play?




✅  summarize  -- summarize to json / other formats 
_!summarize_start!_
_!summarize_stop!_
OR
_!summarize.modality_start!_
_!summarize.modality_stop!_

Example - JSON Modality: 

!summarize.json_start!
We the People of the United States, in Order to form a more perfect Union, establish Justice, insure domestic Tranquility, provide for the common defence, promote the general Welfare, and secure the Blessings of Liberty to ourselves and our Posterity, do ordain and establish this Constitution for the United States of America.
Article. I.
Section. 1.

All legislative Powers herein granted shall be vested in a Congress of the United States, which shall consist of a Senate and House of Representatives.
Section. 2.

The House of Representatives shall be composed of Members chosen every second Year by the People of the several States, and the Electors in each State shall have the Qualifications requisite for Electors of the most numerous Branch of the State Legislature.

No Person shall be a Representative who shall not have attained to the Age of twenty five Years, and been seven Years a Citizen of the United States, and who shall not, when elected, be an Inhabitant of that State in which he shall be chosen.

Representatives and direct Taxes shall be apportioned among the several States which may be included within this Union, according to their respective Numbers, which shall be determined by adding to the whole Number of free Persons, including those bound to Service for a Term of Years, and excluding Indians not taxed, three fifths of all other Persons. The actual Enumeration shall be made within three Years after the first Meeting of the Congress of the United States, and within every subsequent Term of ten Years, in such Manner as they shall by Law direct. The Number of Representatives shall not exceed one for every thirty Thousand, but each State shall have at Least one Representative; and until such enumeration shall be made, the State of New Hampshire shall be entitled to chuse three, Massachusetts eight, Rhode-Island and Providence Plantations one, Connecticut five, New-York six, New Jersey four, Pennsylvania eight, Delaware one, Maryland six, Virginia ten, North Carolina five, South Carolina five, and Georgia three.

When vacancies happen in the Representation from any State, the Executive Authority thereof shall issue Writs of Election to fill such Vacancies.

The House of Representatives shall chuse their Speaker and other Officers; and shall have the sole Power of Impeachment.
Section. 3.

The Senate of the United States shall be composed of two Senators from each State, chosen by the Legislature thereof, for six Years; and each Senator shall have one Vote.

Immediately after they shall be assembled in Consequence of the first Election, they shall be divided as equally as may be into three Classes. The Seats of the Senators of the first Class shall be vacated at the Expiration of the second Year, of the second Class at the Expiration of the fourth Year, and of the third Class at the Expiration of the sixth Year, so that one third may be chosen every second Year; and if Vacancies happen by Resignation, or otherwise, during the Recess of the Legislature of any State, the Executive thereof may make temporary Appointments until the next Meeting of the Legislature, which shall then fill such Vacancies.

!summarize.json_stop!

