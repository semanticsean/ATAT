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


def add_monthly_credits():
  users = User.query.all()
  for user in users:
    user.credits += 10
  db.session.commit()


class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(64), index=True, unique=True)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password_hash = db.Column(db.String(256))
  agents_data = db.Column(db.JSON)
  images_data = db.Column(db.JSON, default={})
  thumbnail_images_data = db.Column(db.JSON, default={})
  credits = db.Column(db.Integer, default=10)
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
  voice = db.Column(db.String(20), default='echo')

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
  agents_data = db.Column(db.Text, nullable=False)
  images_data = db.Column(db.Text, nullable=False)
  thumbnail_images_data = db.Column(db.Text, nullable=False)
  summary = db.Column(db.Text)
  image_data = db.Column(db.Text)
  thumbnail_image_data = db.Column(db.Text)

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
  original_name = db.Column(db.String(100))
  summary = db.Column(db.Text)
  image_data = db.Column(db.Text)
  thumbnail_image_data = db.Column(db.Text)


class Conversation(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  name = db.Column(db.String(100), nullable=False)
  agents = db.Column(db.JSON)
  messages = db.Column(db.JSON)
  timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

  def __init__(self, user_id, name, agents, messages):
    self.user_id = user_id
    self.name = name
    self.agents = agents
    self.messages = messages


class Document(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  filename = db.Column(db.String(255), nullable=False)
  data = db.Column(db.JSON)
  user = db.relationship('User', backref=db.backref('documents', lazy=True))