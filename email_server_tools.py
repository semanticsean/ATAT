import email
import html
import imaplib
import json
import logging
import os
import re
import smtplib


def setup_email_server():
    self.smtp_server = os.getenv('SMTP_SERVER')
    self.smtp_port = os.getenv('SMTP_PORT')
    self.smtp_username = os.getenv('SMTP_USERNAME')
    self.smtp_password = os.getenv('SMTP_PASSWORD')
    self.connect_to_imap_server()

def connect_to_imap_server():
  self.imap_server = imaplib.IMAP4_SSL(os.getenv('IMAP_SERVER'))
  self.imap_server.login(self.smtp_username, self.smtp_password)
  self.imap_server.debug = 4

def check_imap_connection():
  try:
    response = self.imap_server.noop()
    status = response[0]
    return status == 'OK'
  except:
    return False

def mark_as_seen(num):
  # Code to mark the email as read
  self.imap_server.uid('store', num, '+FLAGS', '(\Seen)')



def update_processed_threads(message_id, num, subject):
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

def strip_html_tags(text):
  clean = re.compile('<.*?>')
  return re.sub(clean, '', html.unescape(text))

def load_processed_threads():
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

def restart_system():
  print("Restarting system...")
  self.connect_to_imap_server()

def aggregate_human_responses(human_threads, thread_content):
  print(f"Inside aggregate_human_responses - human_threads: {human_threads}")
  print(
      f"Inside aggregate_human_responses - thread_content: {thread_content}")

  # Extract and aggregate human responses from the thread_content
  human_responses = [
      response for thread in thread_content.split("\n\n")
      for response in human_threads if response in thread
  ]
  aggregated_human_content = "\n\n---\n\n".join(human_responses)
  return aggregated_human_content