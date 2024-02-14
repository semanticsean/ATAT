# ATAT Project Collaboration and Roadmap

## Seeking Collaborators and Co-Owners

We're on the lookout for collaborators, sponsors, and potentially a co-owner to join the ATAT project. Ideal candidates have extensive experience with email clients and are familiar with the challenges and nuances they present. With 347.3 billion emails sent last year, our mission is to leverage AI agents to enhance email communication efficiency and quality, making it easy for users to deploy and manage agent swarms with minimal setup.

## Big Picture Roadmap

- **Email Client Improvements:** Tackle challenges in email history construction, including quoting, mime types, encoding, and style decomposition for multi-agent systems. Develop a comprehensive email constructor to address compatibility across clients and improve history management and CSS handling.
- **SDK Integration:** Update `gpt.py` and `new_agent.py` for compatibility with OpenAI SDK 1.0. Expand functionality to include diverse API integrations and shortcode-driven API call parameters.
- **API Diversity:** Enable per-agent API settings, allowing for the integration of various AI models (e.g., LLAMA, Mixtral, OpenAI) with configurable parameters accessible via shortcode.
- **Security and Testing:** Implement watermarking, authentication, and passphrase systems for enhanced security. Develop a synthetic email server for robust testing and introduce token/credit counting for usage management.
- **Community Building:** Engage with the community to gather feedback and plan a large-scale refactor for more robust testing, database integration, and code optimization.

## API and Onboarding Enhancements

- **API Flexibility:** Customize LLM settings per agent, including temperature and max tokens. Develop an external API for multi-agent email control, facilitating applications like voice-to-email interactions.
- **Onboarding Improvements:** Revise the onboarding process to capture company-specific configurations and allow for domain customization.

## Functionality and Feature Updates

- **Inbox Management:** Automate emails for daily briefs and task lists, adapt inbox checking based on activity, and implement adaptive rate limiting.
- **Context Awareness:** Improve agent's context and date awareness, prevent duplicate responses, and integrate advanced functionalities like ABE within the system.
- **GitHub Integration:** Transition development from Replit to GitHub for enhanced collaboration and version control.

## HTML, CSS, and Flask App Enhancements

- **Email and CSS:** Address challenges with multiple agents in emails, refine CSS Grid designs, and resolve issues with HTML email content.
- **Flask App Development:** Enhance the Flask app for streamlined onboarding, configuration management, and secure access to agent profiles.

## Bug Fixes and Project Enhancements

No subject line leads to processed_threads.json errors. 

Header image / social image broken 

Using id to find agent makes it sensitive so it breaks if email address and agent id aren't the same. 

- **Data Consistency:** Address inconsistencies in relationship data formatting, PDF email quoting, and agent operation behaviors.
- **Functionality Improvements:** Enhance shortcode detection, fix issues with agent rendering, and optimize performance for features like summarization and thread reconciliation.

Our roadmap is ambitious, focusing on enhancing ATAT's core functionality, expanding its capabilities, and ensuring a secure, efficient, and user-friendly experience. Join us in revolutionizing email communication with AI, contributing your expertise, feedback, and innovation to shape the future of ATAT.
