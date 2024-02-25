import imaplib
import getpass

# IMAP server details
IMAP_SERVER = 'localhost'
IMAP_PORT = 993

# User credentials
USERNAME = 'emailuser'
PASSWORD = '1234'
#getpass.getpass('Enter your password: ')

# Connect to the IMAP server
imap_server = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)

# Log in
try:
    imap_server.login(USERNAME, PASSWORD)
    print("Logged in successfully.")
except imaplib.IMAP4.error as e:
    print(f"Login failed: {e}")
    exit(1)

# Select the INBOX
status, messages = imap_server.select('INBOX')
if status != 'OK':
    print(f"Failed to select INBOX: {messages}")
    imap_server.logout()
    exit(1)

# Search for unseen emails
status, response = imap_server.search(None, 'UNSEEN')
if status != 'OK':
    print(f"Failed to search for unseen emails: {response}")
else:
    unseen_emails = response[0].split()
    print(f"Found {len(unseen_emails)} unseen emails.")

# Log out
imap_server.logout()
