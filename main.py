"""ALPHA email server for agents."""
from email_server import EmailServer
from gpt_model import GPTModel
from agent_loader import AgentManager


def main():
  """Load modules and run orchestrator."""
  agent_loader = AgentManager()
  gpt_model = GPTModel()
  email_server = EmailServer(agent_loader, gpt_model)

  # Start the email server
  email_server.start()


if __name__ == "__main__":
  main()
