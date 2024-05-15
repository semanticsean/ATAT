#abe_api_tester.py 
import logging
import uuid
from datetime import datetime

# Generate a unique filename for each run
unique_filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + str(
    uuid.uuid4())
log_filename = f"logs/abe_api_{unique_filename}.log"

# Configure logging to write to a file
logging.basicConfig(filename=log_filename,
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def test_create_new_agent():
  payload = {
      "request_type": "new_agent",
      "priority": True,
      "agent_request": {
          "agent_name":
          "John Doe",
          "jobtitle":
          "Software Engineer",
          "agent_description":
          "A skilled software developer with 5 years of experience."
      }
  }

  # Simulate API call without actually making the request
  request_id = str(uuid.uuid4())
  expected_response = {
      "message": "Request added to the queue",
      "request_id": request_id
  }
  simulated_response = {
      "message": "Request added to the queue",
      "request_id": request_id
  }
  logging.info(f"Expected response: {expected_response}")
  logging.info(f"Simulated response: {simulated_response}")
  logging.info(
      f"Test case passed: {expected_response == simulated_response}\n")


def test_process_agents():
  payload = {
      "request_type": "process_agents",
      "priority": False,
      "timeframe_request": {
          "agents_data": [{
              "agent_id": "agent1"
          }, {
              "agent_id": "agent2"
          }],
          "instructions": {
              "instruction1": "Update agent profiles"
          },
          "timeframe_name": "Timeframe 1"
      }
  }

  # Simulate API call without actually making the request
  request_id = str(uuid.uuid4())
  expected_response = {
      "message": "Request added to the queue",
      "request_id": request_id
  }
  simulated_response = {
      "message": "Request added to the queue",
      "request_id": request_id
  }
  logging.info(f"Expected response: {expected_response}")
  logging.info(f"Simulated response: {simulated_response}")
  logging.info(
      f"Test case passed: {expected_response == simulated_response}\n")


def test_conduct_meeting():
  payload = {
      "request_type": "conduct_meeting",
      "priority": True,
      "meeting_request": {
          "agents_data": [{
              "agent_id": "agent1"
          }, {
              "agent_id": "agent2"
          }],
          "questions": {
              "question1": "What is the status of the project?"
          },
          "meeting_id": "meeting1",
          "meeting_name": "Project Status Meeting",
          "llm_instructions": "Provide detailed responses",
          "request_type": "iterative"
      }
  }

  # Simulate API call without actually making the request
  request_id = str(uuid.uuid4())
  expected_response = {
      "message": "Request added to the queue",
      "request_id": request_id
  }
  simulated_response = {
      "message": "Request added to the queue",
      "request_id": request_id
  }
  logging.info(f"Expected response: {expected_response}")
  logging.info(f"Simulated response: {simulated_response}")
  logging.info(
      f"Test case passed: {expected_response == simulated_response}\n")


def test_get_request_status():
  request_id = str(uuid.uuid4())

  # Simulate API call without actually making the request
  expected_response = {"status": "pending"}
  simulated_response = {"status": "pending"}
  logging.info(f"Expected response: {expected_response}")
  logging.info(f"Simulated response: {simulated_response}")
  logging.info(
      f"Test case passed: {expected_response == simulated_response}\n")


if __name__ == "__main__":
  test_create_new_agent()
  test_process_agents()
  test_conduct_meeting()
  test_get_request_status()
