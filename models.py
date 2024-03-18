from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(64), index=True, unique=True)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password_hash = db.Column(db.String(256))
  agents_data = db.Column(db.JSON)
  images_data = db.Column(db.JSON)

  def set_password(self, password):
    self.password_hash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

  def create_user_data(self):
    self.agents_data = []
    self.images_data = {}


class Survey(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  survey_data = db.Column(db.JSON)
  is_public = db.Column(db.Boolean, default=False)
  public_url = db.Column(db.String(255), unique=True)

  user = db.relationship('User', backref=db.backref('surveys', lazy=True))
