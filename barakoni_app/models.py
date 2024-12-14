from db import db

class BarakoniState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hunger = db.Column(db.Integer, default=50)
    happiness = db.Column(db.Integer, default=50)
    energy = db.Column(db.Integer, default=50)
    evolution_stage = db.Column(db.Integer, default=1)
    happy_streak = db.Column(db.Integer, default=0)
    unhappy_streak = db.Column(db.Integer, default=0)
    has_hat = db.Column(db.Boolean, default=False)
    has_glasses = db.Column(db.Boolean, default=False)
    has_wig = db.Column(db.Boolean, default=False)

class GlobalState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer, default=0)
    # Removed last_visit since no daily logs

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    cost = db.Column(db.Integer)
    owned = db.Column(db.Boolean, default=False)
