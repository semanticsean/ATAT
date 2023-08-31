import email
import html
import imaplib
import json
import logging
import os
import re
import smtplib
from contextlib import contextmanager
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import getaddresses
from time import sleep

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
        print(f"IMAP connection aborted: {e}. Reconnecting...")
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

  def check_imap_connection(self):
    try:
      status, _ = self.imap_server.noop()
      return status == 'OK'
    except:
      return False

  def load_processed_threads(self):
    file_path = "processed_threads.json"
    if os.path.exists(file_path):
      with open(file_path, 'r') as file:
        try:
          threads = json.load(file)
          for thread_id, data in threads.items():
            if isinstance(
                data,
                list):  # Check if data is a list, indicating the old format
              # Convert to the new format
              threads[thread_id] = {'nums': data, 'subject': 'Unknown Subject'}
          return threads
        except json.JSONDecodeError:
          print(
              "Error decoding processed_threads.json. Returning an empty list."
          )
          return {}
    return {}

  def restart_system(self):
    print("Restarting system...")
    self.connect_to_imap_server()

  def process_email(self, num):
    try:
      # Fetch the email content by UID
      result, data = self.imap_server.uid('fetch', num, '(RFC822)')
      if result != 'OK':
        print(f"Error fetching email content for UID {num}: {result}")
        return None, None, None, None, None, None, None, None

      raw_email = data[0][1].decode("utf-8")
      email_message = email.message_from_string(raw_email)
      if not email_message:
        print(f"Error: email_message object is None for UID {num}")
        return None, None, None, None, None, None, None, None

      # Extract headers and content
      from_ = email_message['From']
      to_emails = [addr[1] for addr in getaddresses([email_message['To']])]
      cc_emails = [
          addr[1] for addr in getaddresses([email_message.get('Cc', '')])
      ]
      subject = email_message['Subject']
      message_id = email_message['Message-ID']
      references = email_message.get('References', '')

      content = ""
      if email_message.is_multipart():
        for part in email_message.get_payload():
          if part.get_content_type() == 'text/plain':
            content = part.get_payload()
      else:
        content = email_message.get_payload()

      # Check if the content is too long
      if len(content) > 10000:
        self.send_error_email(from_, subject, "Content too long")
        self.mark_as_seen(num)
        self.update_processed_threads(message_id, num, subject)
        return None, None, None, None, None, None, None, None

      # Check if the email contains attachments
      if email_message.is_multipart() and any(
          part.get_filename() for part in email_message.get_payload()):
        self.send_error_email(from_, subject, "Attachments not allowed")
        self.mark_as_seen(num)
        self.update_processed_threads(message_id, num, subject)
        return None, None, None, None, None, None, None, None

      return message_id, num, subject, content, from_, to_emails, cc_emails, references

    except Exception as e:
      print(f"Exception while processing email: {e}")
      return None, None, None, None, None, None, None, None

  def send_error_email(self, to_email, original_subject, error_reason):
    error_file_path = "error-response-email.txt"
    if os.path.exists(error_file_path):
      with open(error_file_path, 'r') as file:
        error_content = file.read().replace("{error_reason}", error_reason)
    else:
      error_content = f"Thank you for using Semantic Life. Your email with the subject '{original_subject}' could not be processed because {error_reason}. Please try sending your email again. It may be that your email included an attachment, or that your email text was too long. If you did not get the agent you are looking for, email agent@semantic-life.com to ask for help. To customize your personal agent, email atlas@semantic-life.com. For sales inquiries about highly personalized synthetic copies of yourself and others, please email sean@semantic-life.com."

    subject = f"Please try again. || Error:  '{original_subject}'"
    with self.smtp_connection() as server:
      msg = MIMEText(error_content, 'plain')
      msg['From'] = self.smtp_username
      msg['To'] = to_email
      msg['Subject'] = subject
      server.sendmail(self.smtp_username, [to_email], msg.as_string())

  def process_emails(self):
    try:
      self.imap_server.select("INBOX")
      result, data = self.imap_server.uid('search', None, 'UNSEEN')
      if result != 'OK':
        print(f"Error searching for emails: {result}")
        return

      unseen_emails = data[0].split()
      if unseen_emails:
        print(f"Found {len(unseen_emails)} unseen emails.")
        for num in unseen_emails:
          try:
            message_id, num, subject, content, from_, to_emails, cc_emails, references = self.process_email(
                num)
            if message_id is not None and num is not None:
              successful = self.handle_incoming_email(from_, to_emails,
                                                      cc_emails, content,
                                                      subject, message_id,
                                                      references, num)
              if successful:
                self.mark_as_seen(num)
              # Moved the else block outside process_email
              else:
                print(
                    f"Email {num} failed to process, moving to the next email."
                )
            else:
              print(
                  f"Email {num} failed to process, moving to the next email.")
          except Exception as e:
            print(f"Exception while processing single email: {e}")
            logging.error(f"Exception while processing single email: {e}")

      else:
        print("No unseen emails found.")

    except Exception as e:
      print(f"Exception while processing emails: {e}")
      logging.error(f"Exception while processing emails: {e}")

  def mark_as_seen(self, num):
    # Code to mark the email as read
    self.imap_server.uid('store', num, '+FLAGS', '(\Seen)')

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

  def strip_html_tags(self, text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html.unescape(text))

  def handle_incoming_email(self, from_, to_emails, cc_emails, content,
                          subject, message_id, references, num):

    print("Entered handle_incoming_email")

    if from_ == self.smtp_username:
      print("Ignoring self-sent email.")
      return False

    print(f"Handling email from: {from_}")
    print(f"To emails: {to_emails}")
    print(f"CC emails: {cc_emails}")

    recipient_emails = to_emails + cc_emails
    agents = self.agent_selector.get_agent_names_from_content_and_emails(
        content, recipient_emails, self.agent_manager)

    print(f"Identified agents: {agents}")

    # Check if this thread has been processed before
    old_content = self.processed_threads.get(message_id, {}).get('content', '')
    content.replace(old_content, '').strip()

    # If no agents are found in the content, check for agents in the email addresses
    if not agents:
        print("No agents identified from content.")
        agents = self.agent_selector.get_agent_names_from_content_and_emails(
            "", recipient_emails, self.agent_manager)  # Only check recipient_emails
        if not agents:
            print("No agents identified from email addresses either.")
            self.send_error_email(from_, subject,
                                  "No agents identified from content or email addresses")
            self.mark_as_seen(num)
            self.update_processed_threads(message_id, num, subject)
            return False

    all_responses_successful = True
    previous_responses = []

    for agent_name, order in agents:
        # Generate response
        response = self.agent_selector.get_response_for_agent(
            self.agent_manager, self.gpt_model, agent_name, order, agents,
            content)
        if not response:  # Skip empty responses
            all_responses_successful = False
            continue

        if message_id in self.processed_threads:
            print(
                f"Email with message_id {message_id} has already been processed.")
            return False

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

    if all_responses_successful:
        self.update_processed_threads(
            message_id, num, subject)  # Update processed_threads.json

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
      server.sendmail(from_email, all_recipients, msg.as_string())
