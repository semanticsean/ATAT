# routes.py
import os, json, random, re, glob, shutil, bleach, logging
from models import User, Survey
from extensions import db
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory, abort, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from survey_handler import generate_random_answers, process_survey_responses, extract_questions_from_form
from logging.handlers import RotatingFileHandler


logging.basicConfig(level=logging.INFO,
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
handlers=[
    logging.StreamHandler(),  # Console output
    RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)  # File output
])

AGENTS_JSON_PATH = os.path.join('agents', 'agents.json')
IMAGES_BASE_PATH = os.path.join('agents', 'pics')


auth_blueprint = Blueprint('auth_blueprint', __name__, template_folder='templates')
survey_blueprint = Blueprint('survey_blueprint', __name__, template_folder='templates')

dashboard_blueprint = Blueprint('dashboard_blueprint', __name__, template_folder='templates')


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Invalid username or password')
            return redirect(url_for('auth_blueprint.login'))  
        login_user(user)
        return redirect(url_for('home'))  
    return render_template('login.html')

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('auth_blueprint.register'))
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        new_user.create_user_folder()
        db.session.add(new_user)
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
        return redirect(url_for('auth_blueprint.update_profile'))

    return render_template('user.html')

@auth_blueprint.route('/new_agent_copy')
@login_required
def new_agent_copy():
    return render_template('new_agents_copy.html')

def sanitize_filename(filename):
  # Strip HTML tags
  clean_filename = bleach.clean(filename, tags=[], strip=True)
  # Remove spaces and special characters
  clean_filename = re.sub(r'\s+|[^a-zA-Z0-9]', '_', clean_filename)
  # Remove leading or trailing underscores
  clean_filename = clean_filename.strip('_')
  return clean_filename

@auth_blueprint.route('/agents/copies/pics_<int:copy_num>/<path:filename>')
@login_required
def serve_image(copy_num, filename):
    user_dir = current_user.folder_path
    image_path = os.path.join(user_dir, 'agents', 'copies', f'pics_{copy_num}', filename)

    if os.path.exists(image_path):
        return send_from_directory(os.path.join(user_dir, 'agents', 'copies', f'pics_{copy_num}'), filename)
    else:
        return abort(404)


@auth_blueprint.route('/create_agent_copy', methods=['POST'])
@login_required
def create_agent_copy():
    filename = request.form['filename']
    sanitized_filename = sanitize_filename(filename)
    user_dir = current_user.folder_path
    agents_dir = os.path.join(user_dir, 'agents')
    copies_dir = os.path.join(agents_dir, 'copies')
    os.makedirs(copies_dir, exist_ok=True)

    # Check if agents.json exists in the user's agent directory
    user_agents_file = os.path.join(agents_dir, 'agents.json')
    if not os.path.exists(user_agents_file):
        # Copy agents.json from the app's agents directory to the user's agent directory
        src_agents_file = os.path.join(os.getcwd(), 'agents', 'agents.json')
        shutil.copy(src_agents_file, user_agents_file)

    # Find the next available filename with a trailing digit
    existing_files = glob.glob(os.path.join(copies_dir, f"{filename}*.json"))
    highest_num = 0
    for file in existing_files:
        match = re.search(f"{filename}(\\d*)\\.json$", file)
        if match:
            num = int(match.group(1) or 0)
            highest_num = max(highest_num, num)

    new_filename = f"{filename}{highest_num + 1}.json"
    new_agents_file = os.path.join(copies_dir, new_filename)
    shutil.copy(os.path.join(agents_dir, 'agents.json'), new_agents_file)

    # Create a new pics folder for the new agents file
    new_pics_dir = os.path.join(copies_dir, f"pics_{highest_num + 1}")
    os.makedirs(new_pics_dir, exist_ok=True)

    # Update the photo_path in the new agents file
    with open(new_agents_file, 'r') as f:
        agents_data = json.load(f)

    for agent in agents_data:
        old_photo_path = agent['photo_path']
    
        # Check if the old_photo_path is already in the new format
        if old_photo_path.startswith('agents/copies/'):
            # Extract the filename from the old_photo_path
            photo_filename = os.path.basename(old_photo_path)
        else:
            # Assume the old_photo_path is in the original format
            photo_filename = os.path.basename(old_photo_path)
            # Copy the photo from the original 'pics' directory to the new location
            original_photo_path = os.path.join(agents_dir, 'pics', photo_filename)
            shutil.copy(original_photo_path, os.path.join(new_pics_dir, photo_filename))
    
        # Update the agent's photo_path with the new relative path
        new_photo_path_relative = os.path.join('agents', 'copies', f"pics_{highest_num + 1}", photo_filename)
        agent['photo_path'] = new_photo_path_relative

    with open(new_agents_file, 'w') as f:
        json.dump(agents_data, f)

    return redirect('/')


@survey_blueprint.route('/survey/create', methods=['GET', 'POST'])
@login_required
def create_survey():
    logger = logging.getLogger(__name__)
    user_id = current_user.id  # Capture the current user's ID for logging
    user_dir = current_user.folder_path

    logger.info(f"User {user_id} started creating a survey. User directory: {user_dir}")

    agents_dir = os.path.join(user_dir, 'agents')
    copies_dir = os.path.join(agents_dir, 'copies')

    if request.method == 'POST':
        selected_file = request.form.get('selected_file')
        survey_name = request.form.get('survey_name')
        logger.info(f"User {user_id} is creating survey '{survey_name}' with file '{selected_file}'.")

        file_path = os.path.join(copies_dir if selected_file != 'agents.json' else agents_dir, selected_file)

        try:
            with open(file_path, 'r') as f:
                agents = json.load(f)
            logger.info(f"Loaded agents from '{file_path}'. Total agents loaded: {len(agents)}")
        except Exception as e:
            logger.error(f"Failed to load agents for user {user_id} from '{file_path}': {e}")
            flash('There was an error loading the selected agent file. Please try again.')
            return redirect(url_for('survey_blueprint.create_survey'))

        selected_agents = request.form.getlist('selected_agents')
        survey_agents = [agent for agent in agents if str(agent['id']) in selected_agents]
        logger.info(f"Selected {len(survey_agents)} agents for survey '{survey_name}'.")

        # Create survey folder and selected_agents.json
        survey_folder = os.path.join(user_dir, 'surveys', f"{survey_name}_{random.randint(100000, 999999)}")
        os.makedirs(survey_folder, exist_ok=True)
        selected_agents_file = os.path.join(survey_folder, 'selected_agents.json')
        with open(selected_agents_file, 'w') as f:
            json.dump(survey_agents, f)
        logger.info(f"Created survey folder '{survey_folder}' and saved selected agents.")

        # Copy photos to a new subfolder within the survey folder
        photos_subfolder = os.path.join(survey_folder, 'pics')
        os.makedirs(photos_subfolder, exist_ok=True)
        logger.info(f"Created photos subfolder at '{photos_subfolder}'.")

        for agent in survey_agents:
            try:
                old_photo_path = agent['photo_path']
                photo_filename = os.path.basename(old_photo_path)
                new_photo_path = os.path.join('surveys', os.path.basename(survey_folder), 'pics', photo_filename)
                shutil.copy(os.path.join(user_dir, old_photo_path), os.path.join(photos_subfolder, photo_filename))
                survey_id = os.path.basename(survey_folder)
                agent['photo_path'] = url_for('survey_blueprint.serve_survey_image', survey_id=survey_id, filename=photo_filename)
  
                logger.info(f"Copied photo '{photo_filename}' for agent '{agent['id']}' to '{new_photo_path}'.")
            except Exception as e:
                logger.error(f"Failed to copy photo for agent '{agent['id']}': {e}")

        # Save the updated paths back to selected_agents.json
        with open(selected_agents_file, 'w') as f:
            json.dump(survey_agents, f)
        logger.info("Updated agent photo paths in 'selected_agents.json'.")

        new_survey = Survey(name=survey_name, user_id=current_user.id, agents_file=selected_agents_file)
        db.session.add(new_survey)
        db.session.commit()
        logger.info(f"Successfully created survey '{survey_name}' with ID {new_survey.id} for user {user_id}.")

        return redirect(url_for('survey_blueprint.survey_form', survey_id=new_survey.id))
    else:
        logger.info(f"User {user_id} accessed the survey creation page.")

    agent_files = ['agents.json'] + [f for f in os.listdir(copies_dir) if os.path.isfile(os.path.join(copies_dir, f))]
    return render_template('survey1.html', agent_files=agent_files)

  
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

    with open(survey.agents_file, 'r') as f:
        agents = json.load(f)

    if request.method == 'POST':
        questions = extract_questions_from_form(request.form)
        selected_agent_ids = request.form.getlist('selected_agents')
        
        if selected_agent_ids:
            selected_agents = [agent for agent in agents if str(agent['id']) in selected_agent_ids]
        else:
            selected_agents = agents

        responses = process_survey_responses(questions)

        results_data = []
        for i, agent in enumerate(selected_agents):
            agent_data = agent.copy()
            agent_data['responses'] = responses[i % len(responses)]
            agent_data['questions'] = questions
            results_data.append(agent_data)

        results_file = os.path.join(os.path.dirname(survey.agents_file), f"selected_agents_results{survey.result_count + 1}.json")
        with open(results_file, 'w') as f:
            json.dump(results_data, f)

        survey.result_count += 1
        db.session.commit()

        survey_folder = os.path.basename(os.path.dirname(survey.agents_file))
        results_filename = f"selected_agents_results{survey.result_count}.json"

        return redirect(url_for('survey_blueprint.results', folder=survey_folder, filename=results_filename))

    return render_template('survey2.html', survey=survey, agents=agents)

@survey_blueprint.route('/survey/<int:survey_id>/get_results')
@login_required
def get_results(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if survey.user_id != current_user.id:
        abort(403)

    results_files = glob.glob(os.path.join(os.path.dirname(survey.agents_file), 'selected_agents_results*.json'))
    results = []
    for file in results_files:
        with open(file, 'r') as f:
            results.extend(json.load(f))  # Extend the results array with data from each file

    return jsonify(results)


@survey_blueprint.route('/survey/<folder>/<filename>/results')
@login_required
def results(folder, filename):
    user_dir = current_user.folder_path
    survey_file = os.path.join(user_dir, 'surveys', folder, filename)

    if not os.path.exists(survey_file):
        flash('Survey file not found.')
        return redirect(url_for('home'))

    try:
        with open(survey_file, 'r') as f:
            survey_data = json.load(f)
    except (json.JSONDecodeError, KeyError):
        flash('Invalid survey file format.')
        return redirect(url_for('home'))

    # Retrieve the survey object based on the folder and filename
    survey_folder = os.path.join(user_dir, 'surveys', folder)
    survey = Survey.query.filter_by(agents_file=os.path.join(survey_folder, 'selected_agents.json')).first()

    return render_template('results.html', results=survey_data, survey=survey)

@dashboard_blueprint.route('/dashboard')
@login_required
def dashboard():
    agents = []  # Initialize agents as an empty list to handle exceptions
    try:
        # Use AGENTS_JSON_PATH to maintain compatibility
        with open(AGENTS_JSON_PATH, 'r') as file:
            agents = json.load(file)
        # Process each agent for additional data
        for agent in agents:
            # Assuming get_image_path is a function that updates the agent's photo path
            agent['photo_path'] = get_image_path(agent)
            # Handle keywords, if present
            if 'keywords' in agent and isinstance(agent['keywords'], list):
                agent['keywords'] = random.sample(agent['keywords'], min(len(agent['keywords']), 3))
            else:
                agent['keywords'] = []
    except Exception as e:
        print(f"Failed to load or parse JSON file: {e}")

    return render_template('dashboard.html', agents=agents)
  

@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))