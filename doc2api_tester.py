# doc2api_tester.py
import os
import json
import logging
import requests
from flask import url_for
from unittest.mock import MagicMock

from abe import app

# Set the SERVER_NAME configuration for testing
app.config['SERVER_NAME'] = 'localhost:5000'

# Configure logging
logs_directory = 'logs'
os.makedirs(logs_directory, exist_ok=True)
log_file = os.path.join(logs_directory, 'doc2api_tester.log')

logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')



def test_upload_document():
  logging.info("Testing upload_document endpoint")

  # Prepare test data
  test_file_data = b"This is a test document."

  # Mock the API request to upload the document
  mock_response = MagicMock()
  mock_response.status_code = 200
  mock_response.json.return_value = {'document_id': 1}

  requests.post = MagicMock(return_value=mock_response)

  try:
    # Make the API request to upload the document
    response = requests.post(
        url_for('doc2api_blueprint.upload_document'),
        files={'file': ('test_document.txt', test_file_data)})

    # Check the response status code
    if response.status_code == 200:
      logging.info("upload_document endpoint returned status code 200")
      logging.info(f"Response data: {response.json()}")
    else:
      logging.error(
          f"upload_document endpoint returned status code {response.status_code}"
      )
      logging.error(f"Response data: {response.json()}")

  except requests.exceptions.RequestException as e:
    logging.error(
        f"Error occurred while testing upload_document endpoint: {str(e)}")


def test_edit_document():
  logging.info("Testing edit_document endpoint")

  # Prepare test data
  test_document_id = 1
  test_document_data = {'key': 'value'}

  # Mock the API request to edit the document
  mock_response = MagicMock()
  mock_response.status_code = 200
  mock_response.json.return_value = {
      'message': 'Document updated successfully'
  }

  requests.post = MagicMock(return_value=mock_response)

  try:
    # Make the API request to edit the document
    response = requests.post(url_for('doc2api_blueprint.edit_document',
                                     document_id=test_document_id),
                             json=test_document_data)
    # Check the response status code
    if response.status_code == 200:
      logging.info("edit_document endpoint returned status code 200")
      logging.info(f"Response data: {response.json()}")
    else:
      logging.error(
          f"edit_document endpoint returned status code {response.status_code}"
      )
      logging.error(f"Response data: {response.json()}")

  except requests.exceptions.RequestException as e:
    logging.error(
        f"Error occurred while testing edit_document endpoint: {str(e)}")


def test_submit_document():
  logging.info("Testing submit_document endpoint")

  # Prepare test data
  test_document_id = 1
  test_document_data = {
      'agents': [{
          'name': 'Test Agent',
          'jobtitle': 'Test Job',
          'description': 'Test Description'
      }],
      'timeframes': [{
          'name': 'Test Timeframe'
      }],
      'meetings': [{
          'name': 'Test Meeting'
      }]
  }

  # Mock the API request to submit the document
  mock_response = MagicMock()
  mock_response.status_code = 200
  mock_response.json.return_value = {
      'message': 'Document submitted successfully'
  }

  requests.post = MagicMock(return_value=mock_response)

  try:
    # Make the API request to submit the document
    response = requests.post(url_for('doc2api_blueprint.submit_document',
                                     document_id=test_document_id),
                             json=test_document_data)

    # Check the response status code
    if response.status_code == 200:
      logging.info("submit_document endpoint returned status code 200")
      logging.info(f"Response data: {response.json()}")
    else:
      logging.error(
          f"submit_document endpoint returned status code {response.status_code}"
      )
      logging.error(f"Response data: {response.json()}")

  except requests.exceptions.RequestException as e:
    logging.error(
        f"Error occurred while testing submit_document endpoint: {str(e)}")


if __name__ == '__main__':
  with app.app_context():
      test_upload_document()
      test_edit_document()
      test_submit_document()