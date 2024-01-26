import threading
import cards

from email_client import EmailClient
from gpt import GPTModel
from agent_loader import AgentManager


def run_flask_app():
  # Start the Flask app without the reloader 
  cards.app.run(debug=True, host='0.0.0.0', port=81, use_reloader=False)


def main():
  agent_loader = AgentManager()
  gpt = GPTModel()
  email_client = EmailClient(agent_loader, gpt)

  # Start the Flask app in a separate thread
  flask_thread = threading.Thread(target=run_flask_app)
  flask_thread.start()

  # Start the email server
  email_client.start()


if __name__ == "__main__":
  main()
