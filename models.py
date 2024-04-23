"""
########
########This script works better with specific instructions. 
########
Here's a schema-like table and development guide for handling images and thumbnails for the three classes of agents:
Agent ClassImage HandlingThumbnail HandlingParsing LogicRequired Arguments, Parameters, and FieldsUser Agent- Stored in current_user.images_data dictionary<br>- Key: photo filename, Value: base64 encoded image data- Stored in current_user.thumbnail_images_data dictionary<br>- Key: photo filename + '_thumbnail', Value: base64 encoded thumbnail data- Extract photo filename from agent['photo_path']<br>- Use photo filename as key to retrieve image and thumbnail data from respective dictionaries- current_user.agents_data: List of user agents<br>- current_user.images_data: Dictionary mapping photo filenames to base64 encoded image data<br>- current_user.thumbnail_images_data: Dictionary mapping photo filenames to base64 encoded thumbnail dataTimeframe Agent- Stored in timeframe.images_data JSON field<br>- Key: photo filename, Value: base64 encoded image data- Stored in timeframe.thumbnail_images_data JSON field<br>- Key: photo filename + '_thumbnail', Value: base64 encoded thumbnail data- Extract photo filename from agent['photo_path']<br>- Parse timeframe.images_data and timeframe.thumbnail_images_data JSON fields<br>- Use photo filename as key to retrieve image and thumbnail data from respective parsed dictionaries- timeframe.agents_data: JSON field containing list of timeframe agents<br>- timeframe.images_data: JSON field mapping photo filenames to base64 encoded image data<br>- timeframe.thumbnail_images_data: JSON field mapping photo filenames to base64 encoded thumbnail dataAgent Class- Stored in current_user.images_data dictionary<br>- Key: photo filename, Value: base64 encoded image data- Stored in current_user.thumbnail_images_data dictionary<br>- Key: photo filename + '_thumbnail', Value: base64 encoded thumbnail data- Extract photo filename from agent.data['photo_path']<br>- Use photo filename as key to retrieve image and thumbnail data from respective dictionaries- Agent.query.filter_by(user_id=current_user.id).all(): List of Agent class instances<br>- current_user.images_data: Dictionary mapping photo filenames to base64 encoded image data<br>- current_user.thumbnail_images_data: Dictionary mapping photo filenames to base64 encoded thumbnail data
Instructions for accessing images and thumbnails for each agent class:

User Agent:

Retrieve the list of user agents from current_user.agents_data.
For each agent, extract the photo filename from agent['photo_path'].
Use the photo filename as the key to retrieve the base64 encoded image data from current_user.images_data dictionary.
Use the photo filename appended with '_thumbnail' as the key to retrieve the base64 encoded thumbnail data from current_user.thumbnail_images_data dictionary.
Pass the retrieved image and thumbnail data to the template for rendering.

Sample data:
pythonCopy codecurrent_user.agents_data = [
    {'id': 'agent1', 'photo_path': 'path/to/agent1.jpg', ...},
    {'id': 'agent2', 'photo_path': 'path/to/agent2.jpg', ...},
    ...
]
current_user.images_data = {
    'agent1.jpg': 'base64_encoded_image_data_agent1',
    'agent2.jpg': 'base64_encoded_image_data_agent2',
    ...
}
current_user.thumbnail_images_data = {
    'agent1.jpg_thumbnail': 'base64_encoded_thumbnail_data_agent1',
    'agent2.jpg_thumbnail': 'base64_encoded_thumbnail_data_agent2',
    ...
}

Timeframe Agent:

Retrieve the specific timeframe using Timeframe.query.get(timeframe_id).
Parse the timeframe.agents_data JSON field to get the list of timeframe agents.
Parse the timeframe.images_data and timeframe.thumbnail_images_data JSON fields to get the dictionaries mapping photo filenames to base64 encoded image and thumbnail data.
For each agent, extract the photo filename from agent['photo_path'].
Use the photo filename as the key to retrieve the base64 encoded image data from the parsed timeframe.images_data dictionary.
Use the photo filename appended with '_thumbnail' as the key to retrieve the base64 encoded thumbnail data from the parsed timeframe.thumbnail_images_data dictionary.
Pass the retrieved image and thumbnail data to the template for rendering.

Sample data:
pythonCopy codetimeframe.agents_data = json.dumps([
    {'id': 'agent1', 'photo_path': 'path/to/agent1.jpg', ...},
    {'id': 'agent2', 'photo_path': 'path/to/agent2.jpg', ...},
    ...
])
timeframe.images_data = json.dumps({
    'agent1.jpg': 'base64_encoded_image_data_agent1',
    'agent2.jpg': 'base64_encoded_image_data_agent2',
    ...
})
timeframe.thumbnail_images_data = json.dumps({
    'agent1.jpg_thumbnail': 'base64_encoded_thumbnail_data_agent1',
    'agent2.jpg_thumbnail': 'base64_encoded_thumbnail_data_agent2',
    ...
})

Agent Class:

Retrieve the list of Agent class instances using Agent.query.filter_by(user_id=current_user.id).all().
For each agent instance, extract the photo filename from agent.data['photo_path'].
Use the photo filename as the key to retrieve the base64 encoded image data from current_user.images_data dictionary.
Use the photo filename appended with '_thumbnail' as the key to retrieve the base64 encoded thumbnail data from current_user.thumbnail_images_data dictionary.
Pass the retrieved image and thumbnail data to the template for rendering.

Sample data:
pythonCopy codeagents = Agent.query.filter_by(user_id=current_user.id).all()
# Each agent instance contains data similar to user agents
agent.data = {'id': 'agent1', 'photo_path': 'path/to/agent1.jpg', ...}
current_user.images_data = {
    'agent1.jpg': 'base64_encoded_image_data_agent1',
    ...
}
current_user.thumbnail_images_data = {
    'agent1.jpg_thumbnail': 'base64_encoded_thumbnail_data_agent1',
    ...
}


By following these instructions and utilizing the provided arguments, parameters, and fields, you can effectively access and load images and thumbnails for the different classes of agents in your code.
Remember to handle scenarios where the required data may be missing or invalid, and implement appropriate error handling and fallback mechanisms.
When passing the image and thumbnail data to templates, ensure that you use the appropriate Jinja2 syntax to display the base64 encoded data as image sources."""

#models.py
import os
import datetime
import random
import json
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous.url_safe import URLSafeSerializer as Serializer
from flask import current_app


class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(64), index=True, unique=True)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password_hash = db.Column(db.String(256))
  agents_data = db.Column(db.JSON)
  images_data = db.Column(db.JSON, default={})
  thumbnail_images_data = db.Column(db.JSON, default={})
  credits = db.Column(db.Integer, default=0)
  meetings = db.relationship('Meeting', backref='creator', lazy=True)
  api_keys = db.relationship('APIKey', backref='owner', lazy='dynamic')
  timeframes = db.relationship('Timeframe', backref='user', lazy=True)
  agent_type = db.Column(db.String(20), default='user')

  @property
  def folder_path(self):
    user_folder = f"user_{self.id}"
    folder_path = os.path.join(current_app.root_path, 'user_data', user_folder)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

  def generate_api_key(self, expiration=None):
    s = Serializer(current_app.config['SECRET_KEY'])
    random_data = random.randint(1000, 9999)  # Random number for uniqueness
    timestamp = datetime.datetime.utcnow().isoformat()  # Current timestamp
    payload = {'user_id': self.id, 'timestamp': timestamp, 'rnd': random_data}
    token = s.dumps(payload)
    new_key = APIKey(key=token, owner=self)
    try:
      db.session.add(new_key)
      db.session.commit()
      return token
    except Exception as e:
      db.session.rollback(
      )  # Rollback if there's an issue, such as a non-unique key
      return None

  def set_password(self, password):
    self.password_hash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

  def create_user_data(self):
    self.agents_data = []
    self.images_data = {}

    # Create user folder
    os.makedirs(self.folder_path, exist_ok=True)


class APIKey(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  key = db.Column(db.String(256), unique=True, nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Agent(db.Model):
  id = db.Column(db.String, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  data = db.Column(db.JSON)
  user = db.relationship('User', backref=db.backref('agents', lazy=True))
  agent_type = db.Column(db.String(20), default='agent')

  @property
  def persona(self):
    return self.data.get('persona', '')

  @property
  def summary(self):
    return self.data.get('summary', '')

  @property
  def keywords(self):
    return self.data.get('keywords', [])

  @property
  def image_prompt(self):
    return self.data.get('image_prompt', '')

  @property
  def relationships(self):
    return self.data.get('relationships', [])


class Image(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  filename = db.Column(db.String(255), nullable=False)
  data = db.Column(db.LargeBinary)
  user = db.relationship('User', backref=db.backref('images', lazy=True))


class MainAgent(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  data = db.Column(db.Text, nullable=False)
  image_data = db.Column(db.Text)
  user = db.relationship('User', backref=db.backref('main_agents', lazy=True))


class Survey(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  survey_data = db.Column(db.JSON)
  is_public = db.Column(db.Boolean, default=False)
  public_url = db.Column(db.String(255), unique=True)
  user = db.relationship('User', backref=db.backref('surveys', lazy=True))


class Timeframe(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  agents_data = db.Column(db.Text, default='[]')
  images_data = db.Column(db.Text, default='{}')
  thumbnail_images_data = db.Column(db.Text, default='{}')
  agent_type = db.Column(db.String(20), default='timeframe')

  @property
  def agents_count(self):
    if self.agents_data:
      agents = json.loads(self.agents_data)
      return len(agents)
    return 0


class Meeting(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  agents = db.Column(db.JSON)
  questions = db.Column(db.JSON)
  answers = db.Column(db.JSON)
  is_public = db.Column(db.Boolean, default=False)
  public_url = db.Column(db.String(255), unique=True, nullable=True)
