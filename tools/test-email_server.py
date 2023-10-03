import unittest
import logging
from unittest.mock import patch, Mock
from email_server import EmailServer  # Import your EmailServer class

# Configure logging
logging.basicConfig(filename='test_email_server.log',
                    level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s]: %(message)s')


class TestEmailServer(unittest.TestCase):

    def setUp(self):
        logging.info("Setting up test environment.")
        self.email_server = EmailServer(agent_manager=Mock(), gpt_model=Mock())
        self.email_server.imap_server = Mock()

    def tearDown(self):
        logging.info("Tearing down test environment.")

    @patch('email_server.imaplib.IMAP4_SSL')
    def test_check_imap_connection(self, mock_imap):
        logging.info("Testing check_imap_connection method.")
        
        # Test for a successful connection
        mock_imap.return_value.noop.return_value = ('OK', [])
        self.assertTrue(self.email_server.check_imap_connection())
        
        # Test for an unsuccessful connection
        mock_imap.return_value.noop.return_value = ('BAD', [])
        self.assertFalse(self.email_server.check_imap_connection())

    @patch('email_server.imaplib.IMAP4_SSL')
    def test_process_single_email(self, mock_imap):
        logging.info("Testing process_single_email method.")
        
        # Mocking the imap_server.uid call
        self.email_server.imap_server.uid.return_value = ('OK', [(b'1', b'some_raw_email_content')])
        
        # Call the function and capture the output
        message_id, num, subject, content, from_, to_emails, cc_emails, references = self.email_server.process_single_email('1')
        
        # Verify the output (Replace these with the actual expected values)
        self.assertIsNotNone(message_id)
        self.assertIsNotNone(num)

    @patch('email_server.AgentSelector')
    @patch('email_server.EmailServer.send_email')
    def test_handle_incoming_email(self, mock_send_email, mock_agent_selector):
        logging.info("Testing handle_incoming_email method.")
        
        # Mock data
        from_ = 'sender@example.com'
        to_emails = ['to1@example.com']
        cc_emails = []
        aggregated_thread_content = "Hello, this is a test."
        subject = "Test Subject"
        message_id = "12345"
        references = None
        num = '1'
        initial_to_emails = to_emails
        initial_cc_emails = cc_emails
        thread_emails = [{'from_': from_}]
        thread_id = "some_thread_id"
        
        # Execute the function
        result = self.email_server.handle_incoming_email(
            from_, to_emails, cc_emails, aggregated_thread_content,
            subject, message_id, references, num, initial_to_emails,
            initial_cc_emails, thread_emails, thread_id
        )
        
        # Verify the output
        self.assertTrue(result)
        
        # Verify send_email was called (if you expect it to be called)
        mock_send_email.assert_called()


if __name__ == '__main__':
    unittest.main()
