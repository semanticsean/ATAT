# ATAT - Email Client for AI Agents 💪🦾

<p align="center">
    <img src="https://semantic-life.com/static/atat-board.png" width="400" alt="ATAT by Semantic Life"/>
</p>



<div align="center">
    <table>
        <tr>
            <td align="center" width="420"><em>Rapid Setup for AI Agents Over Email</em></td>
            <td align="center">→</td>
            <td align="center" width="420"><strong><em>Deploy Agents In the Easiest Way for Your Users</em></strong></td>
        </tr>
        <tr>
            <td align="center" width="420"><em>To, CC, and Fw: Multiple Agents</em></td>
            <td align="center">→</td>
            <td align="center" width="420"><strong><em>Simplified Training: Just Email</em></strong></td>
        </tr>
        <tr>
            <td align="center" width="420"><em>Powerful Shortcodes for AI</em></td>
            <td align="center">→</td>
            <td align="center" width="420"><strong><em>Multi-Agent Multi-Step Collaboration for All</em></strong></td>
        </tr>
        <tr>
            <td align="center" width="420"><em>Batteries Included, Just Add Credentials</em></td>
            <td align="center">→</td>
            <td align="center" width="420"><strong><em>Includes Email Client and Agent Dashboard</em></strong></td>
        </tr>
    </table>
</div>

# Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
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
- [Shortcodes](#shortcode-overview)
- [Contribution and Development](#contribution-and-development)


# Introduction 

**ATAT enables rapid setup of AI agents you can email -- with simple shortcodes that give the agents superpowers.**

Source Code [https://github.com/semanticsean/ATAT](https://github.com/semanticsean/ATAT)

Roadmap: For those interested in contributing to the project, please refer to our [contribution guide](https://github.com/semanticsean/ATAT/blob/main/contribute.md) for detailed information on how you can get involved.


v0.4 - Includes ABE - A/B + Election polling. 
v0.3 - Initial Release 


**EXAMPLE: Email a team of three AI agents who collaborate to write a short story:**

<p align="left">
    <img src="https://atat-dev-0-3.replit.app/static/email-example-1.png" width="600" alt="ATAT by Semantic Life"/>
</p>

**Email one AI agent, instructed to write a story in three acts (three API calls):**

<p align="left">
    <img src="https://atat-dev-0-3.replit.app/static/email-example-2.png" width="600" alt="ATAT by Semantic Life"/>
</p>


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

IMPORTANT: You may need to whitelist the domain and / or email addresses. 

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


ABE (A/B+Election) - Agent Polling Tool
Overview
ABE stands for A/B+Election, a sophisticated tool designed to facilitate the polling of intelligent agents in various scenarios, ranging from decision-making processes to opinion gathering and beyond. Built on the foundation of Flask, ABE integrates seamlessly with web technologies to offer a dynamic and interactive experience for both administrators and participants.

Features
Agent Management: Easily manage a roster of agents, each with unique identifiers and attributes. ABE allows for the detailed specification of agents, including custom keywords and images, to enhance the polling experience.

Dynamic Polling: Conduct A/B tests or elections among agents with customized questions and instructions. This feature enables researchers and developers to gather nuanced insights into agent preferences or decisions.

Email Authentication: A secure authentication system that utilizes email confirmation for user validation. This ensures that only authorized participants can contribute to the polling process.

Session Management: With ABE, sessions are uniquely identified and managed, allowing for a structured approach to data collection and analysis. Each session can be tailored with specific questions, instructions, and agent selections.

Interactive Dashboard: A web-based dashboard provides a centralized interface for configuring polls, visualizing agent selections, and initiating sessions. The dashboard enhances the user experience, making it easier to navigate through the polling process.

Customizable Output: Generate and customize output based on polling results. ABE supports the creation of detailed reports, visualizations, and summaries, catering to a wide range of analysis needs.

Security and Privacy: Built with security in mind, ABE implements best practices to protect user data and ensure the integrity of the polling process. Sessions and data transmissions are handled securely, with considerations for privacy and confidentiality.

Getting Started
Setup and Installation: Begin by setting up your Python environment and installing Flask along with other necessary dependencies. ABE requires Python 3.6 or newer for backward compatibility.

Configure Agents: Populate agents.json with your agents' information, including names, attributes, and images. This file serves as the database for the agents participating in the polls.

Launch the Application: Run abe.py to start the Flask server. Navigate to the provided URL to access the ABE dashboard.

Create a Poll: Use the dashboard to configure your poll, including questions, agents to involve, and custom instructions. Each poll can be tailored to meet specific research or decision-making needs.

Distribute and Collect Responses: Once your poll is live, authorized participants can engage with the platform, providing their responses and opinions. ABE manages the collection and organization of this data in real-time.

Analyze Results: With the polling complete, ABE facilitates the analysis of results through its dashboard. Export data, generate reports, and derive insights from the aggregated responses.

Use Cases
ABE's versatile framework makes it suitable for a variety of applications, including but not limited to:

Market Research: Understand consumer preferences or predict market trends by polling a group of representative agents.
Decision Support: Facilitate decision-making processes within organizations by gathering and analyzing agent opinions.
Academic Research: Conduct studies and experiments involving agent-based models and simulations.
Conclusion
ABE offers a powerful and flexible platform for the polling of agents across numerous contexts. By combining ease of use with a robust set of features, ABE empowers users to gather, analyze, and leverage data in innovative ways. Whether for research, decision-making, or market analysis, ABE provides the tools necessary to harness the collective intelligence of agents.

## **Contribution and Development**

- **Community Contributions:** Contributions are welcome to address known issues and enhancements listed in `contribute.md`.
- **Roadmap:** Future features and improvements are outlined for participants.

## **License**

ATAT is licensed under the MIT License. Refer to the LICENSE file for details.

## **Trademark Notice**

@@ and ATAT are trademarks of Semantic Life, Copyright 2024. All rights reserved.

Google / Google Workspace (TM) Google.







# NOTES TO ADD 

## ABE db setup

psql -h hostname -U username -d databasename
SET idle_in_transaction_session_timeout = '15min';
psql -d $DB_NAME -U $DB_USER -W $DB_PASS
flask db init  # Only needed the first time to set up migrations directory
flask db migrate -m "Added PageView model"
flask db upgrade






Semantic Life - AI Agent Dashboard

Welcome to the Semantic Life - AI Agent Dashboard! This powerful tool allows you to create, manage, and interact with AI agents in a user-friendly web interface. With features like agent creation, timeframe management, meeting organization, and survey conducting, you can leverage the power of AI to gain valuable insights and make informed decisions.
Features

    Agent Creation: Easily create new AI agents by providing a name, job title, and description. The system generates a detailed agent persona, including keywords, relationships, and an image prompt, using the OpenAI GPT-4 model. It also generates a profile picture using the DALL-E model.
    Timeframe Management: Create different scenarios or contexts for your AI agents by establishing timeframes. You can select specific agents to include in a timeframe and provide instructions to modify their attributes using the OpenAI API. The modified agents are saved in a new JSON file for easy access.
    Meeting Organization: Organize meetings with your AI agents to gather insights and conduct surveys. Select a timeframe, choose the agents to include, and provide a name for the meeting. The system creates a survey form where you can define questions and gather responses from the agents using the OpenAI API.
    Survey Results: View the results of your surveys in a user-friendly interface. The responses from each agent are displayed alongside their profile information. You can analyze the responses, compare insights from different agents, and make informed decisions based on the survey results.
    Public Sharing: Make your survey results publicly accessible by generating a unique public URL. Anyone with the URL can view the survey results without authentication, allowing you to share insights with a broader audience.

Prerequisites

Before running the Semantic Life - AI Agent Dashboard, ensure you have the following:

    Python 3.x installed
    OpenAI API key
    Required Python packages (listed in requirements.txt)

Installation

    Clone the repository:

bash

git clone https://github.com/your-username/semantic-life.git

    Install the required Python packages:

bash

pip install -r requirements.txt

    Set up the environment variables:

    OPENAI_API_KEY: Your OpenAI API key
    DATABASE_URL: URL for your database (e.g., PostgreSQL)
    FLASK_KEY: Secret key for Flask sessions
    DOMAIN_NAME: Domain name for your application

    Run the database migrations:

bash

flask db upgrade

    Start the application:

bash

python app.py

    Access the application in your web browser at http://localhost:5000.

Usage

    Register a new account or log in to an existing account.
    Create new agents by providing a name, job title, and description.
    Establish timeframes and select agents to include. Provide instructions to modify the agents' attributes.
    Organize meetings by selecting a timeframe, choosing agents, and providing a name.
    Conduct surveys by defining questions and gathering responses from the agents.
    View survey results and analyze the insights provided by the AI agents.
    Optionally, make survey results publicly accessible by generating a unique public URL.

Contributing

Contributions to the Semantic Life - AI Agent Dashboard are welcome! If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request on the GitHub repository.
License

This project is licensed under the MIT License.
Contact

For any inquiries or feedback, please contact us at info@semanticlife.com.

Enjoy using the Semantic Life - AI Agent Dashboard to unlock the potential of AI agents and gain valuable insights!


# update user tokens 
Open a terminal or command prompt and navigate to your project directory.
Run the following command to start the Flask shell:flas


flask shell
### In the Flask shell, import the necessary models and database instance:

from models import User, db

###  Replace 'username' with the actual username of the user you want to add tokens to.

user = User.query.filter_by(username='username').first()

### Add tokens to the user's account:

user.token_balance = 1000  

db.session.commit()

print(user.token_balance)

exit()


flask db migrate -m "Added user credits"
flask db upgrade 


# back date required for: 
pip install 'itsdangerous<2.0'




Certainly! Here's a technical description of the app for another AI:

The Semantic Life app is a web-based application built using the Flask web framework in Python. It allows users to create and manage AI agents, conduct surveys, and generate timeframes based on user-defined instructions.

The app follows a blueprint architecture, where different parts of the application are separated into individual blueprints, such as auth_blueprint, survey_blueprint, dashboard_blueprint, and profile_blueprint. Each blueprint handles specific routes and functionality related to its purpose.

The app uses a PostgreSQL database to store user information, agent data, surveys, and timeframes. The database models are defined using Flask-SQLAlchemy, an extension that provides ORM (Object-Relational Mapping) capabilities for interacting with the database.

User authentication is implemented using Flask-Login, which handles user registration, login, and session management. Users can register an account, log in, and update their profile information.

The app integrates with the OpenAI API to generate agent data and conduct surveys. It uses the abe_gpt module to process agent data and generate responses based on user-defined instructions. The abe_gpt module communicates with the OpenAI API to generate agent data, modify agent attributes, and generate survey responses.

The app allows users to create and manage AI agents. Users can add base agents, create new agents, edit agent attributes, and delete agents. Agent data is stored in the database and can be retrieved and updated as needed.

Users can also create surveys and conduct meetings with the AI agents. Surveys are created by selecting agents and defining questions. The app uses the abe_gpt module to generate survey responses based on the selected agents and user-defined instructions. Survey results are stored in the database and can be viewed by the user.

Timeframes are another feature of the app, allowing users to create modified versions of the base agents based on specific instructions and context. Users can select agents, provide instructions, and generate a new timeframe with the modified agents. Timeframe data is stored in the database and can be accessed and managed by the user.

The app utilizes various Flask extensions and libraries to enhance its functionality. Flask-Images is used for image handling and processing, although its usage in the current code needs to be cleaned up and fixed. Flask-Migrate is used for database migrations, allowing easy management of database schema changes.

The app's frontend is built using HTML templates and styled with Tailwind CSS. The templates are rendered using Jinja2, a templating engine that allows dynamic content generation. JavaScript is used for client-side interactivity and AJAX requests.

Error handling and logging are implemented throughout the app to catch and handle exceptions gracefully. The app logs relevant information and errors for debugging and monitoring purposes.

Overall, the Semantic Life app provides a platform for users to create, manage, and interact with AI agents, conduct surveys, and generate timeframes based on user-defined instructions. It leverages the Flask web framework, PostgreSQL database, and OpenAI API to deliver its functionality.


# schema 

 table_schema |   table_name    |  column_name  |          data_type          
--------------+-----------------+---------------+-----------------------------
 public       | alembic_version | version_num   | character varying
 public       | meeting         | id            | integer
 public       | meeting         | name          | character varying
 public       | meeting         | user_id       | integer
 public       | meeting         | meeting_data  | json
 public       | meeting         | is_public     | boolean
 public       | meeting         | public_url    | character varying
 public       | page_view       | id            | integer
 public       | page_view       | page          | character varying
 public       | page_view       | timestamp     | timestamp without time zone
 public       | survey          | id            | integer
 public       | survey          | name          | character varying
 public       | survey          | user_id       | integer
 public       | survey          | is_public     | boolean
 public       | survey          | public_url    | character varying
 public       | survey          | survey_data   | json
 public       | timeframe       | id            | integer
 public       | timeframe       | name          | character varying
 public       | timeframe       | user_id       | integer
 public       | timeframe       | agents_data   | json
 public       | user            | id            | integer
 public       | user            | username      | character varying
 public       | user            | email         | character varying
 public       | user            | password_hash | character varying
 public       | user            | agents_data   | json
 public       | user            | images_data   | json
 public       | user            | credits       | integer



# helpful 

SELECT credits FROM user WHERE username = 'the_username';



-----------------------

SELECT
    table_schema,
    table_name,
    column_name,
    data_type
FROM
    information_schema.columns
WHERE
    table_schema NOT IN ('information_schema', 'pg_catalog')
ORDER BY
    table_schema,
    table_name,
    ordinal_position;





    ----------


    check images 

    SELECT
      agent.value->>'id' AS agent_id,
      agent.value->>'photo_path' AS photo_path,
      LENGTH(COALESCE(u.images_data->>(agent.value->>'photo_path'), '')) AS image_length,
      CASE
        WHEN LENGTH(COALESCE(u.images_data->>(agent.value->>'photo_path'), '')) > 0
        THEN 'Present'
        ELSE 'Missing'
      END AS image_status
    FROM
      "user" u,
      json_array_elements(u.agents_data) AS agent
    WHERE
      u.id = 12;




------ 

admin.py standalone adds credits 




----- 

# find meeting info by id 

SELECT 
    m.id AS meeting_id,
    m.name AS meeting_name,
    m.agents AS meeting_agents,
    m.questions AS meeting_questions,
    m.answers AS meeting_answers,
    m.is_public AS meeting_is_public,
    m.public_url AS meeting_public_url,
    u.id AS user_id,
    u.username AS user_username,
    u.email AS user_email
FROM 
    meeting AS m
    JOIN "user" AS u ON m.user_id = u.id
WHERE 
    m.id = 24;





--------

see timeframe agents 

SELECT 
  t.id AS timeframe_id,
  t.name AS timeframe_name,
  json_array_length(t.agents_data) AS num_agents,
  CASE WHEN t.agents_data IS NULL THEN false ELSE true END AS agents_populated,
  CASE WHEN u.images_data IS NULL THEN false ELSE true END AS images_populated,
  json_agg(t.agents_data->>'id') AS agent_names
FROM 
  timeframe t
  JOIN "user" u ON t.user_id = u.id
GROUP BY
  t.id, t.name, t.agents_data, u.images_data;