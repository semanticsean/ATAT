#abe.py
import logging, glob, os, json
from flask import Flask, render_template, send_from_directory, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from datetime import datetime
from extensions import db, login_manager
from models import User, Survey
import start
from routes import auth_blueprint, survey_blueprint, dashboard_blueprint, profile_blueprint, start_blueprint
from werkzeug.utils import secure_filename


def configure_logging():
  if not os.path.exists('logs'):
    os.makedirs('logs')
  log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log')
  log_file_path = os.path.join('logs', log_file_name)
  file_handler = logging.FileHandler(log_file_path)
  file_handler.setLevel(logging.DEBUG)
  formatter = logging.Formatter(
      '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  file_handler.setFormatter(formatter)

  logging.getLogger().addHandler(file_handler)
  logging.getLogger().setLevel(logging.DEBUG)


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY', 'default_secret_key')
configure_logging()

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
  app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace(
      "postgres://", "postgresql://", 1)
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
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)

app.register_blueprint(auth_blueprint)
app.register_blueprint(survey_blueprint)
app.register_blueprint(dashboard_blueprint)
app.register_blueprint(profile_blueprint)
app.register_blueprint(start_blueprint)


@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))


@app.route('/')
def home():
  if current_user.is_authenticated:
    agents_content = json.dumps(
        current_user.agents_data) if current_user.agents_data else None
    survey_results = []
    for survey in current_user.surveys:
      if survey.survey_data:
        for agent_data in survey.survey_data:
          survey_results.append((survey.name, agent_data['id']))
  else:
    agents_content = None
    
    survey_results = []

  return render_template('index.html',
                         agents_content=agents_content,x2
                         survey_results=survey_results)


@app.route('/agents/pics/<filename>')
@login_required
def serve_agent_image(filename):
  # Ensure the filename is safe and ends with .png
  if ".." in filename or filename.startswith(
      "/") or not filename.endswith(".png"):
    return abort(404)

  user_dir = current_user.folder_path
  image_path = os.path.join(user_dir, 'agents', 'pics', filename)

  if os.path.exists(image_path):
    return send_from_directory(os.path.join(user_dir, 'agents', 'pics'),
                               filename)
  else:
    return abort(404)


if __name__ == '__main__':
  app.run(debug=True)
