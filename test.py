import unittest
from unittest.mock import patch, MagicMock
from email_server import EmailServer
from agent_selector import AgentSelector
from agent_manager import AgentManager
from contextlib import contextmanager


def truncate_field(field, max_length=140):
  return (field[:max_length] + '...') if len(field) > max_length else field


@contextmanager
def mock_imap_server():
  imap_server = MagicMock()
  imap_server.select.return_value = ('OK', None)
  imap_server.uid.return_value = ('OK', [b'Some Email Data'])
  yield imap_server


@contextmanager
def mock_smtp_server():
  smtp_server = MagicMock()
  yield smtp_server


class TestEmailServer(unittest.TestCase):

  def setUp(self):
    self.agent_manager = AgentManager()
    self.email_server = EmailServer(self.agent_manager, "mock_gpt_model")

  @patch('email_server.imaplib.IMAP4_SSL')
  def test_connect_to_imap_server(self, mock_imap_server_class):
    mock_imap_instance = mock_imap_server_class.return_value
    mock_imap_instance.login = MagicMock()

    self.email_server.connect_to_imap_server()

    mock_imap_instance.login.assert_called_once()


class TestAgentSelector(unittest.TestCase):

  def setUp(self):
    self.agent_selector = AgentSelector()
    self.agent_manager = AgentManager()

  def test_get_agent_names_from_content_and_emails(self):
    content = "!!Agent1!1 !!Agent2!2"
    recipient_emails = ["test1@example.com", "test2@example.com"]
    agents = self.agent_selector.get_agent_names_from_content_and_emails(
        content, recipient_emails, self.agent_manager)
    print(f"Agents Extracted: {truncate_field(str(agents))}")


class TestAgentManager(unittest.TestCase):

  def setUp(self):
    self.agent_manager = AgentManager()

  @patch('agent_manager.json.load')
  @patch('builtins.open', new_callable=MagicMock)
  def test_load_agents(self, mock_open, mock_json_load):
    mock_json_load.return_value = [{"id": "Agent1"}, {"id": "Agent2"}]
    self.agent_manager.load_agents()
    print(f"Loaded Agents: {truncate_field(str(self.agent_manager.agents))}")


if __name__ == '__main__':
  unittest.main()
