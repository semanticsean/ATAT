#abe.py
import time
import threading
import os
import main
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
import subprocess


from typing import ClassVar
from flask import request
from mirascope import Prompt, OpenAIChat
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, after_this_request
from flask import current_app as app
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message


app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_very_secret_key'


app.config['MAIL_SERVER'] = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('SMTP_PORT', 587))
app.config['MAIL_USE_TLS'] = True  
app.config['MAIL_USERNAME'] = os.environ.get('SMTP_USERNAME', 'devagent@semantic-life.com')
app.config['MAIL_PASSWORD'] = os.environ.get('SMTP_PASSWORD', '')
mail = Mail(app)

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
AGENTS_JSON_PATH = os.path.join('agents', 'agents.json')
IMAGES_BASE_PATH = os.path.join('agents', 'pics')



# Define and apply a custom logging filter to exclude /status endpoint logs
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



# Global variables to manage process state and results
responses_data = {}
is_processing = False
final_html_path = ""


def initialize_session(unique_folder):
  # Directories for JSON files and agent photos
  html_folder = os.path.join(unique_folder, 'html')
  pics_folder = os.path.join(html_folder, 'pics')
  os.makedirs(pics_folder, exist_ok=True)  # Ensure the pics directory exists

  # Copy JSON files as before
  copy_and_truncate_json_files('.', html_folder)

  # Load agents JSON to get photo paths
  agents_file_path = os.path.join('agents', 'agents.json')
  with open(agents_file_path, 'r') as file:
    agents = json.load(file)

  for agent in agents:
    # Ensure each agent has "include": true by default
    agent.setdefault("include", True)
    original_photo_path = agent.get('photo_path')

  # Copy each agent's photo to the pics directory and update their photo_path
  for agent in agents:
    original_photo_path = agent.get('photo_path')
    if original_photo_path:
      photo_filename = os.path.basename(original_photo_path)
      new_photo_path = os.path.join(pics_folder, photo_filename)
      shutil.copy(original_photo_path, new_photo_path)
      # Update agent's photo_path to reflect new location
      agent['photo_path'] = os.path.join('/static/output',
                                         os.path.basename(unique_folder),
                                         'html', 'pics', photo_filename)

  # Save the updated agents JSON to the new location
  updated_agents_file_path = os.path.join(html_folder, 'agents.json')
  with open(updated_agents_file_path, 'w') as file:
    json.dump(agents, file, indent=4)




def load_session_data(unique_folder):
  # Assuming JSON filenames are known and fixed
  agents_file_path = os.path.join(unique_folder, 'agents', 'agents.json')
  questions_file_path = os.path.join(unique_folder, 'abe',
                                     'abe-questions.json')
  instructions_file_path = os.path.join(unique_folder, 'abe',
                                        'abe-instructions.json')

  # Load data from each file
  agents = load_json_data(agents_file_path)
  questions = load_json_data(questions_file_path)
  instructions = load_json_data(instructions_file_path)['instructions']

  return agents, questions, instructions


def load_json_data(filepath):
  with open(filepath, 'r') as file:
    return json.load(file)


#FLASK

def send_auth_email(email_address):
  serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
  token = serializer.dumps(email_address, salt='email-confirm-salt')
  confirm_url = url_for('confirm_email', token=token, _external=True)
  html = render_template('auth_email.html', confirm_url=confirm_url)
  msg = Message('Email Authentication', recipients=[email_address], html=html)
  mail.send(msg)

@app.route('/')
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
  return render_template('index.html', agents=agents)

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
        email_address = serializer.loads(token, salt='email-confirm-salt', max_age=3600)
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
  # The photo path is assumed to be in the format "pics/filename.png"
  return agent.get('photo_path', 'default.png')


@app.route('/agents/pics/<filename>')
def agent_pics(filename):
  return send_from_directory(IMAGES_BASE_PATH, filename)


@app.route('/abe')
def home():
  return render_template('abe-landing.html')


@app.route('/start_session', methods=['POST'])
def start_session():
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    unique_folder = os.path.join('static', 'output', session_id)

    # Create the session-specific directories
    html_folder = os.path.join(unique_folder, 'html')
    os.makedirs(html_folder, exist_ok=True)

    # Copy the original agents.json to a session-specific location
    src = AGENTS_JSON_PATH
    dst = os.path.join(html_folder, 'agents.json')
    shutil.copy(src, dst)

    # Initialize the session with the potentially modified agents.json
    initialize_session(unique_folder)

    # Redirect to the ABE dashboard or another relevant page
    return redirect(url_for('abedashboard'))


@app.route('/abedashboard')
def abedashboard():
  session_id = session.get('session_id')
  if not session_id:
    return redirect(url_for('home'))
  unique_folder_path = f'/static/output/{session_id}/html/pics'
  agents, questions, instructions = load_session_data(
      os.path.join('static', 'output', session_id, 'html'))
  return render_template('abe.html',
                         agents=agents,
                         questions=questions,
                         instructions=instructions,
                         unique_folder_path=unique_folder_path)


@app.route('/start', methods=['POST'])
def start_process():
  global is_processing
  if is_processing:
    return jsonify({"error": "Process is already running"}), 400

  data = request.get_json()
  selected_agent_ids = data.get('selectedAgents', [])
  questions = data.get('questions',
                       [])  # This will now include custom questions
  custom_instructions = data.get('instructions', '')

  if not selected_agent_ids:
    return jsonify({"error": "No agents selected."}), 400

  session_id = session.get('session_id')
  if session_id is None:
    return jsonify(
        {"error": "Session ID not found. Please restart the session."}), 400

  if not is_processing:  # Double-check to prevent race conditions
    thread = threading.Thread(target=lambda: run_agent_process(
        session_id, selected_agent_ids, questions, custom_instructions))
    thread.start()
    is_processing = True
    return jsonify({"message": "Processing started"}), 202
  else:
    return jsonify({
        "error":
        "Processing was attempted to start again before completion."
    }), 400


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
      agents_file_path = os.path.join(
          'static', 'output', session_id, 'html',
          'agents.json') if session_id else os.path.join(
              'agents', 'agents.json')
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


# PROCESS AGENTS
def copy_agent_photos_to_session(agents_data, destination_folder):
  """
  Copies all agent photos to the specified destination folder.

  Args:
      agents_data: A list of dictionaries, each representing an agent.
      destination_folder: The destination folder where photos will be copied.
  """
  for agent in agents_data:
    photo_path = agent.get("photo_path")
    if photo_path:
      # Assuming photo_path is a relative path from the project root
      source_photo_path = os.path.join(os.getcwd(), photo_path)
      if os.path.exists(source_photo_path):
        try:
          # Ensure the destination folder exists
          os.makedirs(destination_folder, exist_ok=True)
          # Copy the photo
          shutil.copy(source_photo_path, destination_folder)
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


def ask_agents_questions(agents, questions):
  logging.info('Starting to ask agents questions...')
  data = {}
  base_sleep_time = 5  # Base sleep time in seconds
  for agent in agents:
    model = agent.get(
        "model", "gpt-3.5-turbo")  # Use model specified in agent's profile
    chat = OpenAIChat(api_key=OPENAI_API_KEY, model=model)
    agent_data = {"id": agent['id'], "email": agent['email'], "responses": []}
    for question in questions['questions']:
      sleep_time = base_sleep_time  # Reset sleep time for each question
      attempts = 0  # Reset attempts for each question
      while attempts < 5:  # Set a maximum number of attempts
        try:
          prompt = CustomAgentPrompt(agent_json=json.dumps(agent),
                                     question=question['text'])
          completion = chat.create(prompt=prompt.__str__())
          # Properly access the completion content. Adjust based on actual completion structure
          response_text = str(
              completion
          )  # Convert completion to string to get the response content
          logging.info(
              f"Full API response for agent {agent['id']}: {response_text}"
          )  # Log the full response text
          agent_data["responses"].append({
              "question":
              question['text'],
              "answer":
              response_text.strip(),
              "timestamp":
              datetime.datetime.now().isoformat(),
              "unique_id":
              str(uuid.uuid4())
          })
          time.sleep(sleep_time)  # Sleep after successful completion
          break  # Exit the loop after successful call
        except Exception as e:
          logging.exception(
              f"Error asking questions to agent {agent['id']} - {agent['email']} on attempt {attempts + 1}: {e}"
          )
          attempts += 1
          time.sleep(sleep_time)  # Sleep before retrying
          sleep_time *= 2  # Exponential backoff
    data[agent['id']] = agent_data
  logging.info('Finished asking agents questions.')
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


def process_agents(session_id, selected_agent_ids, modified_questions, custom_instructions):
  global is_processing, final_html_path

  logging.info("Starting the process to ask agents and generate output...")

  # Define file paths for questions and instructions
  questions_file_path = os.path.join('static', 'output', session_id, 'abe', 'abe-questions.json')
  instructions_file_path = os.path.join('static', 'output', session_id, 'abe', 'abe-instructions.json')

  # Update the questions and instructions JSON files
  logging.info("Updating questions and instructions JSON files...")
  update_questions_json(modified_questions, questions_file_path)
  update_instructions_json(custom_instructions, instructions_file_path)

  # Load the updated questions and instructions to ensure we're using the latest
  updated_questions = load_json_data(questions_file_path)
  updated_instructions = load_json_data(instructions_file_path)['instructions']

  # Load all agents and filter based on selected_agent_ids
  agents_file_path = os.path.join('agents', 'agents.json')
  with open(agents_file_path, 'r') as file:
      all_agents = json.load(file)
  agents = [agent for agent in all_agents if str(agent.get("id")) in selected_agent_ids]

  # Prepare unique output folder
  timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
  unique_output_folder = os.path.join('static', 'output', f'unique_{timestamp}')
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
      if agent['id'] in agent_responses:
          updated_agent['responses'] = agent_responses[agent['id']]['responses']
      responses[agent['id']] = updated_agent

  # Save responses to JSON

  csv_file_path = os.path.join(unique_output_folder, 'agent_responses.csv')
  json_file_path = os.path.join(unique_output_folder, 'responses.json')

  # Save responses to JSON
  save_responses_to_json(list(responses.values()), json_file_path)

  # Save responses to CSV
  save_to_csv(list(responses.values()), csv_file_path)

  # Generate and save the final HTML
  final_html_path = generate_single_html(app, unique_output_folder, 'responses.json', csv_file_path=csv_file_path)
  if final_html_path:
      web_accessible_path = '/' + os.path.relpath(final_html_path, 'static').replace('\\', '/')
      final_html_path = web_accessible_path
      logging.info(f"Processing completed and HTML is ready. HTML path: {web_accessible_path}")
  else:
      logging.error("Failed to generate the HTML file. No path returned.")

  is_processing = False
  return final_html_path



def run_agent_process(session_id, selected_agent_ids, modified_questions,
                      custom_instructions):

  global is_processing, final_html_path
  try:
    final_html_path = process_agents(session_id, selected_agent_ids,
                                     modified_questions, custom_instructions)
    logging.info(f"Final HTML path set to: {final_html_path}")
  finally:
    is_processing = False


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
      fieldnames = ['id', 'email', 'question', 'answer', 'timestamp', 'unique_id']
      writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
      writer.writeheader()
      for agent_data in data:
          for response in agent_data.get('responses', []):
              writer.writerow({
                  'id': agent_data['id'],
                  'email': agent_data['email'],
                  'question': response['question'],
                  'answer': response['answer'],
                  'timestamp': response['timestamp'],
                  'unique_id': response['unique_id']
              })


def truncate_data(data):
  for agent in data:
      for key, value in agent.items():
          if isinstance(value, str) and len(value) > 140:
              agent[key] = value[:140]
  return data

def copy_and_truncate_json_files(source_folder, destination_folder):
  files_to_copy = ['abe/abe-instructions.json', 'abe/abe-questions.json', 'agents/agents.json']
  for file_name in files_to_copy:
      source_path = os.path.join(source_folder, file_name)
      destination_path = os.path.join(destination_folder, file_name.replace('/', os.sep))
      os.makedirs(os.path.dirname(destination_path), exist_ok=True)  # Ensure the directory exists

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
  """
    Copies a single agent's photo to the static folder within a unique output directory and updates the agent's photo path.
    """
  agent_id = agent.get('id')
  original_photo_path = agent.get('photo_path', None)
  if original_photo_path:
    # Extract the base directory name for the HTML and pictures folder
    html_pics_folder = os.path.join(unique_output_folder, 'html', 'pics')
    new_file_name = os.path.basename(original_photo_path)
    new_photo_path = os.path.join(html_pics_folder, new_file_name)

    # Create the html_pics_folder if it doesn't exist
    os.makedirs(html_pics_folder, exist_ok=True)

    try:
      shutil.copy(original_photo_path, new_photo_path)
      # Update the agent's photo path to be web accessible, correcting the structure
      base_dir_name = os.path.basename(unique_output_folder)
      web_accessible_path = f'/static/output/{base_dir_name}/html/pics/{new_file_name}'
      agent['photo_path'] = web_accessible_path
      logging.info(
          f"Photo for agent {agent_id} successfully copied to {web_accessible_path}"
      )
    except Exception as e:
      logging.error(f"Failed to copy photo for agent {agent_id}: {e}")
      raise FileNotFoundError(
          f"Failed to copy photo for agent {agent_id}: {e}")
  else:
    logging.error(f"No photo path provided for agent {agent_id}")
    # Assuming a default photo is not desired; otherwise, set a default photo path here
    raise FileNotFoundError(f"No photo path provided for agent {agent_id}")
  return agent

def sanitize_json_data(data):
  """
  Attempts to sanitize JSON data by escaping or removing invalid control characters.
  """
  sanitized_data = json.dumps(data)
  sanitized_data = sanitized_data.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
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
      web_accessible_json_path = '/static/' + os.path.relpath(json_file_path, 'static').replace('\\', '/')
      csv_download_path = '/static/' + os.path.relpath(csv_file_path, 'static').replace('\\', '/')

      html_content = render_template('agent_response_template.html',
                                     web_accessible_json_path=web_accessible_json_path,
                                     csv_download_path=csv_download_path)

      html_file_path = os.path.join(output_folder, "agents_responses.html")
      with open(html_file_path, 'w', encoding='utf-8') as f:
          f.write(html_content)

      return '/static/' + os.path.relpath(html_file_path, 'static').replace('\\', '/')


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  app.run(host='0.0.0.0', port=81)
