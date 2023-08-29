import os
import imaplib


class EmailConnection:

  def setup_email_server(self):
    self.smtp_server = os.getenv('SMTP_SERVER')
    self.smtp_port = os.getenv('SMTP_PORT')
    self.smtp_username = os.getenv('SMTP_USERNAME')
    self.smtp_password = os.getenv('SMTP_PASSWORD')
    self.connect_to_imap_server()

  def connect_to_imap_server(self):
    self.imap_server = imaplib.IMAP4_SSL(os.getenv('IMAP_SERVER'))
    self.imap_server.login(self.smtp_username, self.smtp_password)
    self.imap_server.debug = 4

  def check_imap_connection(self):
    try:
      status, _ = self.imap_server.noop()
      return status == 'OK'
    except Exception as e:
      print(f"IMAP Connection error: {e}. Attempting to reconnect...")
      self.connect_to_imap_server()
      return False

  def restart_system(self):
    print("Restarting system...")
    self.connect_to_imap_server()
