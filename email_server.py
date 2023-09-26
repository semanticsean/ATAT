import email
import html
import imaplib
import json
import logging
import os
import re
import smtplib
import openai
from contextlib import contextmanager
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import getaddresses
from shortcode import handle_document_short_code
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
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.replied_threads = {}
        self.human_replied_threads = set()

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

            self.process_new_emails()

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
            response = self.imap_server.noop()
            status = response[0]
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

    def aggregate_human_responses(self, human_senders, thread_content):
        # Extract and aggregate human responses from the thread_content
        human_responses = [
            response for thread in thread_content.split("\n\n")
            for sender in human_senders if sender in thread
        ]
        aggregated_human_content = "\n\n---\n\n".join(human_responses)
        return aggregated_human_content

    def process_single_email(self, num):
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

            # Adjust character limit based on the presence of !detail or !summarize shortcodes
            MAX_LIMIT = 35000
            if "!detail" in content or re.search(r"!summarize\.", content):
                MAX_LIMIT = 200000

            # Check if the content is too long
            if len(content) > MAX_LIMIT:
                print(f"Content too long for UID {num}: {len(content)} characters.")
                self.send_error_email(from_, subject, "Content too long")
                self.mark_as_seen(num)
                self.update_processed_threads(message_id, num, subject)
                return None, None, None, None, None, None, None, None

            # Check if the email contains attachments
            if email_message.is_multipart() and any(
                    part.get_filename() for part in email_message.get_payload()):
                print(f"Attachments found in email with UID {num}")
                self.send_error_email(from_, subject, "Attachments not allowed")
                self.mark_as_seen(num)
                self.update_processed_threads(message_id, num, subject)
                return None, None, None, None, None, None, None, None

            return message_id, num, subject, content, from_, to_emails, cc_emails, references

        except Exception as e:
            print(f"Exception while processing email with UID {num}: {e}")
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

    def handle_incoming_email(self, from_, to_emails, cc_emails, aggregated_thread_content,
                              subject, message_id, references, num, initial_to_emails,
                              initial_cc_emails, thread_emails, thread_id):
        # Check for human replies in the thread
        if any(email_data['from_'] != self.smtp_username for email_data in thread_emails):
            self.human_replied_threads.add(thread_id)

        if thread_id not in self.human_replied_threads:
            return False

        # Get all the human emails in the thread
        human_emails = [
            email_data for email_data in thread_emails
            if email_data['from_'] != self.smtp_username
        ]
        human_senders = [email_data['from_'] for email_data in human_emails]

        # Generate aggregated_human_content using aggregate_human_responses
        aggregated_human_content = self.aggregate_human_responses(
            human_senders, aggregated_thread_content)

        last_email_sender = thread_emails[-1]['from_'] if thread_emails else None
        if last_email_sender in [agent["email"] for agent in self.agent_manager.agents.values()]:
            return True  # Skip if the last email was from an agent

        # Combining all recipients
        recipient_emails = list(set(to_emails + cc_emails))

        agents = self.agent_selector.get_agent_names_from_content_and_emails(
            aggregated_thread_content, recipient_emails, self.agent_manager, self.gpt_model)

        if thread_id not in self.replied_threads:
            self.replied_threads[thread_id] = {}

        all_responses_successful = True
        for agent_name, order in agents:
            if thread_id in self.replied_threads and agent_name in self.replied_threads[thread_id]:
                continue

            response = self.agent_selector.get_response_for_agent(
                self.agent_manager,
                self.gpt_model,
                agent_name,
                order,
                agents,
                aggregated_thread_content
            )

            if not response:
                all_responses_successful = False
                continue

            agent = self.agent_manager.get_agent(agent_name)
            if agent:
                try:
                    self.send_email(
                        from_email=self.smtp_username,
                        from_alias=agent["email"],
                        thread_emails=thread_emails,
                        cc_emails=cc_emails, 
                        subject=f"Re: {subject}",
                        body=response,
                        message_id=message_id,
                        references=references
                    )
                    self.replied_threads[thread_id][agent_name] = True
                except Exception as e:
                    print(f"Exception while sending email: {e}")
                    all_responses_successful = False

        if all_responses_successful:
            self.update_processed_threads(message_id, num, subject)

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

    def process_new_emails(self):
        try:
            self.imap_server.select("INBOX")
            result, data = self.imap_server.uid('search', None, 'UNSEEN')
            if result != 'OK':
                print(f"Error searching for emails: {result}")
                return

            unseen_emails = data[0].split()
            if unseen_emails:
                print(f"Found {len(unseen_emails)} unseen emails.")

                threads = {}
                for num in unseen_emails:
                    message_id, num, subject, content, from_, to_emails, cc_emails, references = self.process_single_email(
                        num)
                    if message_id:
                        thread_id = references.split()[0] if references else subject
                        if thread_id not in threads:
                            threads[thread_id] = []
                        threads[thread_id].append({
                            "message_id": message_id,
                            "num": num,
                            "subject": subject,
                            "content": content,
                            "from_": from_,
                            "to_emails": to_emails,
                            "cc_emails": cc_emails,
                            "references": references
                        })

                for thread_id, thread_emails in threads.items():
                    if thread_id not in self.conversation_threads:
                        self.conversation_threads[thread_id] = []
                    self.conversation_threads[thread_id].extend(thread_emails)
                    self.conversation_threads[thread_id].sort(key=lambda x: x.get('timestamp', 0))

                    # Aggregate thread content
                    aggregated_thread_content = " \n---NEW EMAIL---\n ".join(
                        [email_data['content'] for email_data in self.conversation_threads[thread_id]]
                    )
                    # Get the details of the latest email in the thread
                    latest_email = thread_emails[-1]
                    from_ = latest_email['from_']
                    to_emails = latest_email['to_emails']
                    cc_emails = latest_email['cc_emails']
                    subject = latest_email['subject']
                    message_id = latest_email['message_id']
                    references = latest_email['references']
                    num = latest_email['num']

                    # Handle the incoming email thread
                    successful = self.handle_incoming_email(
                        from_, to_emails, cc_emails, aggregated_thread_content, subject, message_id,
                        references, num, to_emails, cc_emails,
                        thread_emails, thread_id)

                    if successful:
                        # If the email thread was processed successfully, mark all emails in the thread as seen
                        for email_data in thread_emails:
                            self.mark_as_seen(email_data['num'])
                    else:
                        print(
                            f"Email thread {thread_id} failed to process, moving to the next thread."
                        )
            else:
                print("No unseen emails found.")
        except Exception as e:
            print(f"Exception while processing emails: {e}")
            import traceback
            print(traceback.format_exc())
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

    def send_email(self, from_email, from_alias, thread_emails, cc_emails, subject, body, message_id=None, references=None):
        print("=== Debugging send_email ===")
        
        # Extract unique 'From' email addresses from thread_emails
        original_senders = list(set([email_data['from_'] for email_data in thread_emails]))
        print(f"Original senders: {original_senders}")
    
        # Extract unique 'To' and 'Cc' email addresses from thread_emails
        all_recipients = list(set(
            [email_data['from_'] for email_data in thread_emails] +
            [email for email_data in thread_emails for email in email_data['to_emails']] +
            [email for email_data in thread_emails for email in email_data['cc_emails']]
        ))
        print(f"All recipients (before filtering): {all_recipients}")
    
        all_recipients = [
            email for email in all_recipients
            if email.lower() != from_email.lower()  # Exclude the agent's own email
        ]
        print(f"All recipients (after filtering): {all_recipients}")
    
        if not all_recipients:
            print("No valid recipients found. Aborting email send.")
            return
    
        msg = MIMEMultipart()
        msg['From'] = f'"{from_alias}" <{from_email}>'
        msg['Reply-To'] = ', '.join(original_senders)
        msg['To'] = ', '.join(all_recipients)
        msg['Cc'] = ', '.join(cc_emails)  # Add this line to include Cc emails
        msg['Subject'] = subject
        
        if message_id:
            msg["In-Reply-To"] = message_id
            print(f"In-Reply-To: {msg['In-Reply-To']}")
        
        if references:
            msg["References"] = references
            print(f"References: {msg['References']}")
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send the email to all unique recipients
        with self.smtp_connection() as server:
            print(f"Sending email to all_recipients: {all_recipients}")
            server.sendmail(from_email, all_recipients, msg.as_string())
        print("=== Email Sent ===")
    