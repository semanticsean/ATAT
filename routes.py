# routes.py
import os, json, random, re, glob, shutil, bleach, logging, uuid
import abe_gpt
import start
import base64

from models import User, Survey, db
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file, make_response, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from logging.handlers import RotatingFileHandler

from abe_gpt import generate_new_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        RotatingFileHandler('logs/app.log', maxBytes=10000,
                            backupCount=3)  # File output
    ])

logger = logging.getLogger(__name__)

AGENTS_JSON_PATH = os.path.join('agents', 'agents.json')
IMAGES_BASE_PATH = os.path.join('agents', 'pics')
AGENTS_BASE_PATH = 'agents'
SURVEYS_BASE_PATH = 'surveys'

start_blueprint = Blueprint('start_blueprint',
                            __name__,
                            template_folder='templates')

UPLOAD_FOLDER = 'agents/new_agent_files'
ALLOWED_EXTENSIONS = {'txt', 'doc', 'rtf', 'md', 'pdf'}

auth_blueprint = Blueprint('auth_blueprint',
                           __name__,
                           template_folder='templates')
survey_blueprint = Blueprint('survey_blueprint',
                             __name__,
                             template_folder='templates')

dashboard_blueprint = Blueprint('dashboard_blueprint',
                                __name__,
                                template_folder='templates')

profile_blueprint = Blueprint('profile_blueprint',
                              __name__,
                              template_folder='templates')


class PageView(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  page = db.Column(db.String(50), nullable=False)
  timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    identifier = request.form['username_or_email']
    password = request.form['password']

    # Determine if the identifier is an email or username
    user = User.query.filter((User.username == identifier)
                             | (User.email == identifier)).first()

    if user is None or not user.check_password(password):
      flash('Invalid username/email or password')
      return redirect(url_for('auth_blueprint.login'))

    login_user(user)
    return redirect(url_for('home'))

  page_view = PageView(page='/login')
  db.session.add(page_view)
  db.session.commit()

  return render_template('login.html')


@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    email = request.form.get('email')  # Retrieve email from form data
    user = User.query.filter_by(username=username).first()
    if user:
      flash('Username already exists')
      return redirect(url_for('auth_blueprint.register'))
    # Check if email already exists
    email_exists = User.query.filter_by(email=email).first()
    if email_exists:
      flash('Email already registered')
      return redirect(url_for('auth_blueprint.register'))
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    new_user.create_user_folder()
    db.session.add(new_user)
    db.session.commit()
    page_view = PageView(page='/register')
    db.session.add(page_view)
    db.session.commit()
    return redirect(url_for('auth_blueprint.login'))

  return render_template('register.html')


@auth_blueprint.route('/user', methods=['GET', 'POST'])
@login_required
def update_profile():
  if request.method == 'POST':
    current_user.username = request.form['username']
    current_user.email = request.form.get('email')
    password = request.form.get('password')
    if password:
      current_user.password_hash = generate_password_hash(password)

    db.session.commit()
    flash('Your profile was updated successfully!')

    page_view = PageView(page='/user')
    db.session.add(page_view)
    db.session.commit()

    return redirect(url_for('auth_blueprint.update_profile'))

  return render_template('user.html')


@auth_blueprint.route('/help')
def help():
  return render_template('help.html')


def sanitize_filename(filename):
  # Strip HTML tags
  clean_filename = bleach.clean(filename, tags=[], strip=True)
  # Remove spaces and special characters
  clean_filename = re.sub(r'\s+|[^a-zA-Z0-9]', '_', clean_filename)
  # Remove leading or trailing underscores
  clean_filename = clean_filename.strip('_')
  return clean_filename


@auth_blueprint.route('/images/<filename>')
@login_required
def serve_image(filename):
  image_data = current_user.images_data.get(filename)
  if image_data:
    return Response(base64.b64decode(image_data), mimetype='image/png')
  else:
    return abort(404)


@auth_blueprint.route('/new_agent_copy')
@login_required
def new_agent_copy():
  agents_data = current_user.agents_data or []

  if not agents_data:
    base_agents_files = ['agents.json'
                         ]  # Add more files in the future if needed
    return render_template('add_base_agents.html',
                           base_agents_files=base_agents_files)

  return render_template('new_timeframe.html', agents=agents_data)


@auth_blueprint.route('/add_base_agents', methods=['POST'])
@login_required
def add_base_agents():
  base_agents_file = request.form.get('base_agents_file', 'agents.json')
  base_agents_path = os.path.join('agents', base_agents_file)

  try:
    with open(base_agents_path, 'r') as file:
      base_agents_data = json.load(file)

    for agent in base_agents_data:
      photo_path = agent['photo_path']
      photo_filename = os.path.basename(photo_path)
      image_path = os.path.join('agents', 'pics', photo_filename)

      with open(image_path, 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        agent['photo_path'] = f"data:image/jpeg;base64,{encoded_string}"

    current_user.agents_data = base_agents_data
    db.session.commit()

    return jsonify({'success': True})
  except Exception as e:
    return jsonify({'success': False, 'error': str(e)})


@auth_blueprint.route('/new_timeframe', methods=['POST'])
@login_required
def create_agent_copy():
  agents_data = current_user.agents_data
  selected_agent_ids = request.form.getlist('selected_agents')
  selected_agents_data = [
      agent for agent in agents_data if str(agent['id']) in selected_agent_ids
  ]

  form_data = request.form.to_dict()
  form_data.pop('selected_agents', None)

  payload = {
      "agents_data": selected_agents_data,
      "instructions": form_data,
  }

  updated_agents_data = abe_gpt.process_agents(payload, current_user)

  for agent_data in updated_agents_data:
    agent_data['is_copy'] = True

  current_user.agents_data.extend(updated_agents_data)
  db.session.commit()

  return redirect(url_for('dashboard_blueprint.dashboard'))


@survey_blueprint.route('/survey/create', methods=['GET', 'POST'])
@login_required
def create_survey():
  agents_data = current_user.agents_data or []

  if not agents_data:
    base_agents_files = ['agents.json'
                         ]  # Add more files in the future if needed
    return render_template('add_base_agents.html',
                           base_agents_files=base_agents_files)

  if request.method == 'POST':
    selected_file = request.form.get('selected_file', default_agents_json_path)
    survey_name = request.form.get('survey_name')
    logger.info(
        f"User {user_id} is creating survey '{survey_name}' with file '{selected_file}'."
    )

    # Adjusted to handle the case when selected_file is 'agents.json' or the default path
    if selected_file == 'agents.json' or selected_file == default_agents_json_path:
      file_path = default_agents_json_path
    else:
      file_path = os.path.join(copies_dir, os.path.basename(selected_file))

    try:
      with open(file_path, 'r') as f:
        agents = json.load(f)
      logger.info(
          f"Loaded agents from '{file_path}'. Total agents loaded: {len(agents)}"
      )
    except Exception as e:
      logger.error(
          f"Failed to load agents for user {user_id} from '{file_path}': {e}")
      flash(
          'There was an error loading the selected agent file. Please try again.'
      )
      return redirect(url_for('survey_blueprint.create_survey'))

    selected_agents = request.form.getlist('selected_agents')
    logger.info(
        f"Selected agents: {selected_agents}")  # Log the selected agents

    survey_agents = [
        agent for agent in agents if str(agent['id']) in selected_agents
    ]
    logger.info(f"Survey agents: {survey_agents}")  # Log the survey agents

    logger.info(
        f"Selected {len(survey_agents)} agents for survey '{survey_name}'.")

    # Create survey folder and selected_agents.json
    survey_folder = os.path.join(
        user_dir, 'surveys', f"{survey_name}_{random.randint(100000, 999999)}")
    os.makedirs(survey_folder, exist_ok=True)
    selected_agents_file = os.path.join(survey_folder, 'selected_agents.json')
    with open(selected_agents_file, 'w') as f:
      json.dump(survey_agents, f)
    logger.info(
        f"Created survey folder '{survey_folder}' and saved selected agents.")

    # Copy photos to a new subfolder within the survey folder
    photos_subfolder = os.path.join(survey_folder, 'pics')
    os.makedirs(photos_subfolder, exist_ok=True)
    logger.info(f"Created photos subfolder at '{photos_subfolder}'.")

    for agent in survey_agents:
      try:
        old_photo_path = agent['photo_path']
        photo_filename = os.path.basename(old_photo_path)
        new_photo_path = os.path.join('surveys',
                                      os.path.basename(survey_folder), 'pics',
                                      photo_filename)
        shutil.copy(os.path.join(user_dir, old_photo_path),
                    os.path.join(photos_subfolder, photo_filename))
        survey_id = os.path.basename(survey_folder)
        agent['photo_path'] = url_for('survey_blueprint.serve_survey_image',
                                      survey_id=survey_id,
                                      filename=photo_filename)

        logger.info(
            f"Copied photo '{photo_filename}' for agent '{agent['id']}' to '{new_photo_path}'."
        )
      except Exception as e:
        logger.error(f"Failed to copy photo for agent '{agent['id']}': {e}")

    # Save the updated paths back to selected_agents.json
    with open(selected_agents_file, 'w') as f:
      json.dump(survey_agents, f)
    logger.info("Updated agent photo paths in 'selected_agents.json'.")

    new_survey = Survey(name=survey_name,
                        user_id=current_user.id,
                        agents_file=selected_agents_file)
    db.session.add(new_survey)
    db.session.commit()
    logger.info(
        f"Successfully created survey '{survey_name}' with ID {new_survey.id} for user {user_id}."
    )

    return redirect(
        url_for('survey_blueprint.survey_form',
                survey_id=new_survey.id,
                survey_agents=survey_agents))
  else:
    return render_template('meeting1.html', agents=agents_data)


@survey_blueprint.route('/surveys/<path:survey_id>/pics/<filename>')
@login_required
def serve_survey_image(survey_id, filename):
  user_dir = current_user.folder_path
  file_path = os.path.join(user_dir, 'surveys', survey_id, 'pics', filename)
  if os.path.exists(file_path):
    return send_file(file_path)
  else:
    abort(404)


@survey_blueprint.route('/survey/<int:survey_id>', methods=['GET', 'POST'])
@login_required
def survey_form(survey_id):
  survey = Survey.query.get_or_404(survey_id)
  if survey.user_id != current_user.id:
    abort(403)

  if request.method == 'POST':
    questions = extract_questions_from_form(request.form)
    selected_agent_ids = request.form.getlist('selected_agents')
    llm_instructions = request.form.get('llm_instructions', '')
    request_type = request.form.get('request_type', 'iterative')

    selected_agents_data = [
        agent for agent in survey.survey_data
        if str(agent['id']) in selected_agent_ids
    ]

    payload = {
        "agents_data": selected_agents_data,
        "questions": questions,
        "llm_instructions": llm_instructions,
        "request_type": request_type,
    }

    survey_responses = abe_gpt.conduct_survey(payload, current_user)

    for agent_data, response in zip(selected_agents_data, survey_responses):
      agent_data['responses'] = response['responses']
      agent_data['questions'] = questions

    survey.survey_data = selected_agents_data
    db.session.commit()

    return redirect(url_for('survey_blueprint.results', survey_id=survey.id))
  else:
    agents_data = survey.survey_data
    return render_template('meeting2.html', survey=survey, agents=agents_data)


@survey_blueprint.route('/survey/<int:survey_id>/get_results')
@login_required
def get_results(survey_id):
  survey = Survey.query.get_or_404(survey_id)
  if survey.user_id != current_user.id:
    abort(403)

  results_files = glob.glob(
      os.path.join(os.path.dirname(survey.agents_file),
                   'selected_agents_results*.json'))
  results = []
  for file in results_files:
    with open(file, 'r') as f:
      results.extend(
          json.load(f))  # Extend the results array with data from each file

  return jsonify(results)


@survey_blueprint.route('/survey/<int:survey_id>/results')
@login_required
def results(survey_id):
  survey = Survey.query.get_or_404(survey_id)
  if survey.user_id != current_user.id:
    abort(403)

  survey_data = survey.survey_data

  if request.method == 'POST':
    is_public = request.form.get('is_public') == 'on'
    survey.is_public = is_public

    if is_public and not survey.public_url:
      survey.public_url = str(uuid.uuid4())
    elif not is_public:
      survey.public_url = None

    db.session.commit()

  return render_template('results.html', survey=survey, results=survey_data)


@dashboard_blueprint.route('/dashboard')
@login_required
def dashboard():
  agents_data = current_user.agents_data or []

  if not agents_data:
    base_agents_files = ['agents.json'
                         ]  # Add more files in the future if needed
    return render_template('add_base_agents.html',
                           base_agents_files=base_agents_files)

  agent_copies = [
      agent for agent in agents_data if 'is_copy' in agent and agent['is_copy']
  ]
  survey_results = []

  for survey in current_user.surveys:
    if survey.survey_data:
      for agent_data in survey.survey_data:
        survey_results.append((survey.name, agent_data['id']))

  # Update the photo_path to use the base64-encoded image
  for agent in agents_data:
    agent['photo_path'] = agent['photo_path'].replace('agents/pics/', '')

  return render_template('dashboard.html',
                         agents=agents_data,
                         agent_copies=agent_copies,
                         survey_results=survey_results)


@survey_blueprint.route('/survey/results/<int:survey_id>')
@login_required
def show_survey_results(survey_id):
  survey = Survey.query.get_or_404(survey_id)
  page_view = PageView(page='/show_survey_results')
  db.session.add(page_view)
  db.session.commit()
  # Debugging: Print or log the survey object to ensure it has a filename attribute
  print("Survey filename:",
        survey.filename)  # Adjust according to your actual data structure
  if not hasattr(survey, 'filename'):
    # If the survey object doesn't have a filename attribute, handle the case appropriately
    print("Survey object does not have a filename attribute.")
    # Set a default filename or adjust your handling as needed
    survey.filename = 'default_filename'
  return render_template('results.html', survey=survey)


@profile_blueprint.route('/profile')
@login_required
def profile():
  agents_file = request.args.get('agents_file',
                                 'agents.json')  # Default to 'agents.json'
  agent_id = request.args.get('agent_id')

  agents_dir = os.path.join(current_user.folder_path, 'agents')
  copies_dir = os.path.join(agents_dir, 'copies')
  page_view = PageView(page='/profile')
  db.session.add(page_view)
  db.session.commit()

  logger.info(
      f"Accessing profile with agents_file: {agents_file} and agent_id: {agent_id}"
  )

  # Corrected the logic for determining the file path
  if agents_file == 'agents.json':
    agents_file_path = os.path.join(
        agents_dir, agents_file)  # For the main agents.json file
  else:
    # Correctly form the path for copies, avoiding duplication of 'agents/copies/'
    agents_file_path = os.path.join(
        copies_dir,
        os.path.basename(agents_file))  # Only use the basename for copies

  agent_copies = get_agent_copies(copies_dir)
  agents, _ = load_agents(agents_file_path)

  agent = get_agent_by_id(agents, agent_id)
  prev_agent_id, next_agent_id = get_prev_next_agent_ids(agents, agent)

  # Pass the correct file path or identifier as needed for AJAX or other calls
  agents_file_for_ui = 'agents.json' if agents_file == 'agents.json' else os.path.basename(
      agents_file)

  return render_template('profile.html',
                         agent=agent,
                         agents_file=agents_file_for_ui,
                         agent_copies=agent_copies,
                         prev_agent_id=prev_agent_id,
                         next_agent_id=next_agent_id)


def get_agent_copies(copies_dir):
  if os.path.isdir(copies_dir):
    agent_copies = [f for f in os.listdir(copies_dir) if f.endswith('.json')]
    logger.info(
        f"Found {len(agent_copies)} agent copies in directory: {copies_dir}")
  else:
    agent_copies = []
  return agent_copies


# Update load_agents function to accept the direct file path
def load_agents(agents_file_path):
  agents = []
  try:
    if os.path.exists(agents_file_path):
      with open(agents_file_path, 'r') as file:
        agents = json.load(file)
        logger.info(f"Successfully loaded agents from: {agents_file_path}")
    else:
      logger.warning(f"Agents file does not exist at: {agents_file_path}")
  except Exception as e:
    logger.error(f"Failed to load or parse agents JSON file: {e}",
                 exc_info=True)
    flash(f"Failed to load or parse agents JSON file: {e}", "error")

  return agents, agents_file_path


def get_agent_by_id(agents, agent_id):
  if agent_id:
    return next((a for a in agents if a['id'] == agent_id), None)
  return None


def get_prev_next_agent_ids(agents, agent):
  if agent:
    agent_index = agents.index(agent)
    prev_agent_id = agents[agent_index - 1]['id'] if agent_index > 0 else None
    next_agent_id = agents[agent_index +
                           1]['id'] if agent_index < len(agents) - 1 else None
  else:
    prev_agent_id = None
    next_agent_id = None
  return prev_agent_id, next_agent_id


@profile_blueprint.route('/update_agent', methods=['POST'])
@login_required
def update_agent():
  data = request.get_json()
  agent_id = data['agent_id']
  field = data['field']
  value = data['value']

  agents_data = current_user.agents_data
  agent = next((a for a in agents_data if a['id'] == agent_id), None)

  if agent:
    agent[field] = value
    db.session.commit()
    return jsonify(success=True)
  else:
    return jsonify(success=False, error="Agent not found")


@auth_blueprint.route('/agents/agents.json')
@login_required
def serve_agents_json():
  user_dir = current_user.folder_path
  agents_json_path = os.path.join(user_dir, 'agents', 'agents.json')
  if os.path.exists(agents_json_path):
    return send_file(agents_json_path)
  else:
    return abort(404)


@auth_blueprint.route('/agents/copies/<path:filename>')
@login_required
def serve_agent_copy_file(filename):
  user_dir = current_user.folder_path
  file_path = os.path.join(user_dir, 'agents', 'copies', filename)
  if os.path.exists(file_path):
    return send_file(file_path)
  else:
    return abort(404)


def extract_questions_from_form(form_data):
  questions = {}
  for key, value in form_data.items():
    if key.startswith('question_'):
      question_id = key.split('_')[1]
      question_type = form_data.get(f"question_{question_id}_type")
      questions[question_id] = {'type': question_type, 'text': value}
      if question_type == 'multiple_choice':
        options = form_data.getlist(f"question_{question_id}_options")
        questions[question_id]['options'] = options
      elif question_type == 'scale':
        min_value = int(form_data.get(f"question_{question_id}_min"))
        max_value = int(form_data.get(f"question_{question_id}_max"))
        questions[question_id]['min'] = min_value
        questions[question_id]['max'] = max_value
  return questions


@survey_blueprint.route('/public/survey/<public_url>')
def public_survey_results(public_url):
  survey = Survey.query.filter_by(public_url=public_url).first()

  if not survey or not survey.is_public:
    abort(404)

  return render_template('public_results.html', survey=survey)


@survey_blueprint.route('/public_folder_name')
def public_folder_name():
  # Logic to determine survey and foldername...
  survey = get_survey()  # Hypothetical function to get a Survey object
  foldername = calculate_foldername(
      survey)  # Hypothetical function to determine foldername

  page_view = PageView(page='/public_folder_name')
  db.session.add(page_view)
  db.session.commit()

  return render_template('public_results.html',
                         survey=survey,
                         foldername=foldername)


@survey_blueprint.route('/public/survey/<public_url>/data')
def public_survey_data(public_url):
  survey = Survey.query.filter_by(public_url=public_url).first()

  if not survey or not survey.is_public:
    abort(404)

  survey_data = survey.survey_data

  for agent in survey_data:
    agent['photo_path'] = url_for('serve_image',
                                  filename=agent['photo_path'].split('/')[-1])

  return jsonify(survey_data)


@survey_blueprint.route('/public/survey/<public_url>/pics/<filename>')
def public_survey_image(public_url, filename):
  survey = Survey.query.filter_by(public_url=public_url).first()

  if not survey or not survey.is_public:
    abort(404)

  file_path = os.path.join(os.path.dirname(survey.agents_file), 'pics',
                           filename)
  if os.path.exists(file_path):
    return send_file(file_path)
  else:
    abort(404)


@auth_blueprint.route('/logout')
@login_required
def logout():
  logout_user()
  response = make_response(redirect('/'))
  response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
  response.headers['Pragma'] = 'no-cache'
  response.headers['Expires'] = '0'
  page_view = PageView(page='/logout')
  db.session.add(page_view)
  db.session.commit()
  return response


def allowed_file(filename):
  return '.' in filename and filename.rsplit(
      '.', 1)[1].lower() in ALLOWED_EXTENSIONS


@start_blueprint.route('/start', methods=['GET', 'POST'])
def start_route():
  if request.method == 'POST':
    config = request.form.to_dict()
    with open('start-config.json', 'w') as file:
      json.dump(config, file)

    if 'run_start' in request.form:
      start.main()
      return redirect(url_for('start_blueprint.start_route'))

    if 'upload_files' in request.files:
      files = request.files.getlist('upload_files')
      for file in files:
        if file and allowed_file(file.filename):
          filename = secure_filename(file.filename)
          file_path = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                   filename)
          file.save(file_path)
          # Assuming extract_text.extract_and_save_text(file_path) exists and works as intended
          extract_text.extract_and_save_text(file_path)

  config = start.load_configuration()
  new_agent_files = os.listdir(UPLOAD_FOLDER)
  new_agent_files_content = {}

  for file in new_agent_files:
    with open(os.path.join(UPLOAD_FOLDER, file), 'r') as file_content:
      new_agent_files_content[file] = file_content.read()

  page_view = PageView(page='/start_route')
  db.session.add(page_view)
  try:
    db.session.commit()
  except Exception as e:
    app.logger.error(f"Failed to commit to DB: {e}")
    db.session.rollback()

  return render_template('start.html',
                         config=config,
                         new_agent_files=new_agent_files,
                         new_agent_files_content=new_agent_files_content)


@profile_blueprint.route('/create_new_agent', methods=['GET', 'POST'])
@login_required
def create_new_agent():
  if request.method == 'POST':
    agent_name = request.form['agent_name']
    agent_name = re.sub(r'[^a-zA-Z0-9\s]', '', agent_name).replace(' ', '_')
    jobtitle = request.form['jobtitle']
    agent_description = request.form['agent_description']

    new_agent_data = abe_gpt.generate_new_agent(agent_name, jobtitle,
                                                agent_description,
                                                current_user)
    return redirect(
        url_for('profile_blueprint.profile', agent_id=new_agent_data['id']))

  return render_template('new_agent.html')
