# Email Server for Agents: README

add cards.py explanation 
new agent explanation 
pdf2text 
rename files / functions 

Why no testing? 

Doing a lot of unit testing and using Replit IDE rewards using print statements because the AI catches the error automatically. 

Why is it the old version? 

1. Threshold reached of what I can support on my own
2. Ultimately it should be that email addresses work on locked, older systems that don't require upgrade and can be localized if the user desires 


## Overview:
The system is designed to act as an email server for agents. It processes incoming emails, sends responses, and manages agents and their personas. The system leverages the OpenAI GPT model to generate dynamic responses based on agent personas. It works by using aliases. It's primarily built for Google Workspace integration for initial testing, but should be compatible with almost all clients, and has been tested with Hey.com, and privately hosted IMAP / SMTP.


# About This Project: First Large Python Open Source
I have worked at companies that published open source code, in which I played a small role developing, but this is my first fully self-authored (with various AIs) open source project and first large python project. If (when) you see things that can (must) be done better, please contribute or at least comment. I'm on X -- @seanmcdonaldxyz. 

If I could build it again, I would build testing at every level. Due to a lack of testing, development cruft, and inefficiencies, it needs large-scale, even complete refactoring going forward. However, it works - mostly. (!!) 


# Capacitites 

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
