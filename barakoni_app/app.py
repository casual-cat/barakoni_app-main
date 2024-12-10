from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from db import db
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change_this_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barakoni.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

with app.app_context():
    from models import User, BarakoniState
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        barakoni = BarakoniState.query.filter_by(user_id=current_user.id).first()
        if not barakoni:
            barakoni = BarakoniState(user_id=current_user.id)
            db.session.add(barakoni)
            db.session.commit()
        return render_template('home.html', barakoni=barakoni)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    from models import User
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/feed', methods=['POST'])
@login_required
def feed():
    from models import BarakoniState
    barakoni = BarakoniState.query.filter_by(user_id=current_user.id).first()
    if barakoni:
        barakoni.hunger = min(barakoni.hunger + 10, 100)
        db.session.commit()
        flash('You fed Barakoni!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
