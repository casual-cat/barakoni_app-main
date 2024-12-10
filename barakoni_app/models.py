from db import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BarakoniState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    hunger = db.Column(db.Integer, default=50)
    happiness = db.Column(db.Integer, default=50)
    energy = db.Column(db.Integer, default=50)
    evolution_stage = db.Column(db.Integer, default=1)

    user = db.relationship('User', backref='barakoni_state', uselist=False)
