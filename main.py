import threading
import cards
import json
import os
import subprocess
from dotenv import load_dotenv
import os

load_dotenv()

from email_client import EmailClient
from gpt import GPTModel
from agent_loader import AgentManager
 
domain_name = os.environ.get('DOMAIN_NAME', 'semantic-life.com')  
company_name = os.environ.get('COMPANY_NAME')

def run_flask_app():
    # Start the Flask app without the reloader
    cards.app.run(debug=True, host='0.0.0.0', port=81, use_reloader=False)

def check_and_add_agent():
    agents_file = 'agents/agents.json'
    if os.path.exists(agents_file):
        with open(agents_file, 'r') as file:
            agents = json.load(file)
        if not agents:  # List is empty
            print("No agents found, adding new agent...")
            subprocess.call(['python', 'new_agent.py'], cwd='agents')

def main():
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    # Check for and add new agents
    check_and_add_agent()

    agent_loader = AgentManager()
    gpt = GPTModel()
    email_client = EmailClient(agent_loader, gpt)

    # Start the email server
    email_client.start()

if __name__ == "__main__":
    main()
