# abe_api_external.py

from flask import Flask, jsonify, request, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db, User, Meeting, Timeframe, Agent, APIKey
import logging
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configure logging
logs_directory = 'logs'
if not os.path.exists(logs_directory):
    os.makedirs(logs_directory)
log_file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S_api.log')
log_file_path = os.path.join(logs_directory, log_file_name)
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

def verify_api_key(api_key):
    api_key_obj = APIKey.query.filter_by(key=api_key).first()
    if api_key_obj and api_key_obj.owner.credits > 0:
        api_key_obj.owner.credits -= 1
        db.session.commit()
        return api_key_obj.owner
    return None

Sure! Here's the updated abe_api_external.py with a new route that provides a lookup of possible IDs for agents, timeframes, and meetings, along with a snippet of a longer component from each type:
pythonCopy code# abe_api_external.py



@app.route('/lookup')
@limiter.limit("10 per minute")
def lookup():
    api_key = request.headers.get('Authorization')
    item_type = request.args.get('type')
    snippet_length = int(request.args.get('snippet_length', 100))

    if not api_key or not item_type:
        abort(400)

    user = verify_api_key(api_key)
    if not user:
        abort(401)

    if item_type == 'agents':
        agents = Agent.query.filter_by(user_id=user.id).all()
        data = []
        for agent in agents:
            item = {
                'id': agent.id,
                'persona_snippet': agent.data.get('persona', '')[:snippet_length]
            }
            data.append(item)
    elif item_type == 'timeframes':
        timeframes = Timeframe.query.filter_by(user_id=user.id).all()
        data = []
        for timeframe in timeframes:
            item = {
                'id': timeframe.id,
                'summary_snippet': timeframe.summary[:snippet_length] if timeframe.summary else ''
            }
            data.append(item)
    elif item_type == 'meetings':
        meetings = Meeting.query.filter_by(user_id=user.id).all()
        data = []
        for meeting in meetings:
            item = {
                'id': meeting.id,
                'summary_snippet': meeting.summary[:snippet_length] if meeting.summary else ''
            }
            data.append(item)
    else:
        abort(400)

    app.logger.info(f"User {user.id} requested lookup for {item_type}")
    return jsonify(data)

@app.route('/agents')
@limiter.limit("10 per minute")
def get_agent():
    api_key = request.headers.get('Authorization')
    agent_id = request.args.get('id')
    include_images = request.args.get('include_images', 'false').lower() == 'true'

    if not api_key or not agent_id:
        abort(400)

    user = verify_api_key(api_key)
    if not user:
        abort(401)

    agent = Agent.query.filter_by(id=agent_id, user_id=user.id).first()
    if not agent:
        abort(404)

    agent_data = agent.data
    if not include_images:
        agent_data.pop('image_data', None)

    app.logger.info(f"User {user.id} requested agent {agent_id}")
    return jsonify(agent_data)
    

@app.route('/meetings')
@limiter.limit("10 per minute")
def get_meeting():
    api_key = request.headers.get('Authorization')
    meeting_id = request.args.get('id')
    include_images = request.args.get('include_images', 'false').lower() == 'true'

    if not api_key or not meeting_id:
        abort(400)

    user = verify_api_key(api_key)
    if not user:
        abort(401)

    meeting = Meeting.query.filter_by(id=meeting_id, user_id=user.id).first()
    if not meeting:
        abort(404)

    meeting_data = {
        'id': meeting.id,
        'name': meeting.name,
        'agents': meeting.agents,
        'questions': meeting.questions,
        'answers': meeting.answers
    }

    if not include_images:
        for agent in meeting_data['agents']:
            agent.pop('image_data', None)

    app.logger.info(f"User {user.id} requested meeting {meeting_id}")
    return jsonify(meeting_data)

@app.route('/timeframes')
@limiter.limit("10 per minute")
def get_timeframe():
    api_key = request.headers.get('Authorization')
    timeframe_id = request.args.get('id')
    include_images = request.args.get('include_images', 'false').lower() == 'true'

    if not api_key or not timeframe_id:
        abort(400)

    user = verify_api_key(api_key)
    if not user:
        abort(401)

    timeframe = Timeframe.query.filter_by(id=timeframe_id, user_id=user.id).first()
    if not timeframe:
        abort(404)

    timeframe_data = {
        'id': timeframe.id,
        'name': timeframe.name,
        'agents_data': timeframe.agents_data,
        'summary': timeframe.summary
    }

    if not include_images:
        timeframe_data.pop('images_data', None)
        timeframe_data.pop('thumbnail_images_data', None)

    app.logger.info(f"User {user.id} requested timeframe {timeframe_id}")
    return jsonify(timeframe_data)

if __name__ == '__main__':
    app.run()