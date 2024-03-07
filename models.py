#models.py 
from extensions import db

import os, shutil, logging

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256))
    folder_path = db.Column(db.String(128), unique=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def create_user_folder(self):
        base_dir = os.path.join(os.getcwd(), 'user_content')
        user_dir = os.path.join(base_dir, self.username)
        agents_dir = os.path.join(user_dir, 'agents')
        pics_dir = os.path.join(agents_dir, 'pics')
    
        # Make sure the agents and pics directories are created
        os.makedirs(agents_dir, exist_ok=True)
        os.makedirs(pics_dir, exist_ok=True)
    
        # Copy the agents.json to the user's agent directory
        src_agents_file = os.path.join(os.getcwd(), 'agents', 'agents.json')
        dst_agents_file = os.path.join(agents_dir, 'agents.json')
        if os.path.exists(src_agents_file):
            shutil.copy(src_agents_file, dst_agents_file)
    
        # Copy the pics folder to the user's agent directory
        src_pics_dir = os.path.join(os.getcwd(), 'agents', 'pics')
        if os.path.exists(src_pics_dir):
            for pic_file in os.listdir(src_pics_dir):
                src_pic_path = os.path.join(src_pics_dir, pic_file)
                dst_pic_path = os.path.join(pics_dir, pic_file)
                shutil.copy(src_pic_path, dst_pic_path)
    
        self.folder_path = user_dir

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    agents_file = db.Column(db.String(255), nullable=False)
    result_count = db.Column(db.Integer, default=0)
    user = db.relationship('User', backref=db.backref('surveys', lazy=True))