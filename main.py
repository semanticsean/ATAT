"""ALPHA email server for agents."""
from email_server import EmailServer
from gpt import GPTModel
from agent_loader import AgentManager


def main():
  """Load modules and run orchestrator."""
  agent_loader = AgentManager()
  gpt = GPTModel()
  email_server = EmailServer(agent_loader, gpt)

  # Start the email server
  email_server.start()


if __name__ == "__main__":
  main()
