# ATAT - Email Client for AI Agents 💪🦾

ATAT is designed to democratize the use of AI, allowing quick setup of an AI agent "company" in minutes, with the steering handled over email. That means training is as simple as providing a new email to forward to or cc. This approach leverages the inherent slowness of email for thoughtful, comprehensive AI responses.

The other big advantage of email is it's slow. As demonstrated in the @@ and !detail! shortcodes, multi-pass (multi-API-call) components can be integrated and the time it takes to run all the calls, be it minutes or even hours, is normal for email. 

** For Example, a team of 3 AI agents can be instructed a short story about AI easily:**

> Subject: Write a Story About AI using @@
> Body: 
>
> Agent 1: Please write an outline for two AI agents to write a scifi story about AI. 
>
> @@(Agent 2): Please write the first draft based on the outline
> 
> @@(Agent 3): Please proofread and finalize the story
>
> Thanks


**Or 1 AI agent can be instructed to write a story in three parts:**

> Subject: Write a Story About AI using !detail!
> Body:
>
> Agent 1: please write a story about AI.
> !detail_start!
> First Act: The Emergence of sentient AI
> !split!
> Second Act: The Role of AI in Peace and Abundance
> !split!
> Third Act: The Role of Humans and AI in Exploring the Cosmos
> !detail_stop!
>
> Thanks

- [ATAT - Email Client for AI Agents 💪🦾](#atat---email-client-for-ai-agents-)
* [Key Highlights](#key-highlights)
* [Getting Started](#getting-started)
  + [1. Prepare Replit](#1-prepare-replit)
  + [2. Email Address Configuration](#2-email-address-configuration)
  + [3. Deployment and Usage](#3-deployment-and-usage)
  + [⚠️ Critical Advice](#️-critical-advice)
* [Features & Benefits](#features--benefits)
  + [🦾 New Agent Creation](#-new-agent-creation)
  + [🎩 Agent Dashboard](#-agent-dashboard)
* [Shortcode Overview](#shortcode-overview)
* [Contribution and Development](#contribution-and-development)
* [License](#license)
* [Trademark Notice](#trademark-notice)

- **Collaboration Encouraged:** Join us in enhancing ATAT. Find collaboration details at [x.com/seanmcdonalxyz](https://x.com/seanmcdonalxyz).
- **Alpha Stage Disclaimer:** ATAT is in alpha, with potential errors and formatting issues across different email clients. Use it for testing and clearly label AI-generated responses.

## **Getting Started**

### **1. Prepare Replit**
- **Package Version:** Use `pip install openai==0.28.0` for compatibility.
- **Secrets Configuration:** Enter your SMTP and OpenAI API credentials as secrets.
  
### **2. Email Address Configuration**
- **Agent Aliases:** Assign email aliases for agents in `agents/agents.json`. Use app passwords for secure access.

### **3. Deployment and Usage**
- **Run and Explore:** Deploy via Replit and navigate the agent dashboard. Check spam settings if responses are missing.

### **⚠️ Critical 🚨🚨**
MAKE A NEW EMAIL TO USE WITH ATAT. DO NOT CONNECT EXISTING ACCOUNTS. ATAT is reactive and you may send unintended emails if you haven't indexed the history properly. Create a new account exclusively for ATAT use.

## **Features & Benefits**

- **🚀 Rapid Deployment:** Easy integration into existing email systems.
- **🤖 Agent-Centric Communication:** Designed for AI interactions, complete with an Agent Dashboard.
- **✅ Reactive Email Design:** Focuses on human-initiated interactions, avoiding unsolicited email communication.
- **🦾 Multi-Agent Collaboration:** Enhances decision-making through a mixture of expert agents.
- **🛠️ Shortcode System:** Simplifies complex tasks with shortcodes like `!detail`, `!summarize`, and `!ff`.
- **⏰ Embracing Email's Pace:** Utilizes email's slow nature for detailed, thoughtful AI responses.
- **💡 Replit Setup:** Quick setup process on Replit.
- **📝 PDF Capability:** Agents can interpret text from PDFs.
- **🎨 Custom Dashboard:** Customizable HTML/CSS for branding.
- **⏳ Synthetic Time Travel:** See how people will react to an email or document before it happens. 
### **🦾 New Agent Creation**
Utilize `new_agent.py` for generating new agents with detailed personas and DALL-E generated images.

### **🎩 Agent Dashboard**
`cards.py` powers a Flask server showcasing a dashboard of all agents for easy access.

# Shortcode Overview

Enhance your email interactions with our advanced shortcode system. Designed for seamless integration into email content, these shortcodes trigger specialized functionalities within the ATAT platform, enabling dynamic agent engagement and content manipulation directly through your emails. Explore the capabilities and usage of each shortcode to leverage the full potential of ATAT for your email communications.

## Engaging Agents with `@@`

- **Functionality:** Use the `@@` shortcode to dispatch emails to multiple agents simultaneously, fostering a collaborative multi-agent response. This feature is invaluable for scenarios requiring input from diverse AI personas.
- **Usage:** Simply include `@@(agent name)` or `@@.creator` in your email, followed by specific agent identifiers or creation instructions. This command cues ATAT to engage the designated agents in the response process.

### Dynamic Agent Creation with `@@.creator`

- **Functionality:** The `@@.creator` shortcode instantaneously generates new agent personas, offering on-the-fly customization to adapt to the evolving needs of the conversation.
- **Usage:** Implement `@@.creator(Embody an agent...)` with detailed persona specifications. Ensure "Embody" is present to activate the creator function, signaling ATAT to craft and introduce a new agent persona based on your instructions.


## Chunking Long-Form Content Generation with `Detail`

- **Functionality:** The `Detail` shortcode breaks down extensive text blocks into manageable segments, optimizing the processing and generation of responses.
- **Usage:** Wrap your detailed content between `!detail_start!` and `!detail_stop!` markers. ATAT automatically segments the content for efficient handling.

### Summarizing Content with `Summarize`

- **Functionality:** The `Summarize` shortcode condenses detailed content into brief summaries, customizable through specific modifiers to suit your summary's intended focus and style.
- **Usage:** Trigger this feature with `!summarize!`, adding modifiers as needed to refine the summary output.

#### Modifiers for Tailored Summaries

- **Explanation:** Modifiers adjust the shortcode's processing of content, allowing for emphasis on certain elements or the alteration of the response's verbosity.
- **Examples:** Use modifiers like `!summarize.json!`, `!summarize.marketing!`, or `!summarize.budget!` to direct ATAT in crafting summaries that align with your requirements, whether it be in JSON format, marketing language, or budget-focused content.

Leverage these shortcodes to streamline your email interactions, ensuring efficient and effective communication with and between your AI agents.


## **Contribution and Development**

- **Community Contributions:** Contributions are welcome to address known issues and enhancements listed in `contribute.md`.
- **Roadmap:** Future features and improvements are outlined for participants.

## **License**

ATAT is licensed under the MIT License. Refer to the LICENSE file for details.

## **Trademark Notice**

@@ and ATAT are trademarks of Semantic Life, Copyright 2024. All rights reserved.
