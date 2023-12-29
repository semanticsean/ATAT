import os
import smtplib
import imaplib
import logging

def setup_logging():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s [%(levelname)s]: %(message)s',
                        handlers=[
                            logging.StreamHandler()
                        ])

def check_imap_connection(imap_server, username, password):
    try:
        # Connect to the IMAP server and login
        imap_conn = imaplib.IMAP4_SSL(imap_server)
        imap_conn.login(username, password)
        logging.info(f"Successfully connected to IMAP server {imap_server}")
        
        # Check server capabilities
        logging.info(f"IMAP server capabilities: {imap_conn.capabilities}")
        
        imap_conn.logout()
    except Exception as e:
        logging.error(f"Failed to connect to IMAP server due to: {e}")

def check_smtp_connection(smtp_server, smtp_port, username, password):
    try:
        # Try SSL connection first
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(username, password)
            logging.info(f"Successfully connected to SMTP server {smtp_server} on port {smtp_port} with SSL")
    except Exception as e:
        logging.error(f"Failed to connect to SMTP server with SSL due to: {e}")
        try:
            # Try TLS connection next
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                logging.info(f"Successfully connected to SMTP server {smtp_server} on port {smtp_port} with TLS")
        except Exception as e2:
            logging.error(f"Failed to connect to SMTP server with TLS due to: {e2}")


if __name__ == "__main__":
    setup_logging()
    
    # Reading environment variables
    imap_server = os.environ.get('IMAP_SERVER', '')
    smtp_server = os.environ.get('SMTP_SERVER', '')
    smtp_port = os.environ.get('SMTP_PORT', '')
    username = os.environ.get('SMTP_USERNAME', '')
    password = os.environ.get('SMTP_PASSWORD', '')
    
    # Conduct tests
    check_imap_connection(imap_server, username, password)
    check_smtp_connection(smtp_server, smtp_port, username, password)
