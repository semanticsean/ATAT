# ATAT - Email Client for AI Agents 💪🦾

<p align="center">
    <img src="https://atat-dev-0-3.replit.app/static/atat-board.png" width="400" alt="ATAT by Semantic Life"/>
</p>

# Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Prepare Replit](#1-prepare-replit)
  - [Email Address Configuration](#2-email-address-configuration)
  - [Deployment and Usage](#3-deployment-and-usage)
  - [Critical Advice](#️-critical-)
- [Features & Benefits](#features--benefits)
  - [Rapid Deployment](#-rapid-deployment)
  - [Agent-Centric Communication](#-agent-centric-communication)
  - [Reactive Email Design](#-reactive-email-design)
  - [Multi-Agent Collaboration](#-multi-agent-collaboration)
  - [Shortcode System](#-shortcode-system)
  - [Embracing Email's Pace](#-embracing-emails-pace)
  - [Replit Setup](#-replit-setup)
  - [PDF Capability](#-pdf-capability)
  - [Custom Dashboard](#-custom-dashboard)
  - [Synthetic Time Travel](#-synthetic-time-travel)
  - [New Agent Creation](#-new-agent-creation)
  - [Agent Dashboard](#-agent-dashboard)
- [Shortcode Overview](#shortcode-overview)
  - [Engaging Agents with @@](#engaging-agents-with-)
  - [Dynamic Agent Creation with @@.creator](#dynamic-agent-creation-with-creator)
  - [Chunking Long-Form Content Generation with Detail](#chunking-long-form-content-generation-with-detail)
  - [Summarizing Content with Summarize](#summarizing-content-with-summarize)
  - [Modifiers for Tailored Summaries](#modifiers-for-tailored-summaries)
- [Contribution and Development](#contribution-and-development)
- [License](#license)
- [Trademark Notice](#trademark-notice)
- [Source Code](https://github.com/semanticsean/ATAT)
- [Roadmap and Contribution Guide](https://github.com/semanticsean/ATAT/blob/main/contribute.md)


#Introduction 

**ATAT enables rapid setup of AI agents you can email -- with simple shortcodes that give the agents superpowers.**

Just add credentials (see Setup Guide) and you've got dozens of agents deployed over safe, reliable, email. 

<div align="center">
    <table>
        <tr>
            <td align="center" width="420"><em>Rapid Setup for AI Agents Over Email</em></td>
            <td align="center">→</td>
            <td align="center" width="420"><strong><em>Deploy Agents In a Managed System</em></strong></td>
        </tr>
        <tr>
            <td align="center" width="420"><em>To, CC, and Fw: Multiple Agents</em></td>
            <td align="center">→</td>
            <td align="center" width="420"><strong><em>Simplified Training: Just Email</em></strong></td>
        </tr>
        <tr>
            <td align="center" width="420"><em>Powerful Shortcodes for AI</em></td>
            <td align="center">→</td>
            <td align="center" width="420"><strong><em>Multi-Agent Multi-Step Collaboration Enabled</em></strong></td>
        </tr>
        <tr>
            <td align="center" width="420"><em>Batteries Included, Just Add Credentials</em></td>
            <td align="center">→</td>
            <td align="center" width="420"><strong><em>Email Client and Stylized Dashboard Work</em></strong></td>
        </tr>
    </table>
</div>


Source Code [https://github.com/semanticsean/ATAT](https://github.com/semanticsean/ATAT)

Roadmap: For those interested in contributing to the project, please refer to our [contribution guide](https://github.com/semanticsean/ATAT/blob/main/contribute.md) for detailed information on how you can get involved.


**EXAMPLE: Email a team of three AI agents who collaborate to write a short story:**

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


**Email one AI agent, instructed to write a story in three acts (three API calls):**

> Subject: Write a Story About AI using !detail!
> Body:
>
> Agent 1: please write a story about AI.
> 
> !detail_start!
> 
> Act 1: The Emergence of sentient AI
> 
> !split!
> 
> Act 2: The Role of AI in Peace and Abundance
> 
> !split!
> 
> Act 3: The Role of Humans and AI in Exploring the Cosmos
> 
> !detail_stop!
>
> Thanks


# **Getting Started**

This guide walks you through deploying on Replit, because it's so easy to deploy. Start with this [Repl.](https://replit.com/@realityinspector/ATAT-Email-Client-for-AI-Agents-v03-ALPHA-public)

To use locally or on Github, you'll have to change the calls to take env vars. 

### **1. Packages & Secrets / Env Vars**
- **Package Version:** Use `pip install openai==0.28.0` for compatibility.
- **Secrets Configuration:** Enter your SMTP and OpenAI API credentials as secrets.
  
>**{**
>
>  **"SMTP_SERVER": "",**
> 
>  **"IMAP_SERVER": "",**
> 
>  **"SMTP_PORT": "",**
> 
>  **"SMTP_USERNAME": "",**
> 
>  **"SMTP_PASSWORD": "",**
> 
>  **"OPENAI_API_KEY": "",**
> 
>  **"DOMAIN_NAME": "",**
> 
>  **"COMPANY_NAME": ""**
> 
>**}**

For SMTP_PORT using Google Workspace, use Port 587.

For SMTP_PASSWORD, if you're using Google / Gmail it needs to be an APP PASSWORD which requires 2FA.

DOMAIN_NAME should be what follows @ in an email address. For example, "acme.com" like "info@acme.com". 

COMPANY_NAME should be as it appears in writing, like "ACME Corp."

  
### **2. Email Address Configuration**
- **Create An Agent@ Email Address:** This must be a new email address with no history. 
  
- **Agent Aliases:** Assign at least one email alias for at least one agent in `agents/agents.json`. The rest are optional and can be called with the @@(Agent Name) shortcode, or can receive their own alias. @@ is helpful if you want more agents than your email server supports as aliases. For example Google Workspace limits to 25, but you can deploy hundreds of agent models accessible through the @@ shortcode. 

### **3. Deployment and Usage**
- **Run and Explore:** Deploy via Replit and navigate the agent dashboard. Check spam settings if responses are missing.

See /tools/testing_emails.md for emails to test with.

### **⚠️ Critical 🚨🚨**
MAKE A NEW EMAIL TO USE WITH ATAT. DO NOT CONNECT EXISTING ACCOUNTS. ATAT is reactive and you may send unintended emails if you haven't indexed the history properly. Create a new account exclusively for ATAT use.

# **Features & Benefits**

ATAT is an email client that hosts AI agents who respond to emails, so you can email them directly, cc them, or fw: emails to them. ATAT is designed to democratize the use of AI, allowing quick setup of an AI agent "company" in minutes, with the steering handled over email. That means training is as simple as providing a new email to forward to or cc. This approach leverages the inherent slowness of email for thoughtful, comprehensive AI responses. It also opens up "MoE" or "CoE" thinking for normies. 

Another strength of email is that it's slow. As demonstrated in the @@ and !detail! shortcodes, multi-pass (multi-API-call) components can be integrated and the time it takes to run all the calls, be it minutes or even hours, is normal for email. 


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

**Testing Email** 
>
>devatlas - what is the most important question for grant applicants to answer when writing startup pitch decks?
>
>@@(castor) what startups do you like?
>
>@@(Nova) what do you think?
>
>@@(Orion) what do you think? 
>
>@@(Nebula) what do you think?
>
>@@(Altair) what do you think? 

### Dynamic Agent Creation with `@@.creator`

- **Functionality:** The `@@.creator` shortcode instantaneously generates new agent personas, offering on-the-fly customization to adapt to the evolving needs of the conversation.
- **Usage:** Implement `@@.creator(Embody an agent...)` with detailed persona specifications. Ensure "Embody" is present to activate the creator function, signaling ATAT to craft and introduce a new agent persona based on your instructions.

**Testing Email** 
>I'm working on a new creative project and need some roleplaying. Please render this agent and have it answer the question below.
>
>@@.creator(Embody a playful vampire who is friends with a dolphin in a children's book style who speaks in comical vampire voice.)!
>
>Mr. Vampire, what is your favorite game to play?

## Chunking Long-Form Content Generation Requests with `Detail`

- **Functionality:** The `Detail` shortcode breaks down extensive text blocks into manageable segments, optimizing the processing and generation of responses.
- **Usage:** Wrap your detailed content between `!detail_start!` and `!detail_stop!` markers. ATAT automatically segments the content for efficient handling. Use '!split!' to split the API calls / engage multipass.

>
>!detail_start!
>introduction: it's the year 2050 and AI driven synthetic time travel is easily possible
>!split!
>we meet our protagonist, in detail
>!split!
>we meet our antagonist, in detail
>!split!
>we see the first conflict between the protagonist and antagonist, the first act ends
>!split!
>the second act begins with a new player, a romantic interest who hasn't been mentioned yet
>!split!
>the second act has a principal conflit
>!split!
>the climax happens
>!split!
>the resolution doesn't happen yet
>!split!
>now the resolution happens
>!detail_stop! 

### Summarizing Content with `Summarize`

- **Functionality:** The `Summarize` shortcode condenses detailed content into brief summaries, customizable through specific modifiers to suit your summary's intended focus and style.
- **Usage:** Trigger this feature with `!summarize!`, adding modifiers as needed to refine the summary output.

(This feature is even more buggy than others.)

SEE /tools/testing_emails.md for testing scripts--too long to fit here.

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

Google / Google Workspace (TM) Google.