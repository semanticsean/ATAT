# routes.py
import os, json, random, re, glob, shutil, bleach, logging, uuid
import abe_gpt
import start

from models import User, Survey
from extensions import db
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory, abort, jsonify, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from logging.handlers import RotatingFileHandler

from abe_gpt import generate_new_agent


logging.basicConfig(level=logging.INFO,
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
handlers=[
    logging.StreamHandler(),  # Console output
    RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)  # File output
])

logger = logging.getLogger(__name__)

AGENTS_JSON_PATH = os.path.join('agents', 'agents.json')
IMAGES_BASE_PATH = os.path.join('agents', 'pics')
AGENTS_BASE_PATH = 'agents'
SURVEYS_BASE_PATH = 'surveys'

start_blueprint = Blueprint('start_blueprint', __name__, template_folder='templates')

UPLOAD_FOLDER = 'agents/new_agent_files'
ALLOWED_EXTENSIONS = {'txt', 'doc', 'rtf', 'md', 'pdf'}


auth_blueprint = Blueprint('auth_blueprint', __name__, template_folder='templates')
survey_blueprint = Blueprint('survey_blueprint', __name__, template_folder='templates')

dashboard_blueprint = Blueprint('dashboard_blueprint', __name__, template_folder='templates')

profile_blueprint = Blueprint('profile_blueprint', __name__, template_folder='templates')

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
        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()

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

@auth_blueprint.route('/agents/copies/pics_<int:copy_num>/<path:filename>')
@login_required
def serve_image(copy_num, filename):
    user_dir = current_user.folder_path
    image_path = os.path.join(user_dir, 'agents', 'copies', f'pics_{copy_num}', filename)

    page_view = PageView(page='/serve_image')
    db.session.add(page_view)
    db.session.commit()

    if os.path.exists(image_path):
        return send_from_directory(os.path.join(user_dir, 'agents', 'copies', f'pics_{copy_num}'), filename)
    else:
        return abort(404)

@auth_blueprint.route('/new_agent_copy')
@login_required
def new_agent_copy():
    agents_dir = os.path.join(current_user.folder_path, 'agents')
    agents_file = os.path.join(agents_dir, 'agents.json')
    try:
        with open(agents_file, 'r') as f:
            agents_data = json.load(f)
        # Make sure agents_data is a list of agents
        if not isinstance(agents_data, list):
            raise ValueError("agents_data is not a list")
    except Exception as e:
        # Log the error or inform the user if necessary
        print(f"Error loading agents from JSON: {e}")
        agents_data = []  # Ensure agents_data is an empty list if there's an error

    return render_template('new_timeframe.html', agents=agents_data)

@auth_blueprint.route('/new_timeframe', methods=['POST'])
@login_required
def create_agent_copy():
    # Read the starting agents.json
    agents_dir = os.path.join(current_user.folder_path, 'agents')
    agents_file = os.path.join(agents_dir, 'agents.json')
    with open(agents_file, 'r') as f:
        agents_data = json.load(f)

    # Get the selected agent IDs from the form data directly using request.form.getlist
    selected_agent_ids = request.form.getlist('selected_agents')

    # Filter the agents_data to include only the selected agents
    selected_agents_data = [agent for agent in agents_data if str(agent['id']) in selected_agent_ids]

    # Extract other form data
    form_data = request.form.to_dict()
    form_data.pop('selected_agents', None)

    # Prepare the payload for the OpenAI API
    payload = {
        "agents_data": selected_agents_data,
        "instructions": form_data,  # This will include all other form data besides 'selected_agents'
    }

    # Call abe_gpt.py to process each selected agent record
    updated_agents_data = abe_gpt.process_agents(payload, current_user)

    # Save the updated agents data
    filename = form_data['filename']
    sanitized_filename = sanitize_filename(filename)
    copies_dir = os.path.join(agents_dir, 'copies')
    os.makedirs(copies_dir, exist_ok=True)
    new_agents_file_name = f"{sanitized_filename}.json"  # Filename of the new agent copy
    new_agents_file = os.path.join(copies_dir, new_agents_file_name)

    with open(new_agents_file, 'w') as f:
        json.dump(updated_agents_data, f)

    # Redirect to the dashboard view of the new JSON file
    return redirect(url_for('dashboard_blueprint.dashboard', agents_file=new_agents_file_name))


@survey_blueprint.route('/survey/create', methods=['GET', 'POST'])
@login_required
def create_survey(selected_file=None):
    logger = logging.getLogger(__name__)
    user_id = current_user.id  # Capture the current user's ID for logging
    user_dir = current_user.folder_path  # Use the current user's directory

    logger.info(f"User {user_id} started creating a survey. User directory: {user_dir}")

    agents_dir = os.path.join(user_dir, 'agents')
    copies_dir = os.path.join(agents_dir, 'copies')

    # Dynamically set the default agents.json path based on the user's directory
    default_agents_json_path = os.path.join(agents_dir, 'agents.json')
    selected_file = request.args.get('selected_file', default_agents_json_path)

    if request.method == 'POST':
        selected_file = request.form.get('selected_file', default_agents_json_path)
        survey_name = request.form.get('survey_name')
        logger.info(f"User {user_id} is creating survey '{survey_name}' with file '{selected_file}'.")
    
        # Adjusted to handle the case when selected_file is 'agents.json' or the default path
        if selected_file == 'agents.json' or selected_file == default_agents_json_path:
            file_path = default_agents_json_path
        else:
            file_path = os.path.join(copies_dir, os.path.basename(selected_file))
    
        try:
            with open(file_path, 'r') as f:
                agents = json.load(f)
            logger.info(f"Loaded agents from '{file_path}'. Total agents loaded: {len(agents)}")
        except Exception as e:
            logger.error(f"Failed to load agents for user {user_id} from '{file_path}': {e}")
            flash('There was an error loading the selected agent file. Please try again.')
            return redirect(url_for('survey_blueprint.create_survey'))
  


        selected_agents = request.form.getlist('selected_agents')
        logger.info(f"Selected agents: {selected_agents}")  # Log the selected agents

        survey_agents = [agent for agent in agents if str(agent['id']) in selected_agents]
        logger.info(f"Survey agents: {survey_agents}")  # Log the survey agents

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

        return redirect(url_for('survey_blueprint.survey_form', survey_id=new_survey.id, survey_agents=survey_agents))
    else:
        logger.info(f"User {user_id} accessed the survey creation page.")

    agent_files = [default_agents_json_path]
    agent_files.extend(glob.glob(os.path.join(copies_dir, '*.json')))
    agent_files = [os.path.basename(path) for path in agent_files]  # Use only the basename for display

    return render_template('meeting1.html', selected_file=selected_file, agent_files=agent_files, user_dir=current_user.folder_path)


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
def survey_form(survey_id, survey_agents=None):
    logger.info(f"Accessing survey form for survey ID: {survey_id} with method: {request.method}")

    try:
        survey = Survey.query.get_or_404(survey_id)
        if survey.user_id != current_user.id:
            logger.warning(f"Unauthorized access attempt by user ID: {current_user.id} for survey ID: {survey_id}")
            abort(403)

        if survey_agents is None:
            try:
                with open(survey.agents_file, 'r') as f:
                    agents = json.load(f)
                logger.info(f"Loaded agents from file: {survey.agents_file}")
            except Exception as e:
                logger.error(f"Error loading agents file: {survey.agents_file}, Error: {e}")
                raise
        else:
            agents = survey_agents

        if request.method == 'POST':
            questions = extract_questions_from_form(request.form)
            selected_agent_ids = request.form.getlist('selected_agents')
            llm_instructions = request.form.get('llm_instructions', '')
            request_type = request.form.get('request_type', 'iterative')
            logger.debug(f"Processing POST request with data: {locals()}")

            if selected_agent_ids:
                selected_agents = [agent for agent in agents if str(agent['id']) in selected_agent_ids]
            else:
                selected_agents = agents

            payload = {
                "agents_data": selected_agents,
                "questions": questions,
                "llm_instructions": llm_instructions,
                "request_type": request_type,
            }

            survey_responses = abe_gpt.conduct_survey(payload, current_user)
            logger.info(f"Survey conducted successfully for survey ID: {survey_id}")

            results_data = []
            for agent_data, response in zip(selected_agents, survey_responses):
                agent_data['responses'] = response['responses']  # Assuming 'responses' is structured accordingly
                agent_data['questions'] = questions
                results_data.append(agent_data)

            results_file = os.path.join(os.path.dirname(survey.agents_file), f"selected_agents_results{survey.result_count + 1}.json")
            with open(results_file, 'w') as f:
                json.dump(results_data, f)
            logger.info(f"Results written to file: {results_file}")

            survey.result_count += 1
            db.session.commit()

            survey_folder = os.path.basename(os.path.dirname(survey.agents_file))
            results_filename = f"selected_agents_results{survey.result_count}.json"

            return redirect(url_for('survey_blueprint.results', folder=survey_folder, filename=results_filename))
        else:
            return render_template('meeting2.html', survey=survey, agents=agents)
    except Exception as e:
        logger.error(f"An error occurred in survey_form function for survey ID: {survey_id}, Error: {e}")
        abort(500)  # Internal Server Error
  

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


@survey_blueprint.route('/survey/<folder>/<filename>/results', methods=['GET', 'POST'])
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

    if survey:
        # Set the filename and foldername attributes on the survey object
        survey.filename = filename
        survey.foldername = folder  # Here is the modification to add foldername
    else:
        # Handle the case when the survey object is not found
        flash('Survey not found.')
        return redirect(url_for('home'))

    if request.method == 'POST':
        is_public = request.form.get('is_public') == 'on'
        survey.is_public = is_public

        if is_public and not survey.public_url:
            # Generate a unique public URL if it doesn't exist
            survey.public_url = str(uuid.uuid4())
        elif not is_public:
            # Clear the public URL if the survey is made private
            survey.public_url = None

        db.session.commit()

    return render_template('results.html', results=survey_data, survey=survey)


@dashboard_blueprint.route('/dashboard')
@login_required
def dashboard():
    logging.info("Accessing dashboard page")
    agents = []  # Initialize agents as an empty list to handle exceptions
    agent_copies = []
    survey_results = []

    agents_dir = os.path.join(current_user.folder_path, 'agents')
    copies_dir = os.path.join(agents_dir, 'copies')
    agents_file = request.args.get('agents_file', 'agents.json')  # Default to agents.json

    logging.debug(f"Agents directory set to: {agents_dir}")
    logging.debug(f"Copies directory set to: {copies_dir}")
    logging.debug(f"Agents file selected: {agents_file}")

    # Store additional data about the agents' source
    agent_source = {"foldername": None, "filename": None}

    if os.path.isdir(copies_dir):
        agent_copies = [os.path.basename(f) for f in os.listdir(copies_dir) if f.endswith('.json')]
        logging.info(f"Found {len(agent_copies)} agent copies in the directory.")

    try:
        if agents_file == 'agents.json':  # Default file requested
            agents_file_path = os.path.join(agents_dir, agents_file)
            agent_source["filename"] = "agents.json"
        else:  # Any other file from the copies directory
            agents_file_path = os.path.join(copies_dir, agents_file.replace('agents/copies/', ''))
            agent_source["foldername"] = "copies"
            agent_source["filename"] = agents_file

        if os.path.exists(agents_file_path):
            with open(agents_file_path, 'r') as file:
                agents = json.load(file)
                logging.info(f"Successfully loaded agents from: {agents_file_path}")
        else:
            logging.warning(f"Agents file does not exist at: {agents_file_path}")
    except Exception as e:
        logging.error(f"Failed to load or parse agents JSON file: {e}", exc_info=True)
        flash(f"Failed to load or parse agents JSON file: {e}", "error")

    logging.info("Rendering dashboard page")

    page_view = PageView(page='/dashboard')
    db.session.add(page_view)
    db.session.commit()
    return render_template('dashboard.html', agents=agents, agent_copies=agent_copies, survey_results=survey_results, agent_source=agent_source)


@survey_blueprint.route('/survey/results/<int:survey_id>')
@login_required
def show_survey_results(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    page_view = PageView(page='/show_survey_results')
    db.session.add(page_view)
    db.session.commit()
    # Debugging: Print or log the survey object to ensure it has a filename attribute
    print("Survey filename:", survey.filename)  # Adjust according to your actual data structure
    if not hasattr(survey, 'filename'):
        # If the survey object doesn't have a filename attribute, handle the case appropriately
        print("Survey object does not have a filename attribute.")
        # Set a default filename or adjust your handling as needed
        survey.filename = 'default_filename'
    return render_template('results.html', survey=survey)



@profile_blueprint.route('/profile')
@login_required
def profile():
    agents_file = request.args.get('agents_file', 'agents.json')  # Default to 'agents.json'
    agent_id = request.args.get('agent_id')

    agents_dir = os.path.join(current_user.folder_path, 'agents')
    copies_dir = os.path.join(agents_dir, 'copies')
    page_view = PageView(page='/profile')
    db.session.add(page_view)
    db.session.commit()
  
    logger.info(f"Accessing profile with agents_file: {agents_file} and agent_id: {agent_id}")

    # Corrected the logic for determining the file path
    if agents_file == 'agents.json':
        agents_file_path = os.path.join(agents_dir, agents_file)  # For the main agents.json file
    else:
        # Correctly form the path for copies, avoiding duplication of 'agents/copies/'
        agents_file_path = os.path.join(copies_dir, os.path.basename(agents_file))  # Only use the basename for copies

    agent_copies = get_agent_copies(copies_dir)
    agents, _ = load_agents(agents_file_path)

    agent = get_agent_by_id(agents, agent_id)
    prev_agent_id, next_agent_id = get_prev_next_agent_ids(agents, agent)

    # Pass the correct file path or identifier as needed for AJAX or other calls
    agents_file_for_ui = 'agents.json' if agents_file == 'agents.json' else os.path.basename(agents_file)

    return render_template('profile.html', agent=agent, agents_file=agents_file_for_ui, agent_copies=agent_copies, prev_agent_id=prev_agent_id, next_agent_id=next_agent_id)



def get_agent_copies(copies_dir):
    if os.path.isdir(copies_dir):
        agent_copies = [f for f in os.listdir(copies_dir) if f.endswith('.json')]
        logger.info(f"Found {len(agent_copies)} agent copies in directory: {copies_dir}")
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
        logger.error(f"Failed to load or parse agents JSON file: {e}", exc_info=True)
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
        next_agent_id = agents[agent_index + 1]['id'] if agent_index < len(agents) - 1 else None
    else:
        prev_agent_id = None
        next_agent_id = None
    return prev_agent_id, next_agent_id

@profile_blueprint.route('/update_agent', methods=['POST'])
@login_required
def update_agent():
    logging.info('Starting agent update process')
    try:
        data = request.get_json()
        agents_file = data['agents_file']
        agent_id = data['agent_id']
        field = data['field']
        value = data['value']
        page_view = PageView(page='/update_agent')
        db.session.add(page_view)
        db.session.commit()

        agents_dir = os.path.join(current_user.folder_path, 'agents')
        copies_dir = os.path.join(agents_dir, 'copies')
        backups_dir = os.path.join(agents_dir, 'backups')

        if agents_file == 'agents/agents.json':
            agents_file_path = os.path.join(agents_dir, 'agents.json')
        else:
            agents_file_path = os.path.join(copies_dir, agents_file.split('/')[-1])

        # Load the agents data from the file
        with open(agents_file_path, 'r') as file:
            agents_data = json.load(file)

        # Find the agent to update
        agent = next((a for a in agents_data if a['id'] == agent_id), None)
        if agent:
            # Update the specified field
            agent[field] = value

            # Create a backup of the original file
            os.makedirs(backups_dir, exist_ok=True)
            backup_file = os.path.join(backups_dir, f"{os.path.basename(agents_file_path)}.bak")
            shutil.copy2(agents_file_path, backup_file)

            # Save the updated agents data back to the file
            with open(agents_file_path, 'w') as file:
                json.dump(agents_data, file)

            logging.info(f"Successfully updated agent {agent_id}")
        else:
            logging.warning(f"Agent {agent_id} not found. No updates made.")

        return jsonify(success=True)
    except Exception as e:
        logging.error(f"Error updating agent: {str(e)}")
        return jsonify(success=False, error=str(e))


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
            questions[question_id] = {
                'type': question_type,
                'text': value
            }
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

    page_view = PageView(page='/public_survey_results')
    db.session.add(page_view)
    db.session.commit()

    return render_template('public_results.html', survey=survey, public_url=public_url)

@survey_blueprint.route('/public_folder_name')
def public_folder_name():
    # Logic to determine survey and foldername...
    survey = get_survey()  # Hypothetical function to get a Survey object
    foldername = calculate_foldername(survey)  # Hypothetical function to determine foldername

    page_view = PageView(page='/public_folder_name')
    db.session.add(page_view)
    db.session.commit()

    return render_template('public_results.html', survey=survey, foldername=foldername)

@survey_blueprint.route('/public/survey/<public_url>/data')
def public_survey_data(public_url):
    survey = Survey.query.filter_by(public_url=public_url).first()

    if not survey or not survey.is_public:
        abort(404)

    # Load the survey data from the JSON file
    survey_file = os.path.join(survey.agents_file)
    with open(survey_file, 'r') as f:
        survey_data = json.load(f)

    # Update the photo_path for each agent
    for agent in survey_data:
        agent['photo_path'] = url_for('survey_blueprint.public_survey_image', public_url=public_url, filename=os.path.basename(agent['photo_path']))

    # Load the survey responses from the JSON file(s)
    results_files = glob.glob(os.path.join(os.path.dirname(survey.agents_file), 'selected_agents_results*.json'))
    responses_data = []
    for file in results_files:
        with open(file, 'r') as f:
            responses_data.extend(json.load(f))

    # Combine the survey data and responses data
    for agent in survey_data:
        agent_responses = next((r for r in responses_data if r['id'] == agent['id']), None)
        if agent_responses:
            agent['responses'] = agent_responses['responses']
            agent['questions'] = agent_responses['questions']

    return jsonify(survey_data)

@survey_blueprint.route('/public/survey/<public_url>/pics/<filename>')
def public_survey_image(public_url, filename):
    survey = Survey.query.filter_by(public_url=public_url).first()

    if not survey or not survey.is_public:
        abort(404)

    file_path = os.path.join(os.path.dirname(survey.agents_file), 'pics', filename)
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
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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

  
  
    return render_template('start.html', config=config, new_agent_files=new_agent_files, new_agent_files_content=new_agent_files_content)


@profile_blueprint.route('/create_new_agent', methods=['GET', 'POST'])
@login_required
def create_new_agent():
    if request.method == 'POST':
        agent_name = request.form['agent_name']
        # Process the agent_name to ensure it's safe for file paths
        agent_name = re.sub(r'[^a-zA-Z0-9\s]', '', agent_name).replace(' ', '_')
        jobtitle = request.form['jobtitle']
        agent_description = request.form['agent_description']

        # Corrected: Generate the new agent data and save it to the current user's agents.json
        new_agent_data = generate_new_agent(agent_name, jobtitle, agent_description, current_user)

        return redirect(url_for('profile_blueprint.profile', agents_file='agents.json', agent_id=new_agent_data['id']))

    # Assuming you're loading a template for the form from here
    return render_template('new_agent.html')
