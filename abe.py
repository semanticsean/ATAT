# abe.py

import logging
import glob
import os
import base64
import json
from flask import Flask, render_template, send_from_directory, abort, send_file, url_for, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from datetime import datetime
from extensions import db, login_manager
from models import db, User, Survey, Timeframe, Meeting, Agent, Image
import start
from routes import auth_blueprint, meeting_blueprint, dashboard_blueprint, profile_blueprint, start_blueprint
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

logger = logging.getLogger(__name__)

database_url = os.environ.get('DATABASE_URL')
if database_url:
    corrected_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = corrected_url
else:
    raise ValueError('Missing DATABASE_URL')


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_NAME'] = 'session_data'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['MAX_COOKIE_SIZE'] = 8192  # Adjust the size as needed

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
app.register_blueprint(meeting_blueprint)
app.register_blueprint(dashboard_blueprint)
app.register_blueprint(profile_blueprint)
app.register_blueprint(start_blueprint)

@app.template_filter('from_json')
def from_json(value):
    return json.loads(value)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_images():
    def custom_image_filter(photo_path, size='48x48'):
        # Extract the filename from the photo_path
        filename = os.path.basename(photo_path)

        # Generate the URL for the image using the appropriate route
        image_url = url_for('serve_image', filename=filename)

        return image_url

    return dict(custom_image_filter=custom_image_filter)

@app.context_processor
def inject_secrets():
    def get_secret(name):
        # Fetches and returns the secret by name from environment variables
        return os.environ.get(name)

    return dict(get_secret=get_secret)

@app.route('/')
def home():
    if current_user.is_authenticated:
        user_agents = current_user.agents_data or []
        agent_class_agents = Agent.query.filter_by(user_id=current_user.id).all()

        agents_content = []
        for agent in user_agents:
            agent_data = {
                'id': agent['id'],
                'jobtitle': agent.get('jobtitle', ''),
                'image_data': current_user.images_data.get(agent['photo_path'].split('/')[-1], '')
            }
            agents_content.append(agent_data)

        for agent in agent_class_agents:
            agent_data = {
                'id': agent.id,
                'jobtitle': agent.data.get('jobtitle', ''),
                'image_data': current_user.images_data.get(agent.data['photo_path'].split('/')[-1], '')
            }
            agents_content.append(agent_data)

        agents_content = json.dumps(agents_content) if agents_content else None
        meeting_results = []
        for meeting in current_user.meetings:
            if meeting.agents and meeting.questions and meeting.answers:
                for agent_data in meeting.agents:
                    meeting_results.append((meeting.name, agent_data['id']))
    else:
        agents_content = None
        meeting_results = []

    timeframes = current_user.timeframes if current_user.is_authenticated else []
    return render_template('index.html', agents_content=agents_content, meeting_results=meeting_results, timeframes=timeframes)

@app.route('/images/<filename>')
def serve_image(filename):
    if current_user.is_authenticated:
        user_id = current_user.id
        user = User.query.get(user_id)

        # Check if the image is in the user's images_data
        if user.images_data and filename in user.images_data:
            image_data = user.images_data.get(filename)
            return Response(base64.b64decode(image_data), mimetype='image/png')

        # Check if the image is in any of the user's timeframes
        for timeframe in user.timeframes:
            timeframe_images_data = json.loads(timeframe.images_data)
            if filename in timeframe_images_data:
                image_data = timeframe_images_data.get(filename)
                return Response(base64.b64decode(image_data), mimetype='image/png')
    else:
        # Check if the image belongs to a public meeting
        public_meeting = Meeting.query.filter_by(is_public=True).join(Meeting.agents).filter(Meeting.agents.any(photo_path=filename)).first()
        if public_meeting:
            image_data = public_meeting.images_data.get(filename)
            if image_data:
                return Response(base64.b64decode(image_data), mimetype='image/png')

    abort(404)

@app.route('/public/<path:filename>')
def serve_public_image(filename):
    public_folder = 'public'
    file_path = os.path.join(public_folder, filename)

    if os.path.exists(file_path):
        return send_from_directory(public_folder, filename)
    else:
        abort(404)

def custom_img_filter(photo_path, size='48x48'):
  # Extract the filename from the photo_path
  filename = os.path.basename(photo_path)

  # Generate the URL for the image using the appropriate route
  image_url = url_for('serve_image', filename=filename)

  # Return the HTML img tag with the image URL and size
  return f'<img src="{image_url}" alt="{filename}" width="{size.split("x")[0]}" height="{size.split("x")[1]}">'


if __name__ == '__main__':
    app.run(debug=True)