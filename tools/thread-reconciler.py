# In the case that processed_threads.json is corrupted, run this to re-sync it with the inbox.

import imaplib
import json
import os
import email
from email.utils import parsedate_to_datetime

# Fetch IMAP server details from environment variables
IMAP_SERVER = os.getenv('IMAP_SERVER')
IMAP_USER = os.getenv('SMTP_USERNAME')
IMAP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Connect to the IMAP server
mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(IMAP_USER, IMAP_PASSWORD)
mail.select('inbox')  # default mailbox is 'inbox'

# Fetch all email UIDs
status, email_ids = mail.uid('search', None, 'ALL')
if status != 'OK':
  print("Error searching for emails.")
  exit(1)

# Convert byte response to list of UIDs
uids = email_ids[0].decode().split()

# Initialize a dictionary to store the thread details
processed_threads = {}

# Fetch details for each email
for uid in uids:
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
  message_id = msg.get('Message-ID')
  subject = msg.get('Subject', 'Unknown Subject')
  timestamp = parsedate_to_datetime(msg.get('Date')).isoformat()

  if thread_id in processed_threads:
    processed_threads[thread_id]['nums'].append(uid)
  else:
    processed_threads[thread_id] = {"nums": [uid], "subject": subject}

try:
  mail.logout()
except Exception as e:
  print(f"An error occurred while logging out: {e}")
  exit(1)  # Gracefully terminate the script

# Update processed_threads.json with new structure
with open('processed_threads.json', 'w') as json_file:
  json.dump(processed_threads, json_file, indent=4)

print("Update completed.")
