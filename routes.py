# routes.py
import os
import json
import re
import bleach
import logging
import uuid
import abe_gpt
import start
import base64
import binascii

from models import db, User, Survey, Timeframe, Meeting, Agent, Image
from abe import login_manager
from talker import talker_blueprint
import email_client

from io import BytesIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

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

talker_blueprint = Blueprint('talker_blueprint',
                             __name__,
                             template_folder='templates')

timeframes_blueprint = Blueprint('timeframes_blueprint',
                                 __name__,
                                 template_folder='templates')

doc2api_blueprint = Blueprint('doc2api_blueprint', __name__)

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
    try:
      questions = extract_questions_from_form(request.form)
      selected_agent_ids = request.form.getlist('selected_agents')
      llm_instructions = request.form.get('llm_instructions', '')
      request_type = request.form.get('request_type', 'iterative')

      selected_agents_data = [
          agent for agent in meeting.agents
          if str(agent['id']) in selected_agent_ids
      ]

      payload = {
          "meeting_id": meeting_id,
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
    except Exception as e:
      if "Insufficient credits" in str(e):
        return redirect(url_for('auth_blueprint.update_profile'))
      else:
        raise  # Re-raise the exception if it's not the one we're catching
  else:
    agents_data = meeting.agents
    return render_template('meeting2.html',
                           meeting=meeting,
                           agents=agents_data)


@meeting_blueprint.route('/meeting/<int:meeting_id>/results', methods=['GET', 'POST'])
@login_required
def meeting_results(meeting_id):
    meeting = Meeting.query.get(meeting_id)
    agents_data = meeting.agents

    for agent in agents_data:
        agent['photo_path'] = agent['photo_path'].split('/')[-1]

    if meeting.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
      is_public = request.form.get('is_public') == 'on'
      meeting.is_public = is_public
  
      if is_public:
        if not meeting.public_url:
          meeting.public_url = str(uuid.uuid4())
          logger.info(f"Generated public_url: {meeting.public_url}")
        public_url = url_for('meeting_blueprint.public_meeting_results',
                             public_url=meeting.public_url,
                             _external=True)
        logger.info(f"Full public URL: {public_url}")
  
        # Save the image files in the public folder
        public_folder = 'public'
        os.makedirs(public_folder, exist_ok=True)
        for agent in meeting.agents:
          filename = agent['photo_path'].split('/')[-1]
  
          # Check if the agent is from a Timeframe
          timeframe = Timeframe.query.filter(
              Timeframe.agents_data.contains(json.dumps(agent))).first()
          if timeframe:
            # If the agent is from a Timeframe, get the image data from the Timeframe's images_data
            images_data = json.loads(timeframe.images_data)
            image_data = images_data.get(filename)
            logger.info(
                f"Agent {agent['id']} image data retrieved from Timeframe {timeframe.id}"
            )
          else:
            # If the agent is a Main Agent, get the image data from the user's images_data
            image_data = current_user.images_data.get(filename)
            logger.info(
                f"Agent {agent['id']} image data retrieved from User {current_user.id}"
            )
  
          if image_data:
            image_data = base64.b64decode(image_data)
            file_path = os.path.join(public_folder, secure_filename(filename))
            with open(file_path, 'wb') as file:
              file.write(image_data)
            logger.info(f"Agent {agent['id']} image saved to {file_path}")
          else:
            logger.warning(f"Missing image data for agent: {agent['id']}")
      else:
        meeting.public_url = None
        public_url = None
        logger.info("Meeting is not public")
  
      db.session.commit()
      return redirect(
          url_for('meeting_blueprint.meeting_results', meeting_id=meeting.id))
  
    prev_meeting = Meeting.query.filter(Meeting.user_id == current_user.id,
                                        Meeting.id < meeting.id).order_by(
                                            Meeting.id.desc()).first()
    next_meeting = Meeting.query.filter(Meeting.user_id == current_user.id,
                                        Meeting.id > meeting.id).order_by(
                                            Meeting.id).first()
  
    # Retrieve the meeting summary and image data from the database
    meeting.summary = meeting.summary if meeting.summary else None
    meeting.image_data = meeting.image_data if meeting.image_data else None
    meeting.thumbnail_image_data = meeting.thumbnail_image_data if meeting.thumbnail_image_data else None
  
    logger.info(f"Meeting {meeting.id} summary: {meeting.summary}")
    logger.info(
        f"Meeting {meeting.id} image data: {meeting.image_data[:50] if meeting.image_data else None}"
    )
    logger.info(
        f"Meeting {meeting.id} thumbnail image data: {meeting.thumbnail_image_data[:50] if meeting.thumbnail_image_data else None}"
    )
  
    if meeting.image_data:
      logger.info(
          f"Meeting {meeting.id} image data type: {type(meeting.image_data)}")
      logger.info(
          f"Meeting {meeting.id} image data length: {len(meeting.image_data)}")
      logger.info(
          f"Meeting {meeting.id} image URL: {url_for('meeting_blueprint.serve_meeting_image', meeting_id=meeting.id, _external=True)}"
      )
    else:
      logger.warning(f"No image data found for Meeting {meeting.id}")
  
    prev_meeting = Meeting.query.filter(Meeting.user_id == current_user.id,
                                        Meeting.id < meeting.id).order_by(
                                            Meeting.id.desc()).first()
    next_meeting = Meeting.query.filter(Meeting.user_id == current_user.id,
                                        Meeting.id > meeting.id).order_by(
                                            Meeting.id).first()
  
    # Update the answer extraction logic
    for agent_id, answers in meeting.answers.items():
      for question_id, answer in answers.items():
        if isinstance(answer, dict) and 'response' in answer:
          meeting.answers[agent_id][question_id] = answer['response']
        elif isinstance(answer, str):
          try:
            answer_json = json.loads(answer)
            if isinstance(answer_json, dict) and 'response' in answer_json:
              meeting.answers[agent_id][question_id] = answer_json['response']
          except (json.JSONDecodeError, TypeError):
            pass
  
    return render_template('results.html', meeting=meeting, agents_data=agents_data)

@meeting_blueprint.route('/meetings')
@login_required
def meetings():
    user_meetings = Meeting.query.filter_by(user_id=current_user.id).all()

    for meeting in user_meetings:
        # Load the summary image data for each meeting
        meeting.image_data = meeting.image_data if meeting.image_data else None

        # Load the agents involved in each meeting
        for agent in meeting.agents:
            if 'photo_path' in agent:
                agent['photo_path'] = agent['photo_path'].split('/')[-1]

    return render_template('meetings.html', meetings=user_meetings) 

@dashboard_blueprint.route('/dashboard')
@login_required
def dashboard():
  timeframe_id = request.args.get('timeframe_id')
  agents_data = []
  timeframe = None

  if timeframe_id:
    timeframe = Timeframe.query.get(timeframe_id)
    if timeframe and timeframe.user_id == current_user.id:
      agents_data = json.loads(timeframe.agents_data)
      for agent in agents_data:
        agent['photo_path'] = agent.get('photo_path', '')
    else:
      abort(404)
  else:
    user_agents = current_user.agents_data or []
    agent_class_agents = Agent.query.filter_by(user_id=current_user.id).all()

    for agent in user_agents:
      agent['photo_path'] = agent.get('photo_path', '')
      agents_data.append(agent)

    for agent in agent_class_agents:
      agent_data = {
          'id': agent.id,
          'jobtitle': agent.data.get('jobtitle', ''),
          'summary': agent.data.get('summary', ''),
          'photo_path': agent.data.get('photo_path', ''),
      }
      agents_data.append(agent_data)

  timeframes = current_user.timeframes

  return render_template('dashboard.html',
                         agents=agents_data,
                         timeframes=timeframes,
                         timeframe=timeframe)


def get_prev_next_agent_ids(agents, agent):
  prev_agent_id = None
  next_agent_id = None
  if agent:
    agent_index = next(
        (index for index, a in enumerate(agents) if a.id == agent.id), None)
    if agent_index is not None:
      prev_agent_id = agents[agent_index - 1].id if agent_index > 0 else None
      next_agent_id = agents[agent_index +
                             1].id if agent_index < len(agents) - 1 else None
  return prev_agent_id, next_agent_id


@timeframes_blueprint.route('/timeframe_images/<int:timeframe_id>')
def serve_timeframe_image(timeframe_id):
  logging.info(f"Attempting to serve image for timeframe {timeframe_id}")
  timeframe = Timeframe.query.get(timeframe_id)
  if not timeframe:
    logging.error(f"Timeframe with ID {timeframe_id} not found.")
    abort(404)

  if not timeframe.image_data:
    logging.error(
        f"No image data found for timeframe {timeframe_id}. Data: {timeframe.image_data}"
    )
    abort(404)

  try:
    image_data = base64.b64decode(timeframe.summary_image_data)
    return Response(image_data, mimetype='image/png')
  except Exception as e:
    logging.error(f"Failed to serve image for timeframe {timeframe_id}: {e}")
    abort(500)

@timeframes_blueprint.route('/timeframe/<int:timeframe_id>')
def single_timeframe(timeframe_id):
    logging.info(f"Retrieving timeframe with ID: {timeframe_id}")
    timeframe = Timeframe.query.get(timeframe_id)

    if timeframe:
        logging.info(f"Timeframe found: {timeframe.name}")

        if timeframe.summary_image_data:
            logging.info(f"Timeframe summary image data: {timeframe.summary_image_data[:100]}...")
        else:
            logging.warning("Timeframe summary image data is None")

        logging.info(f"Timeframe summary: {timeframe.summary}")

        if timeframe.summary_thumbnail_image_data:
            logging.info(f"Timeframe summary thumbnail image data: {timeframe.summary_thumbnail_image_data[:100]}...")
        else:
            logging.warning("Timeframe summary thumbnail image data is None")

        logging.info("Loading agents data...")
        agents_data = json.loads(timeframe.agents_data)
        logging.info(f"Loaded {len(agents_data)} agents from timeframe agents_data")

        # Load user agents
        logging.info("Loading user agents...")
        user_agents = current_user.agents_data or []
        for agent in user_agents:
            if 'id' in agent:
                agent['agent_type'] = 'user'
                agents_data.append(agent)
        logging.info(f"Loaded {len(user_agents)} user agents")

        # Load timeframe agents
        logging.info("Loading timeframe agents...")
        for agent in agents_data:
            if 'id' in agent:
                agent['agent_type'] = 'timeframe'
        logging.info(f"Loaded {len(agents_data)} timeframe agents")

        # Load Agent class agents
        logging.info("Loading Agent class agents...")
        agent_class_agents = Agent.query.filter_by(user_id=current_user.id).all()
        for agent in agent_class_agents:
            if hasattr(agent, 'id'):
                agent_data = agent.data
                agent_data['agent_type'] = 'agent'
                agents_data.append(agent_data)
        logging.info(f"Loaded {len(agent_class_agents)} Agent class agents")

        logging.info("Parsing agents data...")
        parsed_agents_data = []
        for agent in agents_data:
            if 'photo_path' in agent:
                photo_filename = agent['photo_path'].split('/')[-1]
                agent['image_data'] = json.loads(timeframe.images_data).get(photo_filename, '')
            parsed_agents_data.append(agent)
        logging.info(f"Parsed {len(parsed_agents_data)} agents")

        timeframe.parsed_agents_data = parsed_agents_data

        logging.info("Rendering single_timeframe.html template")
        return render_template('single_timeframe.html', timeframe=timeframe)
    else:
        logging.error(f"Timeframe not found for ID: {timeframe_id}")
        abort(404)

@timeframes_blueprint.route('/timeframes')
@login_required
def timeframes():
  timeframes = current_user.timeframes

  for timeframe in timeframes:
    parsed_agents_data = json.loads(timeframe.agents_data)
    for agent in parsed_agents_data:
      if 'photo_path' in agent:
        photo_filename = agent['photo_path'].split('/')[-1]
        agent['image_data'] = json.loads(timeframe.images_data).get(
            photo_filename, '')

    timeframe.parsed_agents_data = parsed_agents_data

    # Decode the base64-encoded image data for the timeframe
    if timeframe.images_data:
      try:
          timeframe.decoded_image_data = base64.b64decode(timeframe.images_data, validate=True)
      except binascii.Error:
          logging.error(f"Invalid base64 data for timeframe {timeframe.id}. Data: {timeframe.images_data}")
          timeframe.decoded_image_data = None
    else:
      timeframe.decoded_image_data = None

    # Log the timeframe summary
    logging.info(f"Timeframe {timeframe.id} summary: {timeframe.summary}")

    # Load the summary, image data, and thumbnail image data for the timeframe
    timeframe.summary = timeframe.summary if timeframe.summary else None
    timeframe.summary_image_data = timeframe.summary_image_data if timeframe.summary_image_data else None
    timeframe.summary_thumbnail_image_data = timeframe.summary_thumbnail_image_data if timeframe.summary_thumbnail_image_data else None

  return render_template('timeframes.html', timeframes=timeframes)


@profile_blueprint.route('/profile')
@login_required
def profile():
  agent_id = request.args.get('agent_id')
  timeframe_id = request.args.get('timeframe_id')

  if timeframe_id:
    timeframe = Timeframe.query.get(timeframe_id)
    if timeframe and timeframe.user_id == current_user.id:
      agents_data = json.loads(timeframe.agents_data)
      agent_data = next((agent for agent in agents_data
                         if str(agent.get('id', '')) == str(agent_id)), None)
      if agent_data:
        agent = Agent(id=agent_data['id'],
                      user_id=current_user.id,
                      data=agent_data)
        agent.agent_type = 'timeframe'
        photo_filename = agent.data.get('photo_path', '').split('/')[-1]
        images_data = json.loads(timeframe.images_data)
        agent_image_data = images_data.get(photo_filename, '')
        timeframe_agents = [{
            'timeframe_id': timeframe.id,
            'timeframe_name': timeframe.name,
            'agent': agent
        }]
        main_agent = None
      else:
        flash('Agent not found within the specified timeframe.', 'error')
        return redirect(url_for('dashboard_blueprint.dashboard'))
    else:
      flash('Invalid timeframe.', 'error')
      return redirect(url_for('dashboard_blueprint.dashboard'))
  else:
    agent = Agent.query.filter((Agent.user_id == current_user.id) & (
        (Agent.id == str(agent_id))
        | (Agent.id == agent_id.replace('_', '.')))).first()

    if not agent:
      agent_data = next(
          (agent
           for agent in current_user.agents_data if str(agent.get('id', '')) in
           [str(agent_id), agent_id.replace('_', '.')]), None)
      if agent_data:
        agent = Agent(id=agent_data['id'],
                      user_id=current_user.id,
                      data=agent_data)
        agent.agent_type = 'agent'
        photo_filename = agent.data.get('photo_path', '').split('/')[-1]
        agent_image_data = current_user.images_data.get(photo_filename, '')
      else:
        flash('Agent not found.', 'error')
        return redirect(url_for('dashboard_blueprint.dashboard'))
    else:
      agent.agent_type = agent.data.get('agent_type', 'agent')
      photo_filename = agent.data.get('photo_path', '').split('/')[-1]
      agent_image_data = current_user.images_data.get(photo_filename, '')
      if not agent_image_data:
        agent_image_data = agent.data.get('image_data', {}).get(
            agent.data.get('photo_path', ''), '')

    main_agent = agent
    timeframe_agents = []

  if agent:
    logging.debug(f"Agent data in profile route: {agent.data}")
    agents = current_user.agents + Agent.query.filter_by(
        user_id=current_user.id).all()
    prev_agent_id, next_agent_id = get_prev_next_agent_ids(agents, agent)

    return render_template('profile.html',
                           agent=agent,
                           agent_image_data=agent_image_data,
                           main_agent=main_agent,
                           timeframe_agents=timeframe_agents,
                           timeframe_id=timeframe_id,
                           prev_agent_id=prev_agent_id,
                           next_agent_id=next_agent_id,
                           talk_to_agent_url=url_for(
                               'talker_blueprint.talker',
                               agent_type=agent.agent_type,
                               agent_id=agent.id))
  else:
    flash('Agent not found.', 'error')
    return redirect(url_for('dashboard_blueprint.dashboard'))


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


@auth_blueprint.route('/get_main_agents', methods=['GET'])
@login_required
def get_main_agents():
  logger.info(f"Retrieving main agents for user: {current_user.id}")
  main_agents = current_user.agents_data or []
  for agent in main_agents:
    photo_path = agent['photo_path'].split('/')[-1]
    agent['image_data'] = current_user.images_data.get(photo_path, '')
  logger.info(
      f"Retrieved {len(main_agents)} main agents for user: {current_user.id}")
  return jsonify(main_agents)


@auth_blueprint.route('/get_timeframe_agents')
@login_required
def get_timeframe_agents():
  timeframe_id = request.args.get('timeframe_id')
  if not timeframe_id:
    return jsonify({'error': 'Timeframe ID is required'}), 400

  timeframe = Timeframe.query.get(timeframe_id)
  if not timeframe:
    return jsonify({'error': 'Timeframe not found'}), 404

  agents_data = json.loads(timeframe.agents_data)
  valid_agents = [agent for agent in agents_data if 'id' in agent]

  for agent in valid_agents:
    photo_path = agent['photo_path'].split('/')[-1]
    agent['image_data'] = current_user.images_data.get(photo_path, '')

  return jsonify(valid_agents)


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
          agents_data = json.loads(timeframe.agents_data)
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
        if 'id' in agent and str(agent['id']) in selected_agent_ids
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
    timeframes = current_user.timeframes
    return render_template('meeting1.html', timeframes=timeframes)


def get_agent_by_id(agents, agent_id):
  if agent_id:
    return next((a for a in agents if str(a.get('id')) == str(agent_id)), None)
  return None


def get_relationships(agent):
  if isinstance(agent.get('relationships'), list):
    return agent['relationships']
  elif isinstance(agent.get('relationships'), str):
    try:
      return json.loads(agent['relationships'])
    except json.JSONDecodeError:
      return []
  else:
    return []


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


@auth_blueprint.route('/agent_images/<filename>')
def serve_agent_image(filename):
  if current_user.is_authenticated:
    image_data = current_user.images_data.get(filename)
    if image_data:
      return Response(base64.b64decode(image_data), mimetype='image/png')
  abort(404)


@auth_blueprint.route('/agents/agents.json')
@login_required
def serve_agents_json():
  user_dir = current_user.folder_path
  agents_json_path = os.path.join(user_dir, 'agents', 'agents.json')
  if os.path.exists(agents_json_path):
    return send_file(agents_json_path)
  else:
    return abort(404)


@meeting_blueprint.route('/meeting_images/<int:meeting_id>')
def serve_meeting_image(meeting_id):
  meeting = Meeting.query.get(meeting_id)
  if meeting and meeting.image_data:
    if meeting.is_public or (current_user.is_authenticated
                             and meeting.user_id == current_user.id):
      try:
        image_data = base64.b64decode(meeting.image_data)
        return Response(image_data, mimetype='image/png')
      except Exception as e:
        logging.error(f"Failed to serve image for meeting {meeting_id}: {e}")
        abort(500)
      return Response(image_data, mimetype='image/png')
  abort(404)


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
  logger.info(f"Accessing public meeting results for URL: {public_url}")
  meeting = Meeting.query.filter_by(public_url=public_url).first()

  if not meeting or not meeting.is_public:
    logger.warning(
        f"Public meeting not found or not public for URL: {public_url}")
    abort(404)

  logger.info(
      f"Rendering public_results.html template for meeting: {meeting.id}")
  return render_template('public_results.html', meeting=meeting)


@meeting_blueprint.route('/public/meeting/<public_url>/data')
def public_meeting_data(public_url):
  logger.info(f"Accessing public meeting data for URL: {public_url}")
  meeting = Meeting.query.filter_by(public_url=public_url).first()

  if not meeting or not meeting.is_public:
    logger.warning(
        f"Public meeting not found or not public for URL: {public_url}")
    abort(404)

  meeting_data = {
      'name': meeting.name,
      'agents': meeting.agents,
      'questions': meeting.questions,
      'answers': meeting.answers
  }

  for agent in meeting_data['agents']:
    agent['photo_path'] = url_for('serve_public_image',
                                  filename=agent['photo_path'].split('/')[-1])

  logger.info(f"Returning public meeting data for meeting: {meeting.id}")
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
  response = make_response(redirect('/login'))
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
    logger.info("Accessing /start route")
    if request.method == 'POST':
        logger.info("Handling POST request")
        config = request.form.to_dict()
        config_path = 'start-config.json'
        logger.info(f"Saving configuration to {config_path}")
        with open(config_path, 'w') as file:
            json.dump(config, file)
        logger.info("Configuration saved successfully")

        if 'run_start' in request.form:
            logger.info("Executing start.main()")
            start.main()
            logger.info("Redirecting to start route")
            return redirect(url_for('start_blueprint.start_route'))

        if 'upload_files' in request.files:
            files = request.files.getlist('upload_files')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    logger.info(f"File {filename} uploaded successfully")
                    # Assuming extract_text.extract_and_save_text(file_path) exists and works as intended
                    extract_text.extract_and_save_text(file_path)
                    logger.info(f"Text extracted and saved for {filename}")

    config = start.load_configuration()
    new_agent_files = os.listdir(UPLOAD_FOLDER)
    new_agent_files_content = {}
    for file in new_agent_files:
        file_path = os.path.join(UPLOAD_FOLDER, file)
        with open(file_path, 'r') as file_content:
            new_agent_files_content[file] = file_content.read()
            logger.debug(f"Loaded content for {file}")

    page_view = PageView(page='/start_route')
    db.session.add(page_view)
    try:
        db.session.commit()
        logger.info("Page view for /start_route committed to DB")
    except Exception as e:
        logger.error(f"Failed to commit to DB: {e}", exc_info=True)
        db.session.rollback()

    return render_template('start.html', config=config, new_agent_files=new_agent_files, new_agent_files_content=new_agent_files_content)



@profile_blueprint.route('/create_new_agent', methods=['GET', 'POST'])
@login_required
def create_new_agent():
  logging.info("Handling request in create_new_agent route")
  if current_user.credits is None or current_user.credits <= 0:
    logging.warning("User does not have enough credits")
    flash(
        "You don't have enough credits. Please contact the admin to add more credits."
    )
    return redirect(url_for('home'))

  if request.method == 'POST':
    logging.info("Processing POST request for creating a new agent")
    agent_name = request.form['agent_name']
    agent_name = re.sub(r'[^a-zA-Z0-9\s]', '', agent_name).strip()
    jobtitle = request.form['jobtitle']
    agent_description = request.form['agent_description']

    logging.info(
        f"Creating new agent with name: {agent_name}, job title: {jobtitle}")
    new_agent = abe_gpt.generate_new_agent(agent_name, jobtitle,
                                           agent_description, current_user)
    logging.info(f"New agent created with ID: {new_agent.id}")

    return redirect(url_for('profile_blueprint.profile',
                            agent_id=new_agent.id))

  return render_template('new_agent.html')


@profile_blueprint.route('/edit_agent/<agent_id>', methods=['GET', 'POST'])
@login_required
def edit_agent(agent_id):
  logging.info(f"Editing agent with ID: {agent_id}")

  # Try to find the agent in the database
  agent = Agent.query.filter((Agent.user_id == current_user.id) & (
      (Agent.id == str(agent_id))
      | (Agent.id == agent_id.replace('_', '.')))).first()

  if not agent:
    logging.info("Agent not found in the database")
    # If agent not found in the database, check in agents_data
    agents_data = current_user.agents_data or []
    agent_data = get_agent_by_id(agents_data, agent_id)
    if agent_data:
      logging.info("Agent found in agents_data")
      logging.debug(f"Agent data: {agent_data}")
      # Create an Agent object from the agent_data dictionary
      agent = Agent(id=agent_data['id'],
                    user_id=current_user.id,
                    data=agent_data)
    else:
      logging.info("Agent not found in agents_data")
      # If agent not found in agents_data, check if it's a user or timeframe
      if current_user.id == int(agent_id):
        logging.info("Editing user")
        # If agent_id matches the current user's id, edit the user
        agent = current_user
      else:
        # Check if it's a timeframe
        timeframe = Timeframe.query.filter_by(id=agent_id,
                                              user_id=current_user.id).first()
        if timeframe:
          logging.info("Editing timeframe")
          agent = timeframe
        else:
          logging.error("Agent not found")
          flash('Agent not found.', 'error')
          return redirect(url_for('dashboard_blueprint.dashboard'))

  if request.method == 'POST':
    logging.info("Handling POST request")
    logging.debug(f"Request form data: {request.form}")
    # Update the agent data based on the form submission
    try:
      if isinstance(agent, Agent):
        logging.info("Updating Agent object")
        agent.data['persona'] = request.form.get('persona')
        agent.data['summary'] = request.form.get('summary')
        agent.data['keywords'] = request.form.get('keywords', '').split(',')
        agent.data['image_prompt'] = request.form.get('image_prompt')
        agent.data['relationships'] = get_relationships(agent.data)
        agent.voice = request.form.get('voice', 'echo')
        logging.debug(f"Updated Agent data: {str(agent.data)[:140]}")
        db.session.add(agent)  # Add the modified instance to the session
      elif isinstance(agent, User):
        logging.info("Updating User's agents_data")
        # Update the user's agents_data
        agents_data = current_user.agents_data or []
        for agent_data in agents_data:
          if agent_data['id'] == agent_id:
            agent_data['persona'] = request.form.get('persona')
            agent_data['summary'] = request.form.get('summary')
            agent_data['keywords'] = request.form.get('keywords',
                                                      '').split(',')
            agent_data['image_prompt'] = request.form.get('image_prompt')
            agent_data['relationships'] = get_relationships(agent_data)
            logging.debug(
                f"Updated User's agents_data: {str(agent_data)[:140]}")
            break
        current_user.agents_data = agents_data
        db.session.add(
            current_user)  # Add the modified user instance to the session
      elif isinstance(agent, Timeframe):
        logging.info("Updating Timeframe's agents_data")
        # Update the timeframe's agents_data
        agents_data = json.loads(agent.agents_data)
        for agent_data in agents_data:
          if agent_data['id'] == agent_id:
            agent_data['persona'] = request.form.get('persona')
            agent_data['summary'] = request.form.get('summary')
            agent_data['keywords'] = request.form.get('keywords',
                                                      '').split(',')
            agent_data['image_prompt'] = request.form.get('image_prompt')
            agent_data['relationships'] = get_relationships(agent_data)
            logging.debug(
                f"Updated Timeframe's agents_data: {str(agent_data)[:140]}")
            break
        agent.agents_data = json.dumps(agents_data)
        db.session.add(
            agent)  # Add the modified timeframe instance to the session
      else:
        logging.error("Unknown agent type")
        # Handle the case when the agent type is unknown
        flash('Unknown agent type. Changes not saved.', 'error')
        return redirect(url_for('profile_blueprint.profile',
                                agent_id=agent_id))

      db.session.commit()  # Commit the changes to the database
    except Exception as e:
      db.session.rollback()  # Rollback the transaction if an exception occurs
      logging.error(f"Error updating agent: {str(e)}")
      flash('An error occurred while updating the agent. Please try again.',
            'error')
      return redirect(
          url_for('profile_blueprint.edit_agent', agent_id=agent_id))

    logging.info("Changes committed to the database")
    logging.info(
        f"Redirecting to the profile page: {url_for('profile_blueprint.profile', agent_id=agent_id)}"
    )
    return redirect(url_for('profile_blueprint.profile', agent_id=agent_id))

  logging.info("Rendering edit_agent.html template")
  logging.debug(f"Agent data loaded into edit_agent.html: {agent.data}")
  voices = ['echo', 'alloy', 'fable', 'onyx', 'nova', 'shimmer']
  return render_template('edit_agent.html', agent=agent, voices=voices)


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

    agents_data = []
    user_agents = current_user.agents_data or []
    agent_class_agents = Agent.query.filter_by(user_id=current_user.id).all()
    timeframe_agents = []

    for timeframe in current_user.timeframes:
      timeframe_agents.extend(json.loads(timeframe.agents_data))

    processed_agent_ids = set()

    for agent in user_agents:
      if 'id' in agent and str(agent['id']) in selected_agent_ids and str(
          agent['id']) not in processed_agent_ids:
        agents_data.append(agent)
        processed_agent_ids.add(str(agent['id']))

    for agent in agent_class_agents:
      if hasattr(agent, 'id') and str(agent.id) in selected_agent_ids and str(
          agent.id) not in processed_agent_ids:
        agents_data.append(agent.data)
        processed_agent_ids.add(str(agent.id))

    for agent in timeframe_agents:
      if 'id' in agent and str(agent['id']) in selected_agent_ids and str(
          agent['id']) not in processed_agent_ids:
        agents_data.append(agent)
        processed_agent_ids.add(str(agent['id']))

    form_data = request.form.to_dict()
    form_data.pop('selected_agents', None)

    payload = {
        "agents_data": agents_data,
        "instructions": form_data,
        "timeframe_name": form_data["name"]
    }

    try:
      new_timeframe = abe_gpt.process_agents(payload, current_user)
      return redirect(
          url_for('dashboard_blueprint.dashboard',
                  timeframe_id=new_timeframe.id))
    except Exception as e:
      db.session.rollback()
      flash(f"An error occurred while processing agents: {str(e)}", "error")
      return redirect(url_for('home'))  # Redirect to home if it fails

  else:
    logger.info('Accessing new timeframe page')
    user_agents = current_user.agents_data or []
    agent_class_agents = Agent.query.filter_by(user_id=current_user.id).all()
    timeframes = current_user.timeframes

    return render_template('new_timeframe.html',
                           user_agents=user_agents,
                           agent_class_agents=agent_class_agents,
                           timeframes=timeframes)


# Route to generate an API key and automatically fetch all keys
@auth_blueprint.route('/users/generate_api_key', methods=['POST'])
@login_required
def generate_api_key():
  token = current_user.generate_api_key()
  if token:
    db.session.commit()
    flash('API Key generated successfully!', 'success')
  else:
    flash('Failed to generate API Key.', 'error')
  return redirect(url_for('auth_blueprint.user_profile'))


# Route to get all API keys for the current user
@auth_blueprint.route('/users/api_keys', methods=['GET'])
@login_required
def get_api_keys():
  api_keys = [api_key.key for api_key in current_user.api_keys]
  return jsonify(api_keys=api_keys)


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


@auth_blueprint.route('/get_agents', methods=['GET'])
@login_required
def get_agents():
  timeframe_id = request.args.get('timeframe_id')

  if timeframe_id:
    timeframe = Timeframe.query.get(timeframe_id)
    if not timeframe or timeframe.user_id != current_user.id:
      return jsonify({'error': 'Invalid timeframe'}), 400

    agents_data = json.loads(timeframe.agents_data)
    images_data = json.loads(timeframe.images_data)
  else:
    agents_data = current_user.agents_data or []
    images_data = current_user.images_data or {}

  agents = []
  for agent in agents_data:
    if 'id' in agent:
      photo_filename = agent['photo_path'].split('/')[-1]
      agent_data = {
          'id': agent['id'],
          'jobtitle': agent.get('jobtitle', ''),
          'image_data': images_data.get(photo_filename, '')
      }
      agents.append(agent_data)

  return jsonify({'agents': agents})
