import os
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

    @property
    def folder_path(self):
        user_folder = f"user_{self.id}"
        folder_path = os.path.join(current_app.root_path, 'user_data', user_folder)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def generate_api_key(self, expiration=None):
        s = Serializer(current_app.config['SECRET_KEY'])
        token = s.dumps({'user_id': self.id}).decode('utf-8')
        new_key = APIKey(key=token, owner=self)
        db.session.add(new_key)
        return token

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def create_user_data(self):
        self.agents_data = []
        self.images_data = {}

        # Create user folder
        os.makedirs(self.folder_path, exist_ok=True)

# ...

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

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
    user = db.relationship('User', backref=db.backref('timeframes', lazy=True))

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    agents = db.Column(db.JSON)
    questions = db.Column(db.JSON)
    answers = db.Column(db.JSON)
    is_public = db.Column(db.Boolean, default=False)
    public_url = db.Column(db.String(255), unique=True)