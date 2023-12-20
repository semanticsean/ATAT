# test alpha 12
Nov 2, 2023
✅  mh mp alpha test 
✅  history nesting  (non ff) test
✅  ff basic / ff history test

✅  ff creator test
✅  summarize alpha test simple 
✅  summarize extended test 
✅  detail test  

🚩  summarize not working 
🚩  agent confusion in mh mp alpha test 1 




# test alpha 10
Wednesday, October 11, 2023 (PDT)

✅  mh mp alpha test 8
✅  history nesting  (non ff)
✅  mh test alpha 8
✅  summarize alpha test 9 simple
✅  summarize extended alpha test 9
✅  detail test  8
✅  handles all threads 
✅  doesn't violate api rules 
✅  ff advanced 

🚩  ff no response MIXED RESULTS 
🚩  hang on extra large gpt calls needing reduction 



# test alpha 9
Wednesday, October 11, 2023 (PDT)

✅  mh mp alpha test 8
✅  history nesting  (non ff)
✅  mh test alpha 8
✅  summarize alpha test 9 simple
✅  summarize extended alpha test 9
✅  detail test basic alpha 8
✅  handles all threads 
✅  doesn't violate api rules 
✅  ff advanced 

🚩  ff no response MIXED RESULTS 
🚩  hang on extra large gpt calls needing reduction 



# test alpha 2 
alpha 2 1:08 PM
Wednesday, October 11, 2023 (PDT)

✅  ff test basic 
✅  multiplayer 
✅  multiplayer many humans 
✅  many humans 
✅  writes to processed_threads 
✅  ff test 
✅  detail 
✅  summarize 
✅  history nesting 
✅  only replies to most recent thread 
✅  summarize 
✅  handles all threads 
✅  doesn't violate api rules / no errors 


known issues: 
formatting of history in fast forward history 
prompt control for detail shortcodes / not an email / explain multi-part nature 
processed threads weird comma thing 
multiplayer putting response inside quoted content 
ff advanced cutting off at 3 rounds 
detail sending each twice 



# multiplayer many humans 

atlas - please tell me a joke about AI.

indie - please tell me a joke about working in education technology. 



# many humans 
please say 'many humans test 




# detail test

rinn,

please tell me about sunschool in a whitepaper.

!detail_start!
an introduction written in clickbait attention grabbing ideas

!split!

an ascii style graph of the growth we expect to see and in what markets

!split!

a budget of our future capital costs in a table format

!split!
our story in an emoji story.

!detail_stop!

# ff test 
crystal - what is the most important grant question?

!ff(devatlas)! what is ALIGN corp's response?

!ff(devcrystal)! how could we improve this response?

!ff(devatlas)! please rewrite based on that feedback.

!ff(devcrystal)! what grants would be good for align corp? recommend any?

!ff(devatlas)! which one should we apply for? based on what? please write a draft memo about the application content. 

# summarize test 

ada, please convert the constitution to json:

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
  

