#abe.py
import time
import threading
import os
import datetime
import logging
import uuid
import os
import shutil
import json
import datetime
import uuid
import random
import csv

from openai import OpenAI
from typing import ClassVar
from flask import request
from mirascope import Prompt, OpenAIChat
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from flask import current_app as app
from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

AGENTS_JSON_PATH = os.path.join('agents', 'agents.json')
IMAGES_BASE_PATH = os.path.join('agents', 'pics')
CURRENT_AGENTS_JSON_PATH = AGENTS_JSON_PATH

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_very_secret_key'

responses_data = {}
is_processing = False
final_html_path = ""
use_modified_agents_json = False
modified_agents_json_path = ""


class NoStatusFilter(logging.Filter):

  def filter(self, record):
    return '/status' not in record.getMessage()


def setup_logging():
  timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
  log_directory = os.path.join('logs')
  os.makedirs(log_directory, exist_ok=True)
  log_file = os.path.join(log_directory, f'{timestamp}.log')
  logging.basicConfig(filename=log_file,
                      level=logging.INFO,
                      format='%(asctime)s %(levelname)s: %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S')


logger = logging.getLogger('werkzeug')
logger.addFilter(NoStatusFilter())
setup_logging()


def initialize_session(unique_folder, agents_file_path):
  # Ensure base directories for session data are created
  html_folder = os.path.join(unique_folder, 'html')
  pics_folder = os.path.join(html_folder, 'pics')
  abe_folder = os.path.join(html_folder, 'abe')  # Additional directory for ABE-related files

  # Create necessary directories
  for folder in [pics_folder, abe_folder]:
      os.makedirs(folder, exist_ok=True)

  # Adjusted to copy and potentially modify JSON files as needed
  copy_and_truncate_json_files('.', html_folder)

  # Directly use the provided agents_file_path to read and then update agents.json at the correct location
  with open(agents_file_path, 'r') as file:
      agents = json.load(file)  # Load agents data from the provided path

      # Process photo paths as before
      for agent in agents:
          agent.setdefault("include", True)
          original_photo_path = agent.get('photo_path')
          if original_photo_path:
              photo_filename = os.path.basename(original_photo_path)
              new_photo_path = os.path.join(pics_folder, photo_filename)
              shutil.copy(original_photo_path, new_photo_path)
              # Update agent's photo_path to reflect the new location
              agent['photo_path'] = os.path.join('/static/output', os.path.basename(unique_folder), 'html', 'pics', photo_filename)

  # Save the updated agents JSON to the provided location, ensuring it matches the expected path in load_session_data
  with open(agents_file_path, 'w') as file:
      json.dump(agents, file, indent=4)






#FLASK
def send_auth_email(email_address):
  serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
  token = serializer.dumps(email_address, salt='email-confirm-salt')
  confirm_url = url_for('confirm_email', token=token, _external=True)
  html = render_template('auth_email.html', confirm_url=confirm_url)
  msg = Message('Email Authentication', recipients=[email_address], html=html)
  mail.send(msg)


@app.route('/dashboard')
def index():
  try:
    with open(AGENTS_JSON_PATH, 'r') as file:
      agents = json.load(file)
  except Exception as e:
    print(f"Failed to load or parse JSON file: {e}")
  for agent in agents:
    agent['photo_path'] = get_image_path(agent)
    if 'keywords' in agent and isinstance(agent['keywords'], list):
      agent['keywords'] = random.sample(agent['keywords'],
                                        min(len(agent['keywords']), 3))
    else:
      agent['keywords'] = []
  return render_template('dashboard.html', agents=agents)


@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    email_address = request.form['email']
    send_auth_email(email_address)
    return 'Check your email for an authentication link.'
  return render_template('login.html')


@app.route('/confirm/<token>')
def confirm_email(token):
  try:
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    email_address = serializer.loads(token,
                                     salt='email-confirm-salt',
                                     max_age=3600)
    # Here, authenticate the user based on email_address
    # For this example, you might set a session variable
    session['authenticated'] = True
    return redirect(url_for('index'))
  except:
    return 'The confirmation link is invalid or has expired.'


@app.route('/readme.html')
def readme():
  return render_template('readme.html')


def get_image_path(agent):
  # Retrieve the relative photo path from agent's data
  return agent.get('photo_path', 'default.png')


@app.route('/agents/pics/<filename>')
def agent_pics(filename):
  return send_from_directory(IMAGES_BASE_PATH, filename)


@app.route('/')
def home():
  return render_template('index.html')


def create_session_specific_agents_json(session_id):
  session_agents_dir = os.path.join('agents', 'session_agents', session_id)
  os.makedirs(session_agents_dir, exist_ok=True)
  session_agents_path = os.path.join(session_agents_dir, 'agents.json')

  # Copy the original agents.json to the session-specific path
  shutil.copy(os.path.join('agents', 'agents.json'), session_agents_path)

  return session_agents_path  # Just return the path


def copy_abe_files_for_session(session_id, abe_folder):
  """
    Copies ABE-related JSON files (abe-questions.json and abe-instructions.json)
    to the session-specific ABE directory.
    """
  # Paths for the source ABE files
  source_questions_path = 'abe/abe-questions.json'
  source_instructions_path = 'abe/abe-instructions.json'

  # Paths for the session-specific ABE files
  session_questions_path = os.path.join(abe_folder, 'abe-questions.json')
  session_instructions_path = os.path.join(abe_folder, 'abe-instructions.json')

  # Copy the ABE files to the session-specific directory
  shutil.copy(source_questions_path, session_questions_path)
  shutil.copy(source_instructions_path, session_instructions_path)



@app.route('/abe')
def abe():
    session_id = session.get('session_id')
    if not session_id:
        return redirect(url_for('home'))
    # Debugging: Print or log the session_id to inspect its value
    print(f"Session ID: {session_id}")
    unique_folder_path = f'/static/output/{session_id}/html/pics'
    agents, questions, instructions = load_session_data(session_id)
    return render_template('abe.html',
                           agents=agents,
                           questions=questions,
                           instructions=instructions,
                           unique_folder_path=unique_folder_path)



@app.route('/start_session', methods=['POST'])
def start_session():
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    agents_file_path = create_session_specific_agents_json(session_id)

    # Adjust unique_folder to point to the session's base folder directly, not nested inside 'html'
    unique_folder = os.path.join('static', 'output', session_id)
    initialize_session(unique_folder, agents_file_path)

    # Ensure the necessary directories exist
    os.makedirs(unique_folder, exist_ok=True)

    # Define abe_folder here correctly before using it
    abe_folder = os.path.join(unique_folder, 'abe')  # Correctly define abe_folder based on unique_folder
    os.makedirs(abe_folder, exist_ok=True)  # Ensure ABE directory exists correctly after defining abe_folder

    # Ensure ABE-related JSON files are present in the session-specific ABE directory
    copy_abe_files_for_session(session_id, abe_folder)

    return redirect(url_for('abe'))

@app.route('/start', methods=['POST'])
def start_process():
  global is_processing
  if is_processing:
    return jsonify({"error": "Process is already running"}), 400

  data = request.get_json()

  selected_agent_ids = data.get('selectedAgents', [])
  questions = data.get('questions', [])
  custom_instructions = data.get('instructions', '')
  modify_agents_json_flag = data.get('modify_agents_json', False)
  custom_modify_instructions = data.get('custom_modify_instructions', '')

  # Assuming modify_agents_json_instructions should be part of the request
  # If it's not part of the request, you'll need to define it before here
  modify_agents_json_instructions = data.get('modify_agents_json_instructions', 'Your default modification instructions')

  if not selected_agent_ids:
    return jsonify({"error": "No agents selected."}), 400

  session_id = session.get('session_id')
  if session_id is None:
    return jsonify({"error": "Session ID not found. Please restart the session."}), 400

  if not is_processing:
    # Corrected call with 7 arguments
    thread = threading.Thread(target=lambda: run_agent_process(
    app, session_id, selected_agent_ids, questions, custom_instructions,
    modify_agents_json_flag, modify_agents_json_instructions)) # Pass modify_agents_json_instructions to your processing function
    thread.start()
    is_processing = True
    return jsonify({"message": "Processing started"}), 202


@app.route('/status')
def status():
  global final_html_path
  if not is_processing and final_html_path:
    # Correcting the web accessible path if necessary
    web_accessible_path = final_html_path if final_html_path.startswith(
        '/static') else url_for('static', filename=final_html_path.strip('/'))
    return jsonify({
        "is_processing": False,
        "redirect": True,
        "final_html_path": web_accessible_path
    })
  else:
    return jsonify({
        "is_processing": True,
        "redirect": False,
        "final_html_path": None
    })


@app.route('/update_agent_inclusion', methods=['POST'])
def update_agent_inclusion():
  logging.info("Starting update_agent_inclusion process")
  try:
    data = request.get_json(force=True)
    logging.info(f"Received data for inclusion update: {data}")

    if 'agent_ids' in data and isinstance(
        data['agent_ids'], list) and 'include' in data and isinstance(
            data['include'], bool):
      agent_ids = data['agent_ids']
      include = data['include']
      logging.info(f"Agent IDs: {agent_ids}, Include: {include}")

      # Determine whether the session-specific agents.json or the default one should be used
      session_id = session.get('session_id', None)
      agents_file_path = AGENTS_JSON_PATH
      logging.info(f"Using agents file path: {agents_file_path}")

      # Update agents' inclusion status
      with open(agents_file_path, 'r+') as file:
        agents = json.load(file)
        updated = False
        for agent in agents:
          if str(agent['id']) in agent_ids:
            agent['include'] = include
            updated = True
            logging.info(
                f"Updated agent {agent['id']} inclusion status to {include}")

        # Save changes if any update occurred
        if updated:
          file.seek(0)
          json.dump(agents, file, indent=4)
          file.truncate()
          logging.info("Agents' inclusion status updated successfully")

      return jsonify({"message": "Inclusion status updated"}), 200
    else:
      logging.warning("Invalid request format for agent inclusion update")
      return jsonify({"error": "Invalid request format"}), 400
  except Exception as e:
    logging.exception("Failed to update agent inclusion", exc_info=e)
    return jsonify({"error":
                    "Server error while updating agent inclusion"}), 500


def remove_session_folder(path):
  """
  Removes the session-specific folder.
  """
  try:
    shutil.rmtree(path)
    logging.info(f"Successfully removed session folder: {path}")
  except Exception as e:
    logging.error(f"Failed to remove session folder {path}: {e}")


@app.route('/results')
def results():
  global final_html_path
  if final_html_path:
    logging.info(f"Attempting to serve HTML file: {final_html_path}")
    try:
      directory = os.path.dirname(final_html_path)
      file_name = os.path.basename(final_html_path)

      def cleanup(response):
        session_id = session.get('session_id')
        if session_id:
          session_folder = os.path.join('static', 'output', session_id)
          remove_session_folder(session_folder)
        return response

      logging.info(
          f"Serving from directory: {directory}, File name: {file_name}")
      return send_from_directory(directory, file_name)
    except Exception as e:
      logging.exception("Error serving HTML file")
  else:
    logging.info("No results available yet.")
  return "No results available yet."


def copy_agent_photos_to_session(agents_data, destination_folder):
  """
  Copies all agent photos to the specified destination folder.

  Args:
      agents_data: A list of dictionaries, each representing an agent.
      destination_folder: The destination folder where photos will be copied.
  """
  # Assuming the root directory contains the 'agents' directory directly
  root_directory = os.getcwd(
  )  # Adjust this if the 'agents' directory is located elsewhere

  for agent in agents_data:
    photo_path = agent.get("photo_path")
    if photo_path:
      # Construct the source path by appending the photo_path to the root directory
      # This assumes photo_path is a relative path from the root directory of the project
      source_photo_path = os.path.join(root_directory, photo_path)

      if os.path.exists(source_photo_path):
        try:
          # Ensure the destination folder exists
          os.makedirs(destination_folder, exist_ok=True)
          # Copy the photo
          destination_path = os.path.join(destination_folder,
                                          os.path.basename(photo_path))
          shutil.copy(source_photo_path, destination_path)
          logging.info(
              f"Copied photo for agent {agent['id']} to {destination_folder}")
        except Exception as e:
          logging.error(f"Failed to copy photo for agent {agent['id']}: {e}")
      else:
        logging.warning(
            f"Photo path does not exist for agent {agent['id']}: {source_photo_path}"
        )


class CustomAgentPrompt(Prompt):
  agent_json: str
  question: str
  template: ClassVar[str] = load_json_data(
      'abe/abe-instructions.json')['instructions']

  def __str__(self):
    return self.template.format(agent_json=self.agent_json,
                                question=self.question)


def ask_agents_questions(selected_agent_ids, questions):
  logging.info('Starting to ask agents questions.')
  agents_file_path = modified_agents_json_path if should_use_modified_agents(
  ) else AGENTS_JSON_PATH
  logging.info(f'Using agents file path: {agents_file_path}')

  try:
    with open(agents_file_path, 'r', encoding='utf-8') as file:
      agents = json.load(file)
    logging.info(f'Loaded {len(agents)} agents from {agents_file_path}.')
  except Exception as e:
    logging.error(f'Failed to load agents from {agents_file_path}: {e}')
    return {}

  filtered_agents = [
      agent for agent in agents if str(agent['id']) in selected_agent_ids
  ]
  logging.info(
      f'Filtered {len(filtered_agents)} agents based on selected IDs: {selected_agent_ids}'
  )

  data = {}
  for agent in filtered_agents:
    model = agent.get("model", "gpt-3.5-turbo")  # Default model
    logging.info(f'Processing agent ID {agent["id"]} with model {model}.')
    agent_data = {"id": agent['id'], "responses": []}
    chat = OpenAIChat(api_key=OPENAI_API_KEY, model=model)

    for question in questions['questions']:
      prompt = CustomAgentPrompt(agent_json=json.dumps(agent),
                                 question=question['text'])
      response = chat.create(prompt=str(prompt))

      # Correct handling based on Mirascope's expected response structure
      response_text = response.message  # Adjust this line based on actual response structure
      logging.info(
          f'Received response for agent ID {agent["id"]}: {response_text}')

      agent_data["responses"].append({
          "question":
          question['text'],
          "answer":
          response_text,
          "timestamp":
          datetime.datetime.now().isoformat(),
          "unique_id":
          str(uuid.uuid4())
      })

    data[agent['id']] = agent_data
  logging.info('Finished asking agents questions. Returning data.')
  return data


def update_instructions_json(instructions, filepath):
  # Extract the directory from the filepath and ensure it exists
  directory = os.path.dirname(filepath)
  os.makedirs(directory, exist_ok=True)

  # Create the instructions structure
  instructions_json = {"instructions": instructions}

  # Write the structured data to the specified filepath
  with open(filepath, 'w') as f:
    json.dump(instructions_json, f, indent=4)


def update_questions_json(questions, filepath):
  # Extract the directory from the filepath and ensure it exists
  directory = os.path.dirname(filepath)
  os.makedirs(directory, exist_ok=True)

  # Create the questions structure with a key for custom questions
  updated_questions = []
  custom_question_counter = 1  # Start counter for custom questions

  for q in questions:
    # Check if a question text is actually a dict with "text" and optionally "key"
    if isinstance(q, dict) and "text" in q:
      # If it's already a properly formatted question, add it as is
      updated_questions.append(q)
    else:
      # For simple string questions, format them with a custom key
      question_format = {
          "key": f"Custom Question {custom_question_counter}",
          "text": q
      }
      updated_questions.append(question_format)
      custom_question_counter += 1  # Increment counter for next custom question

  # Wrap updated questions in the required "questions" structure
  questions_json = {"questions": updated_questions}

  # Write the structured data to the specified filepath
  with open(filepath, 'w') as f:
    json.dump(questions_json, f, indent=4)


def should_use_modified_agents():
  global use_modified_agents_json
  global modified_agents_json_path  # Use the global path variable
  # Check if the modified_agents_json flag is true and the file exists
  return use_modified_agents_json and os.path.exists(modified_agents_json_path)


def process_agents(session_id, selected_agent_ids, modified_questions,
                   custom_instructions):
  global is_processing, final_html_path
  global CURRENT_AGENTS_JSON_PATH
  logging.info("Starting the process to ask agents and generate output...")

  # Define file paths for questions and instructions
  questions_file_path = os.path.join('static', 'output', session_id, 'abe',
                                     'abe-questions.json')
  instructions_file_path = os.path.join('static', 'output', session_id, 'abe',
                                        'abe-instructions.json')

  # Update the questions and instructions JSON files
  logging.info("Updating questions and instructions JSON files...")
  update_questions_json(modified_questions, questions_file_path)
  update_instructions_json(custom_instructions, instructions_file_path)

  # Load the updated questions and instructions to ensure we're using the latest
  updated_questions = load_json_data(questions_file_path)
  updated_instructions = load_json_data(instructions_file_path)['instructions']

  # Load all agents and filter based on selected_agent_ids
  agents_file_path = AGENTS_JSON_PATH
  with open(CURRENT_AGENTS_JSON_PATH, 'r') as file:
    all_agents = json.load(file)

  agents = [
      agent for agent in all_agents
      if str(agent.get("id")) in selected_agent_ids
  ]

  # Prepare unique output folder
  timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
  unique_output_folder = os.path.join('static', 'output',
                                      f'unique_{timestamp}')
  html_folder = os.path.join(unique_output_folder, 'html')
  html_pics_folder = os.path.join(html_folder, 'pics')
  os.makedirs(html_pics_folder, exist_ok=True)

  # Ask questions to all selected agents once
  logging.info("Asking agents questions...")
  agent_responses = ask_agents_questions(agents, updated_questions)
  logging.info("Finished asking agents questions.")

  # Process and save responses
  responses = {}
  for agent in agents:
    updated_agent = copy_agent_photo_to_static(agent, unique_output_folder)
    if updated_agent:  # Check if updated_agent is not None
      agent_id_str = str(agent['id'])
      if agent_id_str in agent_responses and agent_responses[
          agent_id_str] is not None:
        updated_agent['responses'] = agent_responses[agent_id_str].get(
            'responses', [])
      else:
        logging.warning(
            f"No responses or agent_responses entry is None for agent ID {agent_id_str}."
        )
        updated_agent['responses'] = []
      responses[agent['id']] = updated_agent

  csv_file_path = os.path.join(unique_output_folder, 'agent_responses.csv')
  json_file_path = os.path.join(unique_output_folder, 'responses.json')

  # Save responses to JSON
  logging.info(f"Saving responses to JSON at {json_file_path}")

  save_responses_to_json(list(responses.values()), json_file_path)

  # Save responses to CSV
  logging.info(f"Saving responses to CSV at {csv_file_path}")

  save_to_csv(list(responses.values()), csv_file_path)

  # Generate and save the final HTML
  logging.info("Generating final HTML...")

  final_html_path = generate_single_html(app,
                                         unique_output_folder,
                                         'responses.json',
                                         csv_file_path=csv_file_path)
  if final_html_path:
    web_accessible_path = '/' + os.path.relpath(final_html_path,
                                                'static').replace('\\', '/')
    final_html_path = web_accessible_path
    logging.info(
        f"Processing completed and HTML is ready. HTML path: {web_accessible_path}"
    )
  else:
    logging.error("Failed to generate the HTML file. No path returned.")

  is_processing = False
  return final_html_path

def run_agent_process(session_id, selected_agent_ids, questions,
                      custom_instructions, modify_agents_json_flag,
                      modify_agents_json_instructions,
                      custom_modify_instructions):
    with current_app.app_context():
        global is_processing, final_html_path
        try:
            app_context = current_app.app_context()
            app_context.push()

            # Determine the correct JSON file to use based on user choice
            agents_json_path = create_session_specific_agents_json(session_id)
            if modify_agents_json_flag:
                # Modify the agents.json if required by the user
                modify_agents_json(agents_json_path, modify_agents_json_instructions,
                                   custom_instructions, selected_agent_ids,
                                   custom_modify_instructions)

            # Load agents for the session
            agents_file_to_use = modified_agents_json_path if should_use_modified_agents() else agents_json_path

            # Load session data using the appropriate agents JSON file
            session_id = session.get('session_id')
            if not session_id:
                logging.error("Session ID is not set. Cannot load session data.")
                return  # or handle error appropriately

            # Ask questions and process agents
            agent_responses = ask_agents_questions(selected_agent_ids, questions)
            final_html_path = process_agents(session_id, selected_agent_ids, questions,
                                              custom_instructions)

            logging.info(f"Final HTML path set to: {final_html_path}")
            app_context.pop()
        except Exception as e:
            logging.error(f"Error in run_agent_process: {e}")
        finally:
            is_processing = False


def ensure_abe_files_for_session(session_id):
  # Path to the session-specific ABE directory
  session_abe_dir = os.path.join('static', 'output', session_id, 'html', 'abe')

  # Ensure the directory exists
  os.makedirs(session_abe_dir, exist_ok=True)

  # Paths for the source ABE files
  source_questions_path = 'abe/abe-questions.json'
  source_instructions_path = 'abe/abe-instructions.json'

  # Paths for the session-specific ABE files
  session_questions_path = os.path.join(session_abe_dir, 'abe-questions.json')
  session_instructions_path = os.path.join(session_abe_dir,
                                           'abe-instructions.json')

  # Copy the ABE files to the session-specific directory
  shutil.copy(source_questions_path, session_questions_path)
  shutil.copy(source_instructions_path, session_instructions_path)


def save_to_json(data, file_path):
  """
  Saves responses to a JSON file.
  """
  if not data:
    logging.info("No data to save.")
    return

  os.makedirs(os.path.dirname(file_path), exist_ok=True)
  with open(file_path, 'w', encoding='utf-8') as jsonfile:
    json.dump(data, jsonfile, indent=4)
    logging.info(f"Data saved to JSON file: {file_path}")


def save_to_csv(data, csv_file_path):
  """
  Saves agents' responses to a CSV file.
  """
  if not data:
    logging.info("No data to save to CSV.")
    return

  os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
  with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = [
        'id', 'email', 'question', 'answer', 'timestamp', 'unique_id'
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for agent_data in data:
      for response in agent_data.get('responses', []):
        writer.writerow({
            'id': agent_data['id'],
            'email': agent_data['email'],
            'question': response['question'],  # Use dictionary key notation
            'answer': response['answer'],  # Use dictionary key notation
            'timestamp': response['timestamp'],  # Use dictionary key notation
            'unique_id': response['unique_id']  # Use dictionary key notation
        })


def truncate_data(data):
  for agent in data:
    for key, value in agent.items():
      if isinstance(value, str) and len(value) > 140:
        agent[key] = value[:140]
  return data


def copy_and_truncate_json_files(source_folder, destination_folder):
  files_to_copy = [
      'abe/abe-instructions.json', 'abe/abe-questions.json',
      'agents/agents.json'
  ]
  for file_name in files_to_copy:
    source_path = os.path.join(source_folder, file_name)
    destination_path = os.path.join(destination_folder,
                                    file_name.replace('/', os.sep))
    os.makedirs(os.path.dirname(destination_path),
                exist_ok=True)  # Ensure the directory exists

    try:
      with open(source_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

      # Attempt to sanitize data if 'agents.json'
      if 'agents.json' in file_name:
        data = sanitize_json_data(data)

      with open(destination_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    except json.decoder.JSONDecodeError as e:
      logging.error(f"JSONDecodeError encountered in file {file_name}: {e}")


def copy_agent_photo_to_static(agent, unique_output_folder):
  agent_id = agent.get('id')
  original_photo_path = agent.get('photo_path', None)
  if original_photo_path:
    source_photo_path = os.path.join(os.getcwd(), original_photo_path)

    if os.path.exists(source_photo_path):
      html_pics_folder = os.path.join(unique_output_folder, 'html', 'pics')
      os.makedirs(html_pics_folder, exist_ok=True)  # Ensure directory exists

      new_file_name = os.path.basename(original_photo_path)
      new_photo_path = os.path.join(html_pics_folder, new_file_name)

      try:
        shutil.copy(source_photo_path, new_photo_path)
        base_dir_name = os.path.basename(unique_output_folder)
        web_accessible_path = f'/static/output/{base_dir_name}/html/pics/{new_file_name}'
        agent['photo_path'] = web_accessible_path  # Update agent's photo path
        logging.info(
            f"Photo for agent {agent_id} successfully copied to {web_accessible_path}"
        )
      except Exception as e:
        logging.error(f"Failed to copy photo for agent {agent_id}: {e}")
    else:
      logging.error(
          f"Photo path does not exist for agent {agent_id}: {source_photo_path}"
      )
  else:
    logging.error(f"No photo path provided for agent {agent_id}")

  return agent  # Ensure the updated agent is returned


def sanitize_json_data(data):
  """
  Attempts to sanitize JSON data by escaping or removing invalid control characters.
  """
  sanitized_data = json.dumps(data)
  sanitized_data = sanitized_data.replace('\n', '\\n').replace('\r',
                                                               '\\r').replace(
                                                                   '\t', '\\t')
  return json.loads(sanitized_data)


def save_responses_to_json(data, file_path):
  """
  Saves the updated agents' data, including the 'include' flag, to a JSON file.
  """
  os.makedirs(os.path.dirname(file_path), exist_ok=True)
  with open(file_path, 'w', encoding='utf-8') as jsonfile:
    # Convert the data values to a list if it's not already one
    data_list = list(data.values()) if not isinstance(data, list) else data
    json.dump(data_list, jsonfile, indent=4)
    logging.info(f"Updated agent data saved to {file_path}")


def generate_single_html(app, output_folder, json_file_name, csv_file_path):
  with app.app_context():
    json_file_path = os.path.join(output_folder, json_file_name)
    web_accessible_json_path = '/static/' + os.path.relpath(
        json_file_path, 'static').replace('\\', '/')
    csv_download_path = '/static/' + os.path.relpath(
        csv_file_path, 'static').replace('\\', '/')

    html_content = render_template(
        'agent_response_template.html',
        web_accessible_json_path=web_accessible_json_path,
        csv_download_path=csv_download_path)

    html_file_path = os.path.join(output_folder, "agents_responses.html")
    with open(html_file_path, 'w', encoding='utf-8') as f:
      f.write(html_content)

    return '/static/' + os.path.relpath(html_file_path, 'static').replace(
        '\\', '/')


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  app.run(host='0.0.0.0', port=81)
