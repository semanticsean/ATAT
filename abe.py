#abe.py 
import logging, glob, os
from flask import Flask, render_template, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from datetime import datetime
from extensions import db, login_manager
from models import User, Survey
from routes import auth_blueprint, survey_blueprint, dashboard_blueprint, profile_blueprint
from werkzeug.utils import secure_filename

def configure_logging():
  if not os.path.exists('logs'):
      os.makedirs('logs')
  log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log')
  log_file_path = os.path.join('logs', log_file_name)
  file_handler = logging.FileHandler(log_file_path)
  file_handler.setLevel(logging.DEBUG)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  file_handler.setFormatter(formatter)

  logging.getLogger().addHandler(file_handler)
  logging.getLogger().setLevel(logging.DEBUG)
  

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY', 'default_secret_key')


configure_logging() 


database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("postgres://", "postgresql://", 1)
else:
    raise ValueError('Invalid or missing DATABASE_URL')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth_blueprint.login'

migrate = Migrate(app, db)

logs_directory = 'logs'
if not os.path.exists(logs_directory):
    os.makedirs(logs_directory)
log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log')
log_file_path = os.path.join(logs_directory, log_file_name)
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)


app.register_blueprint(auth_blueprint)
app.register_blueprint(survey_blueprint)
app.register_blueprint(dashboard_blueprint)
app.register_blueprint(profile_blueprint)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/user_files/<filename>')
@login_required
def user_file(filename):
    user_dir = current_user.folder_path
    copies_dir = os.path.join(user_dir, 'agents', 'copies')
    safe_filename = secure_filename(filename)  # Ensure the filename is safe
    if not os.path.exists(os.path.join(copies_dir, safe_filename)):
        abort(404)
    return send_from_directory(copies_dir, safe_filename)

@app.route('/user_content/<path:filename>')
def custom_static(filename):
    return send_from_directory('user_content', filename)

@app.route('/')
def home():
    agents_content = None
    agent_copies = []
    survey_results = []
    survey_files = []
    survey_folders = []

    if current_user.is_authenticated:
        user_dir = current_user.folder_path

        # Agents.json handling
        agents_file_path = os.path.join(user_dir, 'agents', 'agents.json')
        if not os.path.exists(agents_file_path):
            src_agents_file = os.path.join(os.getcwd(), 'agents', 'agents.json')
            os.makedirs(os.path.dirname(agents_file_path), exist_ok=True)
            if os.path.exists(src_agents_file):
                shutil.copy(src_agents_file, agents_file_path)
        if os.path.exists(agents_file_path):
            with open(agents_file_path, 'r') as file:
                agents_content = file.read()

        # Agent copies handling
        copies_dir = os.path.join(user_dir, 'agents', 'copies')
        if os.path.isdir(copies_dir):
            agent_copies = [os.path.basename(f) for f in glob.glob(os.path.join(copies_dir, '*.json'))]

        
        # Survey results handling
        surveys_dir = os.path.join(user_dir, 'surveys')
        survey_results = []
        if os.path.isdir(surveys_dir):
            for folder_name in os.listdir(surveys_dir):
                folder_path = os.path.join(surveys_dir, folder_name)
                if os.path.isdir(folder_path):
                    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
                    for file_name in json_files:
                        survey_results.append((folder_name, file_name))
      
    return render_template('index.html', agents_content=agents_content, agent_copies=agent_copies,
                           survey_results=survey_results)


@app.route('/agents/pics/<filename>')
@login_required
def serve_agent_image(filename):
    # Ensure the filename is safe and ends with .png
    if ".." in filename or filename.startswith("/") or not filename.endswith(".png"):
        return abort(404)

    user_dir = current_user.folder_path
    image_path = os.path.join(user_dir, 'agents', 'pics', filename)

    if os.path.exists(image_path):
        return send_from_directory(os.path.join(user_dir, 'agents', 'pics'), filename)
    else:
        return abort(404)



if __name__ == '__main__':
    app.run(debug=True)