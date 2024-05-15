# test_api.py
import requests
import json
import logging
import os

from datetime import datetime

API_BASE_URL = os.environ['INTERNAL_API_TEST_BASE_URL']
API_KEY = os.environ['INTERNAL_API_TEST_KEY']


def configure_logging():
    log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log')
    logging.basicConfig(filename=f'logs/api_tester_{log_file_name}',
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


def get_schema():
    url = f"{API_BASE_URL}/api/schema"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        schema = response.json()
        logging.info(f"✅ Schema retrieved successfully")
        logging.info(f"Schema: {json.dumps(schema, indent=2)}")
        return schema
    else:
        logging.error(
            f"❌ Failed to retrieve schema. Status code: {response.status_code}"
        )
        return None


def test_agents(schema):
    if "agents" in schema:
        url = f"{API_BASE_URL}{schema['agents']['endpoint']}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            agents = response.json()
            if len(agents) > 0:
                logging.info(f"✅ Agents retrieved successfully")
                logging.info(f"Number of agents: {len(agents)}")
                logging.info(f"First agent: {json.dumps(agents[0], indent=2)}")
            else:
                logging.warning(f"⚠️ No agents found")
        else:
            logging.error(
                f"❌ Failed to retrieve agents. Status code: {response.status_code}"
            )
    else:
        logging.warning(f"⚠️ Agents endpoint not found in schema")


def test_meetings(schema):
    if "meetings" in schema:
        url = f"{API_BASE_URL}{schema['meetings']['endpoint']}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            meetings = response.json()
            if len(meetings) > 0:
                logging.info(f"✅ Meetings retrieved successfully")
                logging.info(f"Number of meetings: {len(meetings)}")
                logging.info(
                    f"First meeting: {json.dumps(meetings[0], indent=2)}")
            else:
                logging.warning(f"⚠️ No meetings found")
        else:
            logging.error(
                f"❌ Failed to retrieve meetings. Status code: {response.status_code}"
            )
    else:
        logging.warning(f"⚠️ Meetings endpoint not found in schema")


def test_timeframes(schema):
    if "timeframes" in schema:
        url = f"{API_BASE_URL}{schema['timeframes']['endpoint']}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            timeframes = response.json()
            if len(timeframes) > 0:
                logging.info(f"✅ Timeframes retrieved successfully")
                logging.info(f"Number of timeframes: {len(timeframes)}")
                logging.info(
                    f"First timeframe: {json.dumps(timeframes[0], indent=2)}")
            else:
                logging.warning(f"⚠️ No timeframes found")
        else:
            logging.error(
                f"❌ Failed to retrieve timeframes. Status code: {response.status_code}"
            )
    else:
        logging.warning(f"⚠️ Timeframes endpoint not found in schema")


def test_conversations(schema):
    if "conversations" in schema:
        url = f"{API_BASE_URL}{schema['conversations']['endpoint']}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            conversations = response.json()
            if len(conversations) > 0:
                logging.info(f"✅ Conversations retrieved successfully")
                logging.info(f"Number of conversations: {len(conversations)}")
                logging.info(
                    f"First conversation: {json.dumps(conversations[0], indent=2)}"
                )
            else:
                logging.warning(f"⚠️ No conversations found")
        else:
            logging.error(
                f"❌ Failed to retrieve conversations. Status code: {response.status_code}"
            )
    else:
        logging.warning(f"⚠️ Conversations endpoint not found in schema")


def main():
    configure_logging()
    schema = get_schema()
    if schema:
        test_agents(schema)
        test_meetings(schema)
        test_timeframes(schema)
        test_conversations(schema)


if __name__ == "__main__":
    main()
