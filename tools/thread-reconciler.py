import imaplib
import json
import os
import email

# Fetch IMAP server details from environment variables (replit secrets)
IMAP_SERVER = os.getenv('IMAP_SERVER')
IMAP_USER = os.getenv('SMTP_USERNAME')
IMAP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Connect to the IMAP server
mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(IMAP_USER, IMAP_PASSWORD)
mail.debug = 4
mail.select('inbox')  # default mailbox is 'inbox'

# Fetch all email UIDs
status, email_ids = mail.search(None, 'ALL')
if status != 'OK':
  print("Error searching for emails.")
  exit(1)

# Convert byte response to list of UIDs
uids = email_ids[0].decode().split()

# Initialize a dictionary to store the results
threads_dict = {}

# Fetch details for each email
for uid in uids:
  status, data = mail.fetch(uid, '(BODY.PEEK[HEADER])')
  if status != 'OK':
    continue
  mail_data = data[0][1]
  msg = email.message_from_bytes(mail_data)
  message_id = msg.get('Message-ID')
  subject = msg.get('Subject', 'Unknown Subject')
  if message_id not in threads_dict:
    threads_dict[message_id] = {"nums": [], "subject": subject}
  threads_dict[message_id]["nums"].append(int(uid))

# Update processed_threads.json
with open('processed_threads.json', 'w') as json_file:
  json.dump(threads_dict, json_file, indent=4)

mail.logout()
print("Update completed.")
