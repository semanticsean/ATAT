# abe_api_external_test.py

import requests
import logging
import os
from datetime import datetime

API_URL = 'https://082c65da-f066-4d40-8f2b-5310ac929e85-00-8bl4x7087pru.riker.replit.dev'
API_KEY = '4cec93cac510e31ec21fdd2fb32e7432'

# Configure logging
logs_directory = 'logs'
if not os.path.exists(logs_directory):
    os.makedirs(logs_directory)
log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S_api_test.log')
log_file_path = os.path.join(logs_directory, log_file_name)
logging.basicConfig(filename=log_file_path, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def test_lookup_endpoint(item_type):
    url = f"{API_URL}/api/lookup?api_key={API_KEY}&type={item_type}&snippet_length=100"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        data = response.json()
        logging.info(f"Lookup results for {item_type}:")
        for item in data:
            logging.info(f"ID: {item['id']}, Snippet: {item.get('persona_snippet', item.get('summary_snippet', ''))}")
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred while testing lookup endpoint for {item_type}: {str(e)}")
        return []

def test_get_endpoint(item_type, item_id, include_images=False):
    url = f"{API_URL}/api/{item_type}?api_key={API_KEY}&id={item_id}&include_images={str(include_images).lower()}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        data = response.json()
        logging.info(f"Get results for {item_type} with ID {item_id}:")
        logging.info(data)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred while testing get endpoint for {item_type} with ID {item_id}: {str(e)}")

def main():
    logging.info("Starting API tests...")

    # Test lookup endpoint for agents, timeframes, and meetings
    agents_data = test_lookup_endpoint('agents')
    timeframes_data = test_lookup_endpoint('timeframes')
    meetings_data = test_lookup_endpoint('meetings')

    # Test get endpoint for a specific agent, timeframe, and meeting
    if agents_data:
        agent_id = agents_data[0]['id']
        test_get_endpoint('agents', agent_id)
    else:
        logging.warning("No agents found to test get endpoint.")

    if timeframes_data:
        timeframe_id = timeframes_data[0]['id']
        test_get_endpoint('timeframes', timeframe_id)
    else:
        logging.warning("No timeframes found to test get endpoint.")

    if meetings_data:
        meeting_id = meetings_data[0]['id']
        test_get_endpoint('meetings', meeting_id)
    else:
        logging.warning("No meetings found to test get endpoint.")

    logging.info("API tests completed.")

if __name__ == '__main__':
    main()