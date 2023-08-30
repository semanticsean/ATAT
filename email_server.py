import os
import re
import smtplib
import time
import json
import imaplib
import logging
import html
import email
from time import sleep
from datetime import datetime
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import getaddresses
from contextlib import contextmanager
from agent_selector import AgentSelector


class EmailServer:

  def __init__(self, agent_manager, gpt_model, testing=False):
    logging.basicConfig(filename='email_server.log',
                        level=logging.INFO,
                        format='%(asctime)s [%(levelname)s]: %(message)s')
    self.agent_manager = agent_manager
    self.gpt_model = gpt_model
    self.testing = testing
    self.setup_email_server()
    self.processed_threads = self.load_processed_threads()
    self.agent_selector = AgentSelector()
    self.conversation_threads = {}

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

  def start(self):
    print("Started email server")
    restart_counter = 0
    MAX_RESTARTS = 5
    sleep_time = 620  # Sleep time in seconds

    while True:
      try:
        self.run_server_loop(sleep_time)
      except imaplib.IMAP4.abort as e:
        print(f"IMAP connection aborted: {e}. Reconnecting..."
              )  # Fix for AttributeError
        self.restart_system()
        restart_counter += 1
        if restart_counter >= MAX_RESTARTS:
          print("Max restarts reached. Exiting.")
          break
      except AssertionError as e:
        print(f"Assertion error: {e}. Restarting system...")
        self.restart_system()
      except Exception as outer_exception:
        print(f"Outer exception occurred: {outer_exception}")
        self.restart_system()

  def run_server_loop(self, sleep_time):
    while True:
      if not self.check_imap_connection():
        print("IMAP connection lost. Reconnecting...")
        self.connect_to_imap_server()

      self.process_emails()

      print(
          f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sleeping for {sleep_time} seconds."
      )

      for i in range(
          sleep_time, 0,
          -10):  # Decreasing sleep time by 10 seconds in each iteration
        print(f"Sleeping... {i} seconds remaining.")
        sleep(10)  # Sleep for 10 seconds

      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      print(f"[{timestamp}] Resuming processing.")
      self.process_inbox()

  def check_imap_connection(self):
    try:
      status, _ = self.imap_server.noop()
      return status == 'OK'
    except:
      return False

  def restart_system(self):
    print("Restarting system...")
    self.connect_to_imap_server()

  def process_emails(self):
    try:
      result, data = self.imap_server.select("INBOX")  # Select the mailbox
      if result != 'OK':
        print(f"Error selecting INBOX: {result}")
        return

      result, data = self.imap_server.uid('search', None, 'UNSEEN')
      if result != 'OK':
        print(f"Error searching for emails: {result}")
        return

      unseen_emails = data[0].split()
      if unseen_emails:
        print(f"Found {len(unseen_emails)} unseen emails.")
        for num in unseen_emails:
          message_id, num, subject, content = self.process_email(num)
          if message_id is not None and num is not None:
            self.update_processed_threads(message_id, num, subject)
      else:
        print("No unseen emails found.")
    except Exception as e:
      print(f"Exception while processing emails: {e}")

  def get_message_id(self, num):
    try:
      result, data = self.imap_server.uid(
          'fetch', num, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
      if result != 'OK':
        print(f"Error fetching message ID for UID {num}: {result}")
        return None
    except Exception as e:
      print(f"Exception while fetching message ID for UID {num}: {e}")
      return None

    print(f"Fetching message ID result: {result}, data: {data}")  # Debug log
    if result != 'OK':
      print(f"Error fetching message ID for UID {num}: {result}")
      return None
    raw_email = data[0][1].decode("utf-8")
    email_message = email.message_from_string(raw_email)
    if not email_message:
      print(f"Error: email_message object is None for UID {num_str}")
      return None, None, None, None

    return email_message['Message-ID']

  def process_inbox(self):
    self.imap_server.select("INBOX")
    result, data = self.imap_server.uid('search', None, 'UNSEEN')
    if result != 'OK':
      print(f"Error searching for emails: {result}")
      return

    # Checking if there are any unseen emails
    unseen_emails = data[0].split()
    if unseen_emails:
      print(f"Found {len(unseen_emails)} unseen emails.")
      for num in unseen_emails:
        message_id, num, subject, content = self.process_email(num)
        if message_id is not None and num is not None:
          self.update_processed_threads(message_id, num, subject)
    else:
      print("No unseen emails found.")
      print(type(data), data)

  def mark_as_seen(self, num):
    num_str = num.decode('utf-8') if isinstance(
        num, bytes) else num  # Ensure UID is a string
    if not num_str.isdigit():
      print(f"Invalid UID provided: {num}. Not marking as seen.")
      return

    try:
      result, _ = self.imap_server.uid('store', num_str, '+FLAGS', '\\Seen')
      if result != 'OK':
        print(f"Error marking email as seen: {result}")
      else:
        print(f"Email marked as seen.")
    except Exception as e:
      print(
          f"Exception while marking email as seen for UID {num_str}: {str(e)}")

  def load_processed_threads(self):
    file_path = "processed_threads.json"
    if os.path.exists(file_path):
      with open(file_path, 'r') as file:
        try:
          threads = json.load(file)
          for thread_id, data in threads.items():
            # Check if data is a list, indicating the old format
            if isinstance(data, list):
              # Convert to the new format
              threads[thread_id] = {'nums': data, 'subject': 'Unknown Subject'}
          return threads
        except json.JSONDecodeError:
          print(
              "Error decoding processed_threads.json. Returning an empty list."
          )
          return {}
    return {}

  def update_processed_threads(self, message_id, num, subject):
    # Ensure that num is a string
    num_str = num.decode('utf-8') if isinstance(num, bytes) else num

    self.processed_threads[message_id] = {'num': num_str, 'subject': subject}

    temp_file = "processed_threads_temp.json"
    try:
      with open(temp_file, 'w') as file:
        json.dump(self.processed_threads, file)

      # If the above operation is successful, move the temp file
      os.rename(temp_file, "processed_threads.json")
    except Exception as e:
      print(f"Error updating processed threads: {e}")

  def process_email(self, num):
    try:
      # Ensure IMAP connection is active before processing
      assert self.check_imap_connection(
      ), "IMAP connection must be active before processing email"

      num_str = num.decode('utf-8')  # Decoding the UID from bytes to string
      print(f"Processing email with UID: {num_str}, type: {type(num_str)}")

      # Check for a valid UID
      if not num_str.isdigit():
        print(f"Invalid UID: {num_str}")
        return None, None, None, None

      result, data = self.imap_server.uid('fetch', num, '(RFC822)')
      if self.testing:
          mock_imap_instance.uid.side_effect = [('OK', [b'Some Email Data'])] * n_emails
      if result != 'OK':
          print(f"Error fetching email content for UID {num}: {result}")
          return None, None, None, None
      

      raw_email = data[0][1].decode("utf-8")
      email_message = email.message_from_string(raw_email)

      from_ = email_message['From']
      to_emails = [addr[1] for addr in getaddresses([email_message['To']])]
      cc_emails = [
          addr[1] for addr in getaddresses([email_message.get('Cc', '')])
      ]
      subject = email_message['Subject']
      message_id = email_message['Message-ID']
      references = email_message.get('References')

      content = ""
      if email_message.is_multipart():
        for part in email_message.get_payload():
          if part.get_content_type() == 'text/plain':
            content = part.get_payload()
          elif part.get_content_type() == 'text/html':
            content = self.strip_html_tags(
                part.get_payload(decode=True).decode('utf-8'))
      else:
        content = email_message.get_payload()

      email_handled = self.handle_incoming_email(from_, to_emails, cc_emails,
                                                 content, subject, message_id,
                                                 references)
      if email_handled:
        self.mark_as_seen(num)
        return message_id, num, subject, content

      print(f"Processing email with UID: {num}")
      print(self.imap_server.capabilities)
      return None, None, None, None

    except AssertionError as e:
      print(e)
      return None, None, None, None
    except Exception as e:
      print(f"Exception while processing email: {e}")
      return None, None, None, None, None

  def strip_html_tags(self, text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html.unescape(text))

  def restart_system(self):
    print("Restarting system...")
    self.connect_to_imap_server()

  def handle_incoming_email(self, from_, to_emails, cc_emails, content,
                            subject, message_id, references):
    if from_ == self.smtp_username:
      print("Ignoring self-sent email.")
      return False

    print(f"Handling email from: {from_}")
    print(f"To emails: {to_emails}")
    print(f"CC emails: {cc_emails}")

    recipient_emails = to_emails + cc_emails
    agents = self.agent_selector.get_agent_names_from_content_and_emails(
        content, recipient_emails, self.agent_manager)

    # Check if this thread has been processed before
    old_content = self.processed_threads.get(message_id, {}).get('content', '')
    new_content = content.replace(old_content, '').strip()

    if not agents:
      print("No agents identified from content.")
      return False

    all_responses_successful = True
    previous_responses = []

    for agent_name, order in agents:
      # Generate response
      response = self.agent_selector.get_response_for_agent(
          self.agent_manager, self.gpt_model, agent_name, order, agents,
          content)
      if not response:
        all_responses_successful = False
        continue

      if message_id not in self.conversation_threads:
        self.conversation_threads[message_id] = [content]
      self.conversation_threads[message_id].append(response)
      previous_responses.append(response)

      agent = self.agent_manager.get_agent(agent_name)
      if agent:
        to_emails_without_agent = [
            email for email in to_emails if email != self.smtp_username
        ]
        cc_emails_without_agent = [
            email for email in cc_emails if email != self.smtp_username
        ]
        if from_ != self.smtp_username:
          to_emails_without_agent.append(from_)

        if to_emails_without_agent or cc_emails_without_agent:
          print(f"Sending email to: {to_emails_without_agent}")
          print(f"CC: {cc_emails_without_agent}")

          try:
            self.send_email(from_email=self.smtp_username,
                            from_alias=agent["email"],
                            to_emails=to_emails_without_agent,
                            cc_emails=cc_emails_without_agent,
                            subject=f"Re: {subject}",
                            body=response,
                            message_id=message_id,
                            references=references)
            print("Email sent successfully.")
          except Exception as e:
            print(f"Failed to send email. Error: {e}")
            all_responses_successful = False

        else:
          print("No recipients found to send the email to.")

      # Moved the marking of the email as seen to here
      if all_responses_successful:
        self.mark_as_seen(message_id)

    return all_responses_successful

  @contextmanager
  def smtp_connection(self):
    server = smtplib.SMTP(self.smtp_server, self.smtp_port)
    server.starttls()
    server.login(self.smtp_username, self.smtp_password)
    try:
      yield server
    except Exception as e:
      logging.error(f"Exception occurred in smtp_connection: {e}")
    finally:
      server.quit()

  def send_email(self,
                 from_email,
                 from_alias,
                 to_emails,
                 cc_emails,
                 subject,
                 body,
                 message_id=None,
                 references=None):
    msg = MIMEMultipart()
    msg['From'] = f'"{from_alias}" <{from_email}>'  # Combining display name with email address
    msg['Sender'] = from_email  # The actual email address that sends the email
    msg['Reply-To'] = from_alias  # Replies will be directed here
    msg['To'] = ', '.join(to_emails)
    if cc_emails:
      msg['Cc'] = ', '.join(cc_emails)
    msg['Subject'] = subject
    if message_id:
      msg["In-Reply-To"] = message_id
    if references:
      msg["References"] = references
    msg.attach(MIMEText(body, 'plain'))

    all_recipients = to_emails + cc_emails

    with self.smtp_connection() as server:
      server.sendmail(from_email, all_recipients,
                      msg.as_string())  # The actual sender
