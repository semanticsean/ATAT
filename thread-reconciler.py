import imaplib
import json
import os
import email
from datetime import datetime
from email.utils import parsedate_to_datetime

print("Script started.")

# Fetch IMAP server details from environment variables
IMAP_SERVER = os.getenv('IMAP_SERVER')
IMAP_USER = os.getenv('SMTP_USERNAME')
IMAP_PASSWORD = os.getenv('SMTP_PASSWORD')

if not IMAP_SERVER or not IMAP_USER or not IMAP_PASSWORD:
  print("Missing environment variables for IMAP_SERVER, SMTP_USERNAME, or SMTP_PASSWORD.")
  exit(1)

print(f"Attempting to connect to IMAP server: {IMAP_SERVER} with user: {IMAP_USER}")

# Connect to the IMAP server
try:
  mail = imaplib.IMAP4_SSL(IMAP_SERVER)
  mail.login(IMAP_USER, IMAP_PASSWORD)
  mail.select('inbox')  # default mailbox is 'inbox'
  print("Connected to the IMAP server and selected inbox.")
except imaplib.IMAP4.error as e:
  print(f"IMAP connection or login failed: {e}")
  exit(1)

# Fetch all email UIDs
status, email_ids = mail.uid('search', None, 'ALL')
if status != 'OK':
  print("Error searching for emails.")
  exit(1)

print(f"Found emails: {len(email_ids[0].decode().split())} UIDs")

uids = email_ids[0].decode().split()

processed_threads = {}

for uid in uids:
  print(f"Processing UID: {uid}")
  status, data = mail.uid('fetch', uid, '(BODY.PEEK[HEADER] X-GM-THRID)')
  if status != 'OK' or not data or not data[0]:
    print(f"Skipped UID {uid} due to fetch error or empty data.")
    continue
  mail_data = data[0][1]
  if mail_data is None:
    print(f"Skipped UID {uid} because mail data is None.")
    continue

  msg = email.message_from_bytes(mail_data)
  thread_id = data[0][0].decode().split('X-GM-THRID ')[1].split(' ')[0]
  subject = msg.get('Subject', 'Unknown Subject')
  sender = msg.get('From', '')
  receiver = msg.get('To', '')
  in_reply_to = msg.get('In-Reply-To', '')
  references = msg.get('References', '')
  try:
    timestamp = parsedate_to_datetime(msg.get('Date')).strftime('%Y-%m-%d %H:%M:%S')
  except Exception as e:
    print(f"Failed to parse date for UID {uid}: {e}")
    continue

  if thread_id not in processed_threads:
    processed_threads[thread_id] = {"nums": {}, "metadata": {}}

  processed_threads[thread_id]['nums'][uid] = {"processed": True}
  processed_threads[thread_id]['metadata'] = {
      "subject": subject,
      "timestamp": timestamp,
      "sender": sender,
      "receiver": receiver,
      "in_reply_to": in_reply_to,
      "references": references
  }

try:
  mail.logout()
  print("Logged out from IMAP server.")
except Exception as e:
  print(f"An error occurred while logging out: {e}")
  exit(1)

with open('../processed_threads.json', 'w') as json_file:
    json.dump(processed_threads, json_file, indent=4)

print("Update completed.")
