import email
import html
import imaplib
import json
import logging
import os
import re
import smtplib
import quopri
import tempfile
import shutil
 
from time import sleep
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import getaddresses
from contextlib import contextmanager

from pdf2text import extract_pdf_text
from shortcode import handle_document_short_code
from agent_operator import AgentSelector


class EmailClient:

  # INIT & SETUP EMAIL ACCESS

  def __init__(self, agent_loader, gpt, testing=False):
    logging.basicConfig(filename='email_client.log',
                        level=logging.INFO,
                        format='%(asctime)s [%(levelname)s]: %(message)s')
    self.agent_loader = agent_loader
    self.gpt = gpt
    self.testing = testing
    self.setup_email_client()
    self.processed_threads = self.load_processed_threads()
    self.agent_operator = AgentSelector()
    self.conversation_threads = {}
    self.openai_api_key = os.getenv('OPENAI_API_KEY')

  def setup_email_client(self):
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
      response = self.imap_server.noop()
      status = response[0]
      return status == 'OK'
    except:
      return False

  def start(self):
    print("Started email server")
    restart_counter = 0
    MAX_RESTARTS = 500
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

      self.process_thread()

      print(
          f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sleeping for {sleep_time} seconds."
      )

      for i in range(
          sleep_time, 0,
          -30):  # Decreasing sleep time by 10 seconds in each iteration
        print(f"Sleeping... {i} seconds remaining.")
        sleep(30)  # Sleep for 10 seconds

      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      print(f"[{timestamp}] Resuming processing.")

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

  def restart_system(self):
    print("Restarting system...")
    self.connect_to_imap_server()

  # HANDLE THREAD PROCESSING

  def save_processed_threads(self):
    file_path = "processed_threads.json"
    with tempfile.NamedTemporaryFile('w',
                                     dir=os.path.dirname(file_path),
                                     delete=False) as tmp_file:
      json.dump(self.processed_threads, tmp_file)
      tmp_file.flush()
    shutil.move(tmp_file.name, file_path)

  def load_processed_threads(self):
    file_path = "processed_threads.json"
    if os.path.exists(file_path):
      with open(file_path, 'r') as file:
        try:
          threads = json.load(file)
          #print(f"Debug: Loaded processed_threads: {threads}")

          self.validate_processed_threads(threads)
          return threads
        except json.JSONDecodeError:
          print(
              "Error decoding processed_threads.json. Returning an empty list."
          )
          return {}

  def validate_processed_threads(self, threads):
    if not isinstance(threads, dict):
      raise ValueError("Processed threads must be a dictionary.")
    for x_gm_thrid, data in threads.items():
      if 'nums' not in data or not (isinstance(data['nums'], list)
                                    or isinstance(data['nums'], dict)):
        raise ValueError(f"Invalid 'nums' field for {x_gm_thrid}.")
      if 'metadata' not in data or not isinstance(data['metadata'], dict):
        raise ValueError(f"Invalid 'metadata' field for {x_gm_thrid}.")

  def update_processed_threads(self, message_id, x_gm_thrid, num, subject,
                               in_reply_to, references, sender, receiver):
    timestamp = datetime.now()
    num_str = str(num)

    # Convert receiver to a list if it's not already
    if isinstance(receiver, str):
      receiver = [receiver]
    elif not isinstance(receiver, list):
      receiver = list(receiver)  # Convert to list if it's another iterable

    # Initialize the thread record if it doesn't exist
    if x_gm_thrid not in self.processed_threads:
      self.processed_threads[x_gm_thrid] = {'nums': {}, 'metadata': {}}

    # Add the new UID under the existing thread ID
    self.processed_threads[x_gm_thrid]['nums'][num_str] = {'processed': True}

    # Update metadata
    self.processed_threads[x_gm_thrid]['metadata'] = {
        'subject': subject,
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'sender': sender,
        'receiver': ','.join(receiver),  # Joining the list of emails
        'in_reply_to': in_reply_to,
        'references': references
    }
    self.save_processed_threads()

  #  PROCESS EMAILS

  def is_email_processed(self, x_gm_thrid, num):
    num_str = str(num)
    if x_gm_thrid in self.processed_threads:
      if num_str in self.processed_threads[x_gm_thrid]['nums']:
        if self.processed_threads[x_gm_thrid]['nums'][num_str].get(
            'processed', False):
          print(
              f"Skipping already processed message with UID {num} in thread {x_gm_thrid}."
          )
          return True
    print(
        f"is_email_processed allowing response of UID {num} in thread {x_gm_thrid}."
    )
    return False

  def load_email(self, num):
    try:
      # Standardize the num to string type
      num_str = num.decode('utf-8') if isinstance(num, bytes) else str(num)

      # Fetch the email content by UID
      result, data = self.imap_server.uid('fetch', num_str,
                                          '(RFC822 X-GM-THRID)')
      if result != 'OK':
        print(f"Error fetching email content for UID {num}: {result}")
        return None, None, None, None, None, None, None, None

      # Initialize variables
      x_gm_thrid = None
      raw_email = None
      for response_part in data:
        if isinstance(response_part, tuple):
          match = re.search(r'X-GM-THRID (\d+)',
                            response_part[0].decode('utf-8'))
          if match:
            x_gm_thrid = match.group(1)
          raw_email = response_part[1].decode("utf-8")

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
      in_reply_to = email_message.get('In-Reply-To', '')
      references = email_message.get('References', '')

      content = ""
      pdf_attachments = []

      # Extract body and PDF content
      for part in email_message.walk():
        if part.get_content_type() == 'text/html':
          part.get_payload(decode=True).decode('utf-8')
        elif part.get_content_type() == 'text/plain':
          part.get_payload(decode=True).decode('utf-8')
          content_encoding = part.get("Content-Transfer-Encoding")
          payload = part.get_payload()
          if content_encoding == 'base64':
            content += base64.b64decode(payload).decode('utf-8')
          else:
            content += payload

        elif part.get_content_type() == 'application/pdf':
          pdf_data = part.get_payload(decode=True)
          pdf_text = extract_pdf_text(pdf_data)
          pdf_attachments.append({
              'filename': part.get_filename(),
              'text': pdf_text
          })

      # Append PDF contents to the content
      for pdf_attachment in pdf_attachments:
        pdf_text = pdf_attachment.get('text', '')
        if pdf_text:
          pdf_label = f"PDF: {pdf_attachment['filename']}"
          content += f"\n\n{pdf_label}\n{pdf_text}\n{pdf_label}\n"

      MAX_LIMIT = 350000
      if "!detail" in content or re.search(r"!summarize\.", content):
        MAX_LIMIT = 2000000

      # Check if the content is too long
      if len(content) > MAX_LIMIT:
        print(f"Content too long for UID {num}: {len(content)} characters.")
        self.send_error_email(from_, subject, "Content too long")
        self.mark_as_seen(num)
        self.update_processed_threads(message_id, x_gm_thrid, num, subject,
                                      in_reply_to, references, from_,
                                      ','.join(to_emails + cc_emails))
        return None, None, None, None, None, None, None, None

      # Return the content which now includes both the email body and the PDF contents
      return message_id, num, subject, content, from_, to_emails, cc_emails, references, in_reply_to, x_gm_thrid

    except Exception as e:
      print(f"Exception while processing email with UID {num}: {e}")
      import traceback
      print(traceback.format_exc())
      return None, None, None, None, None, None, None, None

  def process_thread(self):
    try:
      self.imap_server.select("INBOX")
      result, data = self.imap_server.uid('search', None, 'UNSEEN')
      if result != 'OK':
        print(f"Error searching for emails: {result}")
        return

      unseen_emails = data[0].split()
      thread_to_unseen = {}

      # Group unseen emails by thread
      for num in unseen_emails:
        email_data = self.load_email(num)
        if email_data is None or len(email_data) != 10:
          continue
        message_id, _, subject, _, from_, _, _, _, _, x_gm_thrid = email_data
        if self.is_email_processed(x_gm_thrid, num):
          continue

        # Use x_gm_thrid if available, else use subject
        if x_gm_thrid is None or x_gm_thrid == "":
          raise ValueError("x_gm_thrid is unavailable.")

        thread_key = x_gm_thrid

        if thread_key not in thread_to_unseen:
          thread_to_unseen[thread_key] = []

        thread_to_unseen[thread_key].append({
            "message_id": message_id,
            "num": num,
            "subject": subject,
            "from_": from_
        })

      # Process the most recent unseen email in each thread
      for thread_key, unseen_list in thread_to_unseen.items():
        unseen_list.sort(key=lambda x: int(x['num']), reverse=True)
        most_recent_unseen = unseen_list[0]
        if most_recent_unseen['from_'] == self.smtp_username:
          continue

        processed = self.process_single_thread(most_recent_unseen['num'])
        if not processed:
          print(f"Failed to process thread: {thread_key}")
        else:
          # Mark all other unseen emails in the same thread as seen
          for unseen_email in unseen_list[1:]:
            self.mark_as_seen(unseen_email['num'])
            if not thread_key:
              raise ValueError("thread_key is unavailable.")
            x_gm_thrid = thread_key

            self.update_processed_threads(unseen_email['message_id'],
                                          x_gm_thrid, unseen_email['num'],
                                          unseen_email['subject'], "", "",
                                          unseen_email['from_'], "")

    except Exception as e:
      print(f"Exception while processing emails: {e}")
      import traceback
      print(traceback.format_exc())

  def process_single_thread(self, num):
    processed = False
    try:
      message_id, num, subject, content, from_, to_emails, cc_emails, references, in_reply_to, x_gm_thrid = self.load_email(
          num)
      if not message_id:
        return processed  # Skip if email couldn't be processed

      successful = self.handle_incoming_email(from_, to_emails, cc_emails,
                                              content, subject, message_id,
                                              references, num, to_emails,
                                              cc_emails, content)
      if successful:
        self.mark_as_seen(num)
      processed = True

      return processed

    except Exception as e:
      print(f"Exception while processing emails: {e}")
      import traceback
      print(traceback.format_exc())
      return False

  def mark_as_seen(self, num):
    try:
      # Ensure num is decoded to a string if it's bytes
      num_str = num.decode('utf-8') if isinstance(num, bytes) else str(num)

      #print( f"Debug: Marking email as seen with UID: {num_str}, Type: {type(num_str)}" )

      print(
          f"Debug: IMAP Server state before STORE command: {self.imap_server.state}"
      )
      # Mark the email as seen
      result, _ = self.imap_server.uid('store', num_str, '+FLAGS', '(\Seen)')
      if result != 'OK':
        raise Exception(
            f"Failed to mark email as seen. IMAP server returned: {result}")
    except Exception as e:
      print(f"Exception while marking email as seen with UID {num}: {e}")
      import traceback
      print(traceback.format_exc())

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

  def strip_html_tags(self, text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html.unescape(text))

  def handle_incoming_email(self, from_, to_emails, cc_emails, thread_content,
                            subject, message_id, references, num,
                            initial_to_emails, initial_cc_emails,
                            original_content):

    print(
        f"Debug: Initial thread_content in handle_incoming_email: {thread_content[:200]}..."
    )

    try:
      print(
          f"Handling incoming email for thread with subject: {subject} and message_id: {message_id}"
      )
      shortcode_type = None
      print("Entered handle_incoming_email")
      #print(f"Debug: Email content at start of handle_incoming_email:{thread_content[:50]}")

      new_content = thread_content
      # Reset conversation history for a new email thread
      self.agent_operator.reset_for_new_thread()
      #print("Before human_threads initialization:", from_, to_emails,cc_emails, subject, message_id, references, num)
      human_threads = set()
      if from_ == self.smtp_username:
        print("Ignoring self-sent email.")
        print("Thread Content:", thread_content)
        return False
      print(f"Handling email from: {from_}")
      print(f"To emails: {to_emails}")
      print(f"CC emails: {cc_emails}")

      thread_content = self.strip_html_tags(thread_content)
      print(
          f"Handling shortcode for email with subject '{subject}' and content: {thread_content[:242]}..."
      )

      result = handle_document_short_code(
          thread_content, self.agent_operator.openai_api_key,
          self.agent_operator.conversation_history)

      if result is None:
        print(
            "Error: email server - handle_document_short_code returned None.")
        return False
      structured_response = result.get('structured_response')

      # Replace the shortcodes to prevent them from being processed again
      thread_content = re.sub(r'!\w+\(.*?\)', '', thread_content)

      if structured_response is not None:
        shortcode_type = structured_response.get("type")

      if shortcode_type in ["style", "detail"]:
        structured_response = result.get('content', None)
        new_content = result.get('new_content', thread_content)

      if shortcode_type == "detail":
        # Stitch the detailed responses together
        stitched_response = "\n\n".join(structured_response)
        # Use the stitched response as the thread_content
        thread_content = stitched_response

      elif shortcode_type is not None:
        print("Unhandled response_data type.")

      style_info = structured_response.get('structured_response',
                                           '') if structured_response else ''
      print("Structured response generated: ")
      self.agent_operator.conversation_history += f"\nStructured Response: {structured_response}"  # Update conversation history
      thread_content = new_content

      recipient_emails = to_emails + cc_emails

      thread_content = original_content

      agents = self.agent_operator.get_agent_names_from_content_and_emails(
          thread_content, recipient_emails, self.agent_loader, self.gpt)

      #print(f"Raw agents list before filtering: {agents}")

      # Filter out invalid agent info and ensure we unpack the expected format
      agents = [
          agent_info for agent_info in agents
          if isinstance(agent_info, tuple) and len(agent_info) == 2
      ]
      #print(f"Filtered agents: {agents}")
      if not agents:
        logging.warning("No valid agent info found")
        return False
      #print("There are valid agents to process.")
      print(f"Identified agents: {agents}")

      # Check if this thread has been processed before
      if message_id in self.processed_threads:
        print(
            f"Email with message_id {message_id} has already been processed.")
        return False

      # Prevent agents from responding to other agents
      if from_ in [
          agent["email"] for agent in self.agent_loader.agents.values()
      ]:
        print("Ignoring email from another agent.")
        return False

      all_responses_successful = True
      previous_responses = []

      # Ensure proper unpacking for the load_email function

      message_id, num, subject, content, from_, to_emails, cc_emails, references, in_reply_to, x_gm_thrid = self.load_email(
          num)

      missing_values = [
          var_name for var_name, value in locals().items()
          if value is None and var_name in [
              "message_id", "num", "subject", "content", "from_", "to_emails",
              "cc_emails", "references"
          ]
      ]

      if missing_values:
        print(
            f"Error processing email with UID {num}. Missing or None values: {', '.join(missing_values)}. Skipping this email."
        )
        return False

      # print(f"Unpacking agents: {agents}")

      for agent_info in agents:
        if len(agent_info) != 2:
          logging.error(
              f"Unexpected agent info format (length {len(agent_info)}): {agent_info}"
          )
          continue
        agent_name, order = agent_info

        # Reset the recipient list to the initial recipient list before processing this agent's response
        to_emails = list(initial_to_emails)
        cc_emails = list(initial_cc_emails)

        # Generate response
        if order == len(agents):
          # This is the last agent, append style info to the prompt
          response = self.agent_operator.get_response_for_agent(
              self.agent_loader,
              self.gpt,
              agent_name,
              order,
              agents,
              thread_content,
              additional_context=f"Note: {style_info}")
        else:
          response = self.agent_operator.get_response_for_agent(
              self.agent_loader, self.gpt, agent_name, order, agents,
              thread_content)

        if not response:  # Skip empty responses
          all_responses_successful = False
          continue

        # If the previous message in the thread was from an agent, skip sending the response
        if previous_responses and isinstance(
            previous_responses[-1], dict) and 'from_' in previous_responses[
                -1] and previous_responses[-1]['from_'] in [
                    agent["email"]
                    for agent in self.agent_loader.agents.values()
                ]:

          # Check for explicit tags or '@@' shortcode in the content
          if "@@" not in thread_content and not any(
              f"@@({name})" in thread_content for name, _ in agents):
            #print("Thread Content:", thread_content)
            print(
                f"Skipping response from {agent_name} to prevent agent-to-agent loop."
            )
            continue
        human_threads.add(from_)

        if message_id not in self.conversation_threads:
          self.conversation_threads[message_id] = [thread_content]

        if '<html>' in thread_content:
          formatted_email_history = self.format_email_history_html(
              thread_content, from_,
              datetime.now().strftime('%a, %b %d, %Y at %I:%M %p'))
        else:
          formatted_email_history = self.format_email_history_plain(
              thread_content, from_,
              datetime.now().strftime('%a, %b %d, %Y at %I:%M %p'))

        
        self.conversation_threads[message_id].append(formatted_email_history)

        previous_responses.append(response)

        agent = self.agent_loader.get_agent(agent_name)
        if agent:
          to_emails = [
              email for email in to_emails if email.lower() != from_.lower()
              and email.lower() != agent["email"].lower()
          ]
          cc_emails = [
              email for email in cc_emails if email.lower() != from_.lower()
              and email.lower() != agent["email"].lower()
          ]

          to_emails_without_agent = [
              email for email in to_emails
              if email.lower() != self.smtp_username.lower()
          ]
          cc_emails_without_agent = [
              email for email in cc_emails
              if email.lower() != self.smtp_username.lower()
          ]

          if from_ not in to_emails_without_agent and from_ != self.smtp_username:
            to_emails_without_agent.append(from_)

          if to_emails_without_agent or cc_emails_without_agent:
            print(f"Sending email to: {to_emails_without_agent}")
            print(f"CC: {cc_emails_without_agent}")

          if message_id in self.conversation_threads:
            self.conversation_threads[message_id].append(response)

          # Collect the email history of the thread
          email_history = '\n'.join(
              self.conversation_threads.get(message_id, [])[:-1])

          # Format the email history based on content type
          formatted_email_history_html = self.format_email_history_html(
              email_history, from_,
              datetime.now().strftime('%a, %b %d, %Y at %I:%M %p'))

          formatted_email_history_plain = self.format_email_history_plain(
              email_history, from_,
              datetime.now().strftime('%a, %b %d, %Y at %I:%M %p'))

          # Formatting response and history in both plain text and HTML
          response_plain = MIMEText(response, 'plain', 'utf-8')     
          response_plain.add_header('Content-Transfer-Encoding',
                                    'quoted-printable')

          response_with_breaks = response.replace('\n', '<br/>')

          response_html = MIMEText(
              f"<html><body>{response_with_breaks}</body></html>", 'html',
              'utf-8')
          response_html.add_header('Content-Transfer-Encoding',
                                   'quoted-printable')

          history_plain = MIMEText(formatted_email_history_plain, 'plain')
          history_html = MIMEText(
              f"<html><body>{formatted_email_history_html}</body></html>",
              'html')
          
          
          
          alternative_response = MIMEMultipart('alternative')
          #alternative_response.attach(response_plain)
          
          alternative_response.attach(response_html)
          

          alternative_history = MIMEMultipart('alternative')
          alternative_history.attach(history_plain)
          
          #alternative_history.attach(history_html)
          

          # Creating 'mixed' MIME container for the entire email
          msg = MIMEMultipart('mixed')
          msg.attach(alternative_response)
          
          msg.attach(alternative_history)
          
          
          

          try:
            self.send_email(from_email=self.smtp_username,
                            from_alias=agent["email"],
                            to_emails=to_emails_without_agent,
                            cc_emails=cc_emails_without_agent,
                            subject=f"Re: {subject}",
                            msg=msg,
                            message_id=message_id,
                            references=references)
            print("Email sent successfully.")
          except Exception as e:
            print(f"Exception while handling incoming email: {e}")
            import traceback
            print(traceback.format_exc())
            logging.error(f"Exception while handling incoming email: {e}")
            return False
          else:
            print(".")

      if all_responses_successful:
        # Concatenate all previous responses into a single string
        full_response_content = "\n\n".join(previous_responses)

        # Format the entire conversation history with 'gmail_quote' div only once
        formatted_email_history_html = self.format_email_history_html(
            full_response_content, from_,
            datetime.now().strftime('%a, %b %d, %Y at %I:%M %p'))
        
        if not references:
          print("No references found, possibly the first email in the thread.")
          references = message_id

        x_gm_thrid = references.split()[0]

        self.update_processed_threads(message_id, x_gm_thrid, num, subject,
                                      in_reply_to, references, from_,
                                      ','.join(to_emails + cc_emails))

      if message_id in self.conversation_threads:
        conversation_history = '\n'.join(self.conversation_threads[message_id])
        # print(f"START Conversation history: {conversation_history} END CONVERSATION HISTORY")

      return all_responses_successful

    except Exception as e:
      print(f"Exception in handle_incoming_email: {e}")
      import traceback
      print(traceback.format_exc())
      return False

  # FORMAT EMAIL HISTORY

  def format_email_history_html(self, history, from_email, date):
    
    try:
        decoded_history = quopri.decodestring(history.encode()).decode('utf-8')
    except UnicodeDecodeError:
        # If utf-8 decoding fails, fall back to 'latin1' encoding
        decoded_history = quopri.decodestring(history.encode()).decode('latin1')

    # Detect if history is already wrapped in 'gmail_quote' and avoid re-wrapping
    if '<div class="gmail_quote">' not in decoded_history:
        lines = decoded_history.split('\n')
        formatted_lines = ['<blockquote>{}</blockquote>'.format(line) for line in lines if line.strip()]
        combined_history = '\n'.join(formatted_lines)
        html_content = '<div class="gmail_quote">On {} {} wrote:<br>{}<br></div>'.format(date, from_email, combined_history)
    else:
        html_content = decoded_history  # Use as-is if already wrapped

    return html_content



  def format_email_history_plain(self, history, from_email, date):
    # Attempt to decode the history with utf-8, replace characters that are not utf-8
    try:
        decoded_history = quopri.decodestring(history.encode()).decode('utf-8')
    except UnicodeDecodeError:
        # If utf-8 decoding fails, fall back to 'latin1' encoding
        decoded_history = quopri.decodestring(history.encode()).decode('latin1')

    lines = decoded_history.split('\n')
    quoted_lines = ['> {}'.format(line) for line in lines if line.strip()]
    plain_text_content = 'On {} {} wrote:\n{}\n'.format(date, from_email, '\n'.join(quoted_lines))
    return plain_text_content



  # SEND EMAIL

  def send_email(self, from_email, from_alias, to_emails, cc_emails, subject, content, message_id=None, references=None):
    msg = MIMEMultipart('mixed')
    msg['From'] = f'"{from_alias}" <{from_email}>'
    msg['To'] = ', '.join(to_emails)
    if cc_emails:
        msg['Cc'] = ', '.join(cc_emails)
    msg['Subject'] = subject

    if message_id:
        msg['In-Reply-To'] = message_id
    if references:
        msg['References'] = references

    # Create the body of the message (a plain-text and an HTML version).
    text = "This is the plain text part of the email."
    html = """\
    <html>
      <head></head>
      <body>
        <p>This is the HTML part of the email.</p>
      </body>
    </html>
    """

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    with self.smtp_connection() as server:
        server.sendmail(from_email, to_emails + cc_emails, msg.as_string())
