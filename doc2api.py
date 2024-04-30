# doc2api.py
import os
import json
import bleach
import uuid
import logging
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, redirect, url_for
from models import db, User, Timeframe, Meeting, Agent, Document
from abe_api_internal import APIRequest, AgentRequest, TimeframeRequest, MeetingRequest
from abe_gpt import generate_new_agent
from openai import OpenAI

doc2api_blueprint = Blueprint('doc2api_blueprint', __name__)

ALLOWED_EXTENSIONS = {'doc', 'pdf', 'md', 'txt', 'json'}
client = OpenAI()

# Configure logging
logs_directory = 'logs'
os.makedirs(logs_directory, exist_ok=True)
log_file = os.path.join(logs_directory, 'doc2api.log')

logging.basicConfig(filename=log_file,
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def allowed_file(filename):
  return '.' in filename and filename.rsplit(
      '.', 1)[1].lower() in ALLOWED_EXTENSIONS


def clean_text(text):
  # Clean and bleach the text to remove any errant characters
  cleaned_text = bleach.clean(text, tags=[], strip=True)
  return cleaned_text


@doc2api_blueprint.route('/upload_document', methods=['POST'])
def upload_document():
  logging.info("Received request to upload document")

  if 'file' not in request.files:
    logging.error("No file uploaded")
    return jsonify({'error': 'No file uploaded'}), 400

  file = request.files['file']
  if file.filename == '':
    logging.error("No file selected")
    return jsonify({'error': 'No file selected'}), 400

  if file and allowed_file(file.filename):
    filename = secure_filename(file.filename)
    file_path = os.path.join('uploads', filename)
    file.save(file_path)

    with open(file_path, 'r') as f:
      document_text = f.read()

    # Clean the document text
    cleaned_text = clean_text(document_text)

    # Save the cleaned document text to the user's record in the database
    current_user = User.query.get(
        1)  # Replace with the appropriate user retrieval logic
    current_user.document_text = cleaned_text
    db.session.commit()

    # Prepare the API payload for GPT-4-turbo
    with open('abe/doc2api_instructions.json', 'r') as f:
      doc2api_instructions = json.load(f)

    system_prompt = doc2api_instructions['system_prompt']
    user_prompt = f"Document text:\n{cleaned_text}\n\n"

    # Append the agent list, timeframe list, and meeting list to the user prompt
    agents = Agent.query.all()
    timeframes = Timeframe.query.all()
    meetings = Meeting.query.all()

    user_prompt += "Agents:\n"
    for agent in agents:
      user_prompt += f"- ID: {agent.id}, Name: {agent.data.get('name', '')}, Job Title: {agent.data.get('jobtitle', '')}\n"

    user_prompt += "\nTimeframes:\n"
    for timeframe in timeframes:
      user_prompt += f"- ID: {timeframe.id}, Name: {timeframe.name}\n"

    user_prompt += "\nMeetings:\n"
    for meeting in meetings:
      user_prompt += f"- ID: {meeting.id}, Name: {meeting.name}\n"

    payload = {
        "model":
        "gpt-4-turbo-preview",
        "messages": [{
            "role": "system",
            "content": system_prompt
        }, {
            "role": "user",
            "content": user_prompt
        }]
    }

    # Call the GPT-4-turbo API with the payload
    response = client.chat.completions.create(**payload)

    # Extract the structured JSON response
    structured_response = json.loads(response.choices[0].message.content)

    # Store the structured response in the database
    document_data = {
        'user_id': current_user.id,
        'filename': filename,
        'data': structured_response
    }
    document = Document(**document_data)
    db.session.add(document)
    db.session.commit()

    logging.info(f"Document uploaded successfully. Document ID: {document.id}")
    return jsonify({'document_id': document.id}), 200

  logging.error("Invalid file type")
  return jsonify({'error': 'Invalid file type'}), 400


@doc2api_blueprint.route('/edit_document/<int:document_id>',
                         methods=['GET', 'POST'])
def edit_document(document_id):
  logging.info(f"Received request to edit document with ID: {document_id}")

  document = Document.query.get(document_id)
  if not document:
    logging.error(f"Document with ID {document_id} not found")
    return jsonify({'error': 'Document not found'}), 404

  if request.method == 'POST':
    # Update the document data based on the form submission
    document.data = request.json
    db.session.commit()

    logging.info(f"Document with ID {document_id} updated successfully")
    return jsonify({'message': 'Document updated successfully'}), 200

  # Render the form for editing the document data
  logging.debug(f"Returning document data for editing: {document.data}")
  return jsonify(document.data), 200


@doc2api_blueprint.route('/submit_document/<int:document_id>',
                         methods=['POST'])
def submit_document(document_id):
  logging.info(f"Received request to submit document with ID: {document_id}")

  document = Document.query.get(document_id)
  if not document:
    logging.error(f"Document with ID {document_id} not found")
    return jsonify({'error': 'Document not found'}), 404

  current_user = User.query.get(
      1)  # Replace with the appropriate user retrieval logic

  # Process the document data and make API calls
  for agent_data in document.data.get('agents', []):
    agent_id = agent_data.get('id')
    if not agent_id:
      # Create a new agent if the agent ID doesn't exist
      new_agent = generate_new_agent(agent_name=agent_data.get('name', ''),
                                     jobtitle=agent_data.get('jobtitle', ''),
                                     agent_description=agent_data.get(
                                         'description', ''),
                                     current_user=current_user)
      agent_id = new_agent.id
      agent_data['id'] = agent_id

    # Create an API request for the agent
    agent_request = AgentRequest(**agent_data)
    api_request = APIRequest(request_type='new_agent',
                             agent_request=agent_request)

    # Make the API call to process the agent request
    try:
      response = requests.post(url_for('api.create_request', _external=True),
                               json=api_request.dict(),
                               headers={'Content-Type': 'application/json'})
      response.raise_for_status()
      logging.info(
          f"Agent request processed successfully. Response: {response.json()}")
    except requests.exceptions.RequestException as e:
      logging.error(f"Error processing agent request: {str(e)}")
      return jsonify({'error':
                      f'Error processing agent request: {str(e)}'}), 500

  for timeframe_data in document.data.get('timeframes', []):
    # Create an API request for the timeframe
    timeframe_request = TimeframeRequest(**timeframe_data)
    api_request = APIRequest(request_type='process_agents',
                             timeframe_request=timeframe_request)

    # Make the API call to process the timeframe request
    try:
      response = requests.post(url_for('api.create_request', _external=True),
                               json=api_request.dict(),
                               headers={'Content-Type': 'application/json'})
      response.raise_for_status()
      logging.info(
          f"Timeframe request processed successfully. Response: {response.json()}"
      )
    except requests.exceptions.RequestException as e:
      logging.error(f"Error processing timeframe request: {str(e)}")
      return jsonify(
          {'error': f'Error processing timeframe request: {str(e)}'}), 500

  for meeting_data in document.data.get('meetings', []):
    # Create an API request for the meeting
    meeting_request = MeetingRequest(**meeting_data)
    api_request = APIRequest(request_type='conduct_meeting',
                             meeting_request=meeting_request)

    # Make the API call to process the meeting request
    try:
      response = requests.post(url_for('api.create_request', _external=True),
                               json=api_request.dict(),
                               headers={'Content-Type': 'application/json'})
      response.raise_for_status()
      logging.info(
          f"Meeting request processed successfully. Response: {response.json()}"
      )
    except requests.exceptions.RequestException as e:
      logging.error(f"Error processing meeting request: {str(e)}")
      return jsonify({'error':
                      f'Error processing meeting request: {str(e)}'}), 500

  logging.info(f"Document with ID {document_id} submitted successfully")
  return jsonify({'message': 'Document submitted successfully'}), 200
