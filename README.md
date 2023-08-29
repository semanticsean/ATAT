Email Server for Agents
Overview

This project is designed to manage an email server that interacts with AI agents. Each file serves a specific purpose in the system, and they are designed to work together.

Responsibilities

    Manages an email server that reads incoming emails and responds to them using AI agents.
    Handles email sending and receiving via SMTP and IMAP protocols.
    Manages email content, agent selection, and responses.

Dependencies

    os
    re
    smtplib
    time
    json
    imaplib
    logging
    html
    email
    datetime
    contextlib
    AgentSelector (from agent_selector.py)

Environment Variables

    SMTP_SERVER
    SMTP_PORT
    SMTP_USERNAME
    SMTP_PASSWORD
    IMAP_SERVER

main.py
Responsibilities

    Acts as the orchestrator for the entire system.
    Initializes AgentManager, GPTModel, and EmailServer.

Dependencies

    EmailServer (from email_server.py)
    GPTModel
    AgentManager (from agent_manager.py)

agent_selector.py
Responsibilities

    Selects which AI agent should handle an incoming email based on the content and recipient list.
    Generates appropriate prompts for the selected agent.

Dependencies

    re
    time

agent_manager.py
Responsibilities

    Manages the agents available in the system.
    Provides functionalities to look up agents by their name, email, etc.

Dependencies

    json

Setup

    Clone the repository.
    Make sure you have all the dependencies installed.
    Set the required environment variables.
    Run main.py to start the email server.

Usage

    Start the email server by running main.py.
    The email server will continuously check for incoming emails and respond to them using the appropriate AI agent.

s