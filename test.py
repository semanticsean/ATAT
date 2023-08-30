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
  imap_server.logout.assert_called()  # Ensure that logout is called


class TestAgentSelector(unittest.TestCase):

  def setUp(self):
    self.max_agents = 12
    self.agent_selector = AgentSelector(self.max_agents)
    self.agent_manager = AgentManager()

  def test_get_agent_names_from_content_and_emails_for_n_agents(self):
    n = 100
    content = " ".join([f"!!Agent{i}!{i}" for i in range(1, n + 1)])
    recipient_emails = [f"test{i}@example.com" for i in range(1, n + 1)]

    agents = self.agent_selector.get_agent_names_from_content_and_emails(
        content, recipient_emails, self.agent_manager)

    expected_agents = [(f"Agent{i}", i)
                       for i in range(1,
                                      min(n, self.max_agents) + 1)]

    self.assertEqual(
        len(agents), len(expected_agents),
        f"Extracted {len(agents)} agents, expected {len(expected_agents)}")

    print(f"Step 2: Agent extraction - Passed ({len(agents)} agents)")


class TestAgentManager(unittest.TestCase):

  def setUp(self):
    self.agent_manager = AgentManager()

  @patch('agent_manager.json.load')
  @patch('builtins.open', new_callable=MagicMock)
  def test_load_agents(self, mock_open, mock_json_load):
    mock_json_load.return_value = [{"id": "Agent1"}, {"id": "Agent2"}]
    self.agent_manager.load_agents()

    self.assertTrue(self.agent_manager.agents, "No agents loaded")
    print(
        f"Step 3: Agent loading - Passed ({len(self.agent_manager.agents)} agents)"
    )


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
    print("Step 1: IMAP server connection - Passed")

  def tearDown(self):

    self.email_server.imap_server.logout()


if __name__ == '__main__':
  unittest.main()
