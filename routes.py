# routes.py
import os, json, random, re, glob, shutil, bleach, logging, uuid
import abe_gpt
import start
import base64

from models import db, User, Survey, Timeframe, Meeting
from abe_gpt import generate_new_agent
from abe import login_manager
import email_client

from PIL import Image
from io import BytesIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import User, Survey, db
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file, make_response, Response, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from logging.handlers import RotatingFileHandler

import time
from sqlalchemy.exc import OperationalError


#LOGGING

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message).142s',
    handlers=[
        logging.StreamHandler(),  # Console output
        RotatingFileHandler('logs/app.log', maxBytes=10000,
                            backupCount=3)  # File output
    ])

logger = logging.getLogger(__name__)

#PATHS

AGENTS_JSON_PATH = os.path.join('agents', 'agents.json')
IMAGES_BASE_PATH = os.path.join('agents', 'pics')
AGENTS_BASE_PATH = 'agents'
SURVEYS_BASE_PATH = 'surveys'
UPLOAD_FOLDER = 'agents/new_agent_files'
ALLOWED_EXTENSIONS = {'txt', 'doc', 'rtf', 'md', 'pdf'}

#BLUEPRINTS
start_blueprint = Blueprint('start_blueprint',
                            __name__,
                            template_folder='templates')

auth_blueprint = Blueprint('auth_blueprint',
                           __name__,
                           template_folder='templates')
meeting_blueprint = Blueprint('meeting_blueprint',
                              __name__,
                              template_folder='templates')

dashboard_blueprint = Blueprint('dashboard_blueprint',
                                __name__,
                                template_folder='templates')

profile_blueprint = Blueprint('profile_blueprint',
                              __name__,
                              template_folder='templates')

#API LIMITER
limiter = Limiter(key_func=get_remote_address,
                  default_limits=["200 per day", "50 per hour"])


#PAGE VIEW ANALYTICS
class PageView(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  page = db.Column(db.String(50), nullable=False)
  timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


#LOGIN / AUTH


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


#  page_view = PageView(page='/login')
# db.session.add(page_view)
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
    new_user.create_user_data(
    )  # Call create_user_data instead of create_user_folder
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


@auth_blueprint.route('/add_base_agents', methods=['POST'])
@login_required
def add_base_agents():
  logging.info("Starting to add base agents")
  try:
    base_agents_path = os.path.join('agents', 'agents.json')
    logging.info(f"Reading base agents from {base_agents_path}")
    with open(base_agents_path, 'r') as file:
      base_agents_data = json.load(file)

    current_user.images_data = {
    }  # Initialize images_data as an empty dictionary
    current_user.thumbnail_images_data = {
    }  # Initialize thumbnail_images_data as an empty dictionary
    logging.info(
        "Initialized images_data and thumbnail_images_data as empty dictionaries"
    )

    for agent in base_agents_data:
      photo_filename = os.path.basename(agent['photo_path'])
      image_path = os.path.join('agents', 'pics', photo_filename)
      logging.info(f"Processing image {photo_filename}")

      with open(image_path, 'rb') as image_file:
        img_data = image_file.read()
        encoded_string = base64.b64encode(img_data).decode('utf-8')
      current_user.images_data[photo_filename] = encoded_string

      # Generate thumbnail image
      thumbnail_size = (200, 200)
      img = Image.open(BytesIO(img_data))
      img.thumbnail(thumbnail_size)
      thumbnail_buffer = BytesIO()
      img.save(thumbnail_buffer, format='PNG')
      thumbnail_data = thumbnail_buffer.getvalue()
      thumbnail_encoded_string = base64.b64encode(thumbnail_data).decode(
          'utf-8')
      current_user.thumbnail_images_data[
          photo_filename + '_thumbnail'] = thumbnail_encoded_string

    current_user.agents_data = base_agents_data
    db.session.commit()
    logging.info(
        "Successfully added base agents and committed to the database")

    return redirect(url_for('home'))
  except Exception as e:
    logging.error(f"Failed to add base agents due to an exception: {str(e)}",
                  exc_info=True)
    return jsonify({'success': False, 'error': str(e)})


@meeting_blueprint.route('/surveys/<path:survey_id>/pics/<filename>')
@login_required
def serve_survey_image(survey_id, filename):
  user_dir = current_user.folder_path
  file_path = os.path.join(user_dir, 'surveys', survey_id, 'pics', filename)
  if os.path.exists(file_path):
    return send_file(file_path)
  else:
    abort(404)


@meeting_blueprint.route('/meeting/<int:meeting_id>', methods=['GET', 'POST'])
@login_required
def meeting_form(meeting_id):
  meeting = Meeting.query.get_or_404(meeting_id)
  if meeting.user_id != current_user.id:
    abort(403)

  if request.method == 'POST':
    questions = extract_questions_from_form(request.form)
    selected_agent_ids = request.form.getlist('selected_agents')
    llm_instructions = request.form.get('llm_instructions', '')
    request_type = request.form.get('request_type', 'iterative')

    selected_agents_data = [
        agent for agent in meeting.agents
        if str(agent['id']) in selected_agent_ids
    ]

    payload = {
        "agents_data": selected_agents_data,
        "questions": questions,
        "llm_instructions": llm_instructions,
        "request_type": request_type,
    }

    meeting_responses = abe_gpt.conduct_meeting(payload, current_user)

    answers = {}
    for agent_data, response in zip(selected_agents_data, meeting_responses):
      answers[agent_data['id']] = response['responses']

    meeting.agents = selected_agents_data
    meeting.questions = questions
    meeting.answers = answers
    db.session.commit()

    return redirect(
        url_for('meeting_blueprint.meeting_results', meeting_id=meeting.id))
  else:
    agents_data = meeting.agents
    return render_template('meeting2.html',
                           meeting=meeting,
                           agents=agents_data)


@meeting_blueprint.route('/meeting/<int:meeting_id>/results',
                         methods=['GET', 'POST'])
@login_required
def meeting_results(meeting_id):
  meeting = Meeting.query.get_or_404(meeting_id)
  if meeting.user_id != current_user.id:
    abort(403)

  if request.method == 'POST':
    is_public = request.form.get('is_public') == 'on'
    meeting.is_public = is_public

    if is_public and not meeting.public_url:
      meeting.public_url = str(uuid.uuid4())
    elif not is_public:
      meeting.public_url = None

    db.session.commit()

  prev_meeting = Meeting.query.filter(Meeting.user_id == current_user.id,
                                      Meeting.id < meeting.id).order_by(
                                          Meeting.id.desc()).first()
  next_meeting = Meeting.query.filter(Meeting.user_id == current_user.id,
                                      Meeting.id > meeting.id).order_by(
                                          Meeting.id).first()

  return render_template('results.html',
                         meeting=meeting,
                         is_public=meeting.is_public,
                         prev_meeting=prev_meeting,
                         next_meeting=next_meeting)


@dashboard_blueprint.route('/dashboard')
@login_required
def dashboard():
    timeframe_id = request.args.get('timeframe_id')
    agents_data = []

    if timeframe_id:
        timeframe = Timeframe.query.get(timeframe_id)
        if timeframe and timeframe.user_id == current_user.id:
            agents_data = json.loads(timeframe.agents_data)
            logger.info(f"Loaded agents data from timeframe {timeframe_id}")

            # Fetch the base64-encoded image data for each agent in the timeframe
            images_data = json.loads(timeframe.images_data)
            for agent in agents_data:
                if 'photo_path' in agent:
                    photo_filename = agent['photo_path'].split('/')[-1]
                    agent['image_data'] = images_data.get(photo_filename, '')
                    logger.debug(f"Fetched image data for agent {agent['id']} in timeframe {timeframe_id}")
                else:
                    agent['image_data'] = ''
        else:
            abort(404)
    else:
        agents_data = current_user.agents_data or []
        logger.info("Loaded base agents")

        # Fetch the base64-encoded image data for each base agent
        for agent in agents_data:
            if 'photo_path' in agent:  # Check if 'photo_path' key exists
                agent['image_data'] = current_user.images_data.get(
                    agent['photo_path'].split('/')[-1], '')
            else:
                agent['image_data'] = ''  # Set a default value if 'photo_path' is missing

    timeframes = current_user.timeframes
    logger.info(f"Timeframes for user {current_user.id}: {timeframes}")

    return render_template('dashboard.html',
                           agents=agents_data,
                           timeframes=timeframes)

@profile_blueprint.route('/profile')
@login_required
def profile():
  agent_id = request.args.get('agent_id')
  agents_data = current_user.agents_data or []

  agent = get_agent_by_id(agents_data, agent_id)
  prev_agent_id, next_agent_id = get_prev_next_agent_ids(agents_data, agent)

  if agent:
    # Fetch the base64-encoded image data from the images_data attribute
    agent['image_data'] = current_user.images_data.get(
        agent['photo_path'].split('/')[-1], '')

  return render_template('profile.html',
                         agent=agent,
                         prev_agent_id=prev_agent_id,
                         next_agent_id=next_agent_id)


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


@login_manager.user_loader
def load_user(user_id):
    max_retries = 3
    retry_delay = 1
    retry_count = 0

    while retry_count < max_retries:
        try:
            return User.query.get(int(user_id))
        except OperationalError as e:
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise e


@auth_blueprint.route('/get_main_agents')
@login_required
def get_main_agents():
  logger.info(f"Retrieving main agents for user: {current_user.id}")
  main_agents = current_user.agents_data or []
  for agent in main_agents:
    photo_path = agent['photo_path'].split('/')[-1]
    logger.debug(
        f"Retrieving image data for agent: {agent['id']}, photo_path: {photo_path}"
    )
    agent['image_data'] = current_user.images_data.get(photo_path, '')
  logger.info(
      f"Retrieved {len(main_agents)} main agents for user: {current_user.id}")
  return jsonify(main_agents)


@auth_blueprint.route('/get_timeframe_agents')
@login_required
def get_timeframe_agents():
    logger.info(f"Retrieving timeframe agents for user: {current_user.id}")
    timeframes = current_user.timeframes
    timeframe_agents = []

    for timeframe in timeframes:
        logger.debug(f"Processing timeframe: {timeframe.id}")
        agents_data = json.loads(timeframe.agents_data)
        images_data = json.loads(timeframe.images_data)
        for agent in agents_data:
            photo_filename = agent['photo_path'].split('/')[-1]
            agent['timeframe_id'] = timeframe.id
            agent['timeframe_name'] = timeframe.name
            agent['image_data'] = images_data.get(photo_filename, '')
            timeframe_agents.append(agent)
            logger.debug(f"Added agent: {agent['id']} to timeframe_agents")

    logger.info(
        f"Retrieved {len(timeframe_agents)} timeframe agents for user: {current_user.id}"
    )
    return jsonify(timeframe_agents)


@meeting_blueprint.route('/meeting/create', methods=['GET', 'POST'])
@login_required
def create_meeting():
  logger.info(f"Creating meeting for user: {current_user.id}")
  if request.method == 'POST':
    meeting_name = request.form.get('meeting_name')
    agent_source = request.form.get('agent_source')
    selected_agent_ids = request.form.get('selected_agents', '').split(',')
    logger.debug(
        f"Meeting name: {meeting_name}, Agent source: {agent_source}, Selected agent IDs: {selected_agent_ids}"
    )

    if agent_source == 'main_agents':
      agents_data = current_user.agents_data
      logger.debug("Using main agents as the agent source")
    else:
      try:
        timeframe_id = int(agent_source.split('_')[1])
        timeframe = Timeframe.query.get(timeframe_id)
        logger.debug(f"Using timeframe {timeframe_id} as the agent source")
        if timeframe and timeframe.user_id == current_user.id:
          agents_data = timeframe.agents_data
        else:
          logger.warning(f"Invalid timeframe selected: {timeframe_id}")
          flash('Invalid timeframe selected.')
          return redirect(url_for('meeting_blueprint.create_meeting'))
      except (IndexError, ValueError):
        logger.error("Invalid agent source format")
        flash('Invalid agent source format.')
        return redirect(url_for('meeting_blueprint.create_meeting'))

    selected_agents = [
        agent for agent in agents_data
        if str(agent['id']) in selected_agent_ids
    ]
    logger.debug(f"Selected agents: {selected_agents}")

    if not selected_agents:
      logger.warning("No agents selected")
      flash('No agents selected.')
      return redirect(url_for('meeting_blueprint.create_meeting'))

    new_meeting = Meeting(name=meeting_name,
                          user_id=current_user.id,
                          agents=selected_agents)
    db.session.add(new_meeting)
    db.session.commit()
    logger.info(
        f"Created new meeting with ID: {new_meeting.id} for user: {current_user.id}"
    )

    return redirect(
        url_for('meeting_blueprint.meeting_form', meeting_id=new_meeting.id))
  else:
    logger.debug("Rendering meeting1.html template")
    return render_template('meeting1.html')


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


@meeting_blueprint.route('/public/meeting/<public_url>')
def public_meeting_results(public_url):
  meeting = Meeting.query.filter_by(public_url=public_url).first()

  if not meeting or not meeting.is_public:
    abort(404)

  return render_template('public_results.html', meeting=meeting)


@meeting_blueprint.route('/public/meeting/<public_url>/data')
def public_meeting_data(public_url):
  meeting = Meeting.query.filter_by(public_url=public_url).first()

  if not meeting or not meeting.is_public:
    abort(404)

  meeting_data = {
      'name': meeting.name,
      'agents': meeting.agents,
      'questions': meeting.questions,
      'answers': meeting.answers
  }

  for agent in meeting_data['agents']:
    agent['photo_path'] = url_for('serve_image',
                                  filename=agent['photo_path'].split('/')[-1])

  return jsonify(meeting_data)


@meeting_blueprint.route('/public/survey/<public_url>/data')
def public_survey_data(public_url):
  survey = Survey.query.filter_by(public_url=public_url).first()

  if not survey or not survey.is_public:
    abort(404)

  survey_data = survey.survey_data

  for agent in survey_data:
    agent['photo_path'] = url_for('serve_image',
                                  filename=agent['photo_path'].split('/')[-1])

  return jsonify(survey_data)


@meeting_blueprint.route('/public/survey/<public_url>/pics/<filename>')
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
  page_view = PageView(page='/')
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
  if current_user.credits is None or current_user.credits <= 0:
    flash(
        "You don't have enough credits. Please contact the admin to add more credits."
    )
    return redirect(url_for('home'))
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


@profile_blueprint.route('/edit_agent/<agent_id>', methods=['GET', 'POST'])
@login_required
def edit_agent(agent_id):
  agents_data = current_user.agents_data or []
  agent = get_agent_by_id(agents_data, agent_id)

  if request.method == 'POST':
    # Update the agent data based on the form submission
    agent['persona'] = request.form.get('persona')
    agent['summary'] = request.form.get('summary')
    agent['keywords'] = request.form.get('keywords').split(',')
    agent['image_prompt'] = request.form.get('image_prompt')
    agent['relationships'] = json.loads(request.form.get('relationships'))
    db.session.commit()
    return redirect(url_for('profile_blueprint.profile', agent_id=agent_id))

  return render_template('edit_agent.html', agent=agent)


@profile_blueprint.route('/delete_agent/<agent_id>', methods=['POST'])
@login_required
def delete_agent(agent_id):
  agents_data = current_user.agents_data or []
  agent = get_agent_by_id(agents_data, agent_id)

  if agent:
    agents_data.remove(agent)
    db.session.commit()
    return jsonify({'success': True})
  else:
    return jsonify({'success': False, 'error': 'Agent not found'})


@profile_blueprint.route('/status')
@login_required
def status():
  email_status = 'working' if email_client.is_running() else 'error'
  num_agents = len(current_user.agents_data)
  user_credits = current_user.credits
  return render_template('status.html',
                         status=email_status,
                         num_agents=num_agents,
                         user_credits=user_credits)


@auth_blueprint.route('/new_timeframe', methods=['GET', 'POST'])
@login_required
def create_timeframe():
  logging.info("Handling request in create_timeframe route")
  if request.method == 'POST':
    logging.info("Inside POST block")

    if current_user.credits is None or current_user.credits <= 0:
      logging.info("User has insufficient credits")
      flash(
          "You don't have enough credits. Please contact the admin to add more credits."
      )
      return redirect(url_for('home'))

    selected_agent_ids = request.form.getlist('selected_agents')
    if not selected_agent_ids:
      # If no agents are selected, flash a message and redirect back to the same page
      flash("Please select at least one agent to proceed.", "warning")
      return redirect(url_for('auth_blueprint.create_timeframe'))

    agents_data = current_user.agents_data
    selected_agents_data = [
        agent for agent in agents_data
        if str(agent['id']) in selected_agent_ids
    ]

    form_data = request.form.to_dict()
    form_data.pop('selected_agents', None)

    payload = {
        "agents_data": selected_agents_data,
        "instructions": form_data,
        "timeframe_name": form_data["name"]
    }

    try:
        logging.info("Calling process_agents function")
        new_timeframe = abe_gpt.process_agents(payload, current_user)
        logging.info(f"New timeframe object received: {new_timeframe}")

        logging.info(f"New timeframe created with ID: {new_timeframe.id}")

        # Redirect to the dashboard for the new timeframe
        return redirect(url_for('dashboard_blueprint.dashboard', timeframe_id=new_timeframe.id))

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error occurred while processing agents: {str(e)}")
        flash(f"An error occurred while processing agents: {str(e)}", "error")
        return redirect(url_for('auth_blueprint.create_timeframe'))


  else:
    logger.info('Accessing new timeframe page')
    base_agents = current_user.agents_data or []
    timeframes = current_user.timeframes

    logger.info(f'Base agents count: {len(base_agents)}')
    logger.info(f'Timeframes count: {len(timeframes)}')

    return render_template('new_timeframe.html',
                           base_agents=base_agents,
                           timeframes=timeframes)



@auth_blueprint.route('/users/generate_api_key', methods=['POST'])
@login_required
def generate_api_key():
  # Generate and return API key
  token = current_user.generate_api_key()
  db.session.commit()
  flash('API Key generated successfully!', 'success')
  return redirect(url_for('auth_blueprint.update_profile'))


@auth_blueprint.route('/users/verify_password', methods=['POST'])
@login_required
def verify_password():
  password = request.form.get('password')
  if current_user.check_password(password):
    # Return API key(s) if password verification succeeds
    api_keys = [api_key.key for api_key in current_user.api_keys]
    return jsonify({'success': True, 'api_keys': api_keys})
  else:
    # Handle failed password verification
    return jsonify({'success': False, 'message': 'Incorrect password'}), 401


def verify_api_key(request):
  api_key = request.headers.get('Authorization')
  if api_key:
    api_key = APIKey.query.filter_by(key=api_key).first()
    if api_key and api_key.owner.credits > 0:
      api_key.owner.credits -= 1
      db.session.commit()
      return api_key.owner
  return None


@auth_blueprint.before_request
def before_request_func():
  current_user = verify_api_key(request)
  if not current_user and request.path.startswith('/api/'):
    return jsonify({'error': 'Unauthorized or insufficient credits'}), 401


@auth_blueprint.route('/api/agents', methods=['GET'])
@limiter.limit("10 per minute")
def get_agents():
  # Assuming the agents.json data is per-user and stored in the database for simplicity
  agents_data = current_user.agents_data
  if agents_data:
    return jsonify(agents_data), 200
  return jsonify({'error': 'No agents data found'}), 404
