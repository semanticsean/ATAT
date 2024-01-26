"""ATAT - ALPHA: Email server for AI agents."""

from email_client import EmailClient
from gpt import GPTModel
from agent_loader import AgentManager


def main():
  """Load modules and run orchestrator."""
  agent_loader = AgentManager()
  gpt = GPTModel()
  email_client = EmailClient(agent_loader, gpt)

  # Start the email server
  email_client.start()


if __name__ == "__main__":
  main()
