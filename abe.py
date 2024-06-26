# abe.py
import logging
import glob
import os
import base64
import json
import requests
import aiohttp

from flask import Flask, render_template, send_from_directory, abort, send_file, url_for, Response, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from datetime import datetime
from extensions import db, login_manager
from models import db, User, Survey, Timeframe, Meeting, Agent, Image, Conversation
import start
from routes import auth_blueprint, meeting_blueprint, dashboard_blueprint, profile_blueprint, start_blueprint, talker_blueprint, timeframes_blueprint, doc2api_blueprint
from werkzeug.utils import secure_filename
from sqlalchemy import cast, String
from talker import talker_blueprint

from fastapi import Header, Depends
from abe_api_internal import get_schema, get_agents, get_meetings, get_timeframes, get_conversations, get_surveys, APIKeyHeader, verify_api_key, get_db_session

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView, fields



# ADMIN MODEL VIEWS



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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY', 'default_secret_key')

configure_logging()

logger = logging.getLogger(__name__)


database_url = os.environ.get('DATABASE_URL')
if database_url:
    corrected_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = corrected_url
else:
    raise ValueError('Missing DATABASE_URL')



class UserModelView(ModelView):
    can_create = False
    can_edit = True
    can_delete = False
    column_list = ['id', 'username', 'agents_data', 'email', 'credits']
    column_searchable_list = ['username', 'email']

class AgentModelView(ModelView):
    can_create = False
    can_edit = True
    can_delete = False
    column_list = ['id', 'user_id', 'data', 'agent_type', 'voice']
    column_searchable_list = ['id', 'user_id']

class TimeframeModelView(ModelView):
    can_create = False
    can_edit = True
    can_delete = False
    column_list = ['id', 'name', 'user_id', 'agents_data', 'images_data', 'thumbnail_images_data', 'summary']
    column_searchable_list = ['id', 'name', 'user_id', 'agents_data', 'images_data', 'thumbnail_images_data',]

class MeetingModelView(ModelView):
    can_create = False
    can_edit = True
    can_delete = False
    column_list = ['id', 'name', 'user_id', 'agents', 'questions', 'answers', 'is_public', 'public_url', 'original_name', 'summary']
    column_searchable_list = ['name', 'user_id']

class ConversationModelView(ModelView):
    can_create = False
    can_edit = True
    can_delete = False
    column_list = ['id', 'user_id', 'name', 'agents', 'messages', 'timestamp', 'url']
    column_searchable_list = ['name', 'user_id']

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
app.register_blueprint(timeframes_blueprint)
app.register_blueprint(talker_blueprint)



# Create an instance of Admin
admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')
admin.add_view(UserModelView(User, db.session))
admin.add_view(AgentModelView(Agent, db.session))
admin.add_view(TimeframeModelView(Timeframe, db.session))
admin.add_view(MeetingModelView(Meeting, db.session))
admin.add_view(ConversationModelView(Conversation, db.session))


# Register Flask routes with appropriate wrappers

@app.route('/api/schema', methods=['GET'])
def api_schema():
    authorization = request.headers.get('Authorization')
    api_key_header = APIKeyHeader(Authorization=authorization)
    db_session = next(get_db_session())
    user = verify_api_key(api_key_header, db_session)
    return jsonify(get_schema(user, db_session))

@app.route('/api/agents', methods=['GET'])
def api_agents():
    authorization = request.headers.get('Authorization')
    api_key_header = APIKeyHeader(Authorization=authorization)
    db_session = next(get_db_session())
    user = verify_api_key(api_key_header, db_session)
    return jsonify(get_agents(user, db_session))

@app.route('/api/meetings', methods=['GET'])
def api_meetings():
    authorization = request.headers.get('Authorization')
    api_key_header = APIKeyHeader(Authorization=authorization)
    db_session = next(get_db_session())
    user = verify_api_key(api_key_header, db_session)
    return jsonify(get_meetings(user, db_session))

@app.route('/api/timeframes', methods=['GET'])
def api_timeframes():
    authorization = request.headers.get('Authorization')
    api_key_header = APIKeyHeader(Authorization=authorization)
    db_session = next(get_db_session())
    user = verify_api_key(api_key_header, db_session)
    return jsonify(get_timeframes(user, db_session))

@app.route('/api/conversations', methods=['GET'])
def api_conversations():
    authorization = request.headers.get('Authorization')
    api_key_header = APIKeyHeader(Authorization=authorization)
    db_session = next(get_db_session())
    user = verify_api_key(api_key_header, db_session)
    return jsonify(get_conversations(user, db_session))

@app.route('/api/surveys', methods=['GET'])
def api_surveys(authorization: str = Header(None)):
    authorization = request.headers.get('Authorization')
    api_key_header = APIKeyHeader(Authorization=authorization)
    db_session = next(get_db_session())
    user = verify_api_key(api_key_header)
    return jsonify(get_surveys(user, db_session))


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
        agent_class_agents = Agent.query.filter_by(
            user_id=current_user.id).all()

        agents_content = []
        for agent in user_agents:
            agent_data = {
                'id':
                agent['id'],
                'jobtitle':
                agent.get('jobtitle', ''),
                'image_data':
                current_user.images_data.get(
                    agent['photo_path'].split('/')[-1], '')
            }
            agents_content.append(agent_data)

        for agent in agent_class_agents:
            agent_data = {
                'id':
                agent.id,
                'jobtitle':
                agent.data.get('jobtitle', ''),
                'image_data':
                current_user.images_data.get(
                    agent.data['photo_path'].split('/')[-1], '')
            }
            agents_content.append(agent_data)

        agents_content = json.dumps(agents_content) if agents_content else None

        meeting_results = []
        for meeting in current_user.meetings:
            if meeting.agents and meeting.questions and meeting.answers:
                for agent_data in meeting.agents:
                    if isinstance(agent_data, dict) and 'id' in agent_data:
                        meeting_results.append(
                            (meeting.name, agent_data['id']))
    else:
        agents_content = None
        meeting_results = []

    timeframes = current_user.timeframes if current_user.is_authenticated else []

    # Load the summary image and thumbnail data for each timeframe
    for timeframe in timeframes:
        timeframe.summary_image_data = timeframe.summary_image_data if timeframe.summary_image_data else None
        timeframe.summary_thumbnail_image_data = timeframe.summary_thumbnail_image_data if timeframe.summary_thumbnail_image_data else None

    return render_template('index.html',
                           agents_content=agents_content,
                           meeting_results=meeting_results,
                           timeframes=timeframes)


@app.route('/images/<filename>')
def serve_image(filename):
    if current_user.is_authenticated:
        user_id = current_user.id
        user = User.query.get(user_id)

        # Check if the image is in the user's images_data
        if user.images_data and filename in user.images_data:
            print("Image found in user's images_data"
                  )  # Print if the image is found
            image_data = user.images_data.get(filename)
            return Response(base64.b64decode(image_data), mimetype='image/png')

        # Check if the image is in any of the user's timeframes
        for timeframe in user.timeframes:
            timeframe_images_data = json.loads(timeframe.images_data)
            if filename in timeframe_images_data:
                image_data = timeframe_images_data.get(filename)
                return Response(base64.b64decode(image_data),
                                mimetype='image/png')

        # Check if the image is in any of the user's agents
        agent = Agent.query.filter(
            Agent.user_id == user_id,
            Agent.data.cast(db.Text).contains(
                f'"photo_path": "/images/{filename}"')).first()
        if agent:
            image_data = agent.data.get('image_data',
                                        {}).get(f"/images/{filename}")
            if image_data:
                return Response(base64.b64decode(image_data),
                                mimetype='image/png')

        # Check if the image belongs to a timeframe agent
        timeframe_agent = db.session.query(Timeframe).filter(
            Timeframe.user_id == user_id,
            Timeframe.agents_data.cast(db.Text).contains(
                f'"photo_path": "/images/{filename}"')).first()
        if timeframe_agent:
            timeframe_images_data = json.loads(timeframe_agent.images_data)
            image_data = timeframe_images_data.get(filename)
            if image_data:
                return Response(base64.b64decode(image_data),
                                mimetype='image/png')

        # Check if the image belongs to a public meeting
        public_meeting = Meeting.query.filter_by(is_public=True).filter(
            Meeting.agents.cast(
                db.Text).contains(f'"/images/{filename}"')).first()
        if public_meeting:
            image_data = public_meeting.images_data.get(filename)
            if image_data:
                return Response(base64.b64decode(image_data),
                                mimetype='image/png')

        # Check if the image belongs to a meeting summary
        meeting = Meeting.query.filter(
            Meeting.image_data.isnot(None)).filter_by(
                image_data=filename).first()
        if meeting:
            image_data = meeting.image_data
            if image_data:
                return Response(base64.b64decode(image_data),
                                mimetype='image/png')

    print("Image not found")
    abort(404)


@app.errorhandler(404)
def page_not_found(e):
    # Render the template for 404.html
    return render_template('404.html')


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
    app.run(debug=False)