from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from db import db
from models import BarakoniState, GlobalState, Item
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change_this_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barakoni.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    barakoni = BarakoniState.query.first()
    if not barakoni:
        barakoni = BarakoniState()
        db.session.add(barakoni)

    global_state = GlobalState.query.first()
    if not global_state:
        global_state = GlobalState(points=100)
        db.session.add(global_state)

    # Ensure items
    if not Item.query.filter_by(name='Fancy Hat').first():
        db.session.add(Item(name='Fancy Hat', cost=50, owned=False))
    if not Item.query.filter_by(name='Glasses').first():
        db.session.add(Item(name='Glasses', cost=40, owned=False))
    if not Item.query.filter_by(name='Wig').first():
        db.session.add(Item(name='Wig', cost=60, owned=False))

    db.session.commit()

@app.before_request
def ensure_defaults():
    if 'secret_number' not in session:
        session['secret_number'] = random.randint(1, 5)
    if 'devops_quiz_wins' not in session:
        session['devops_quiz_wins'] = 0
    if 'quiz_question' not in session:
        session['quiz_question'] = None

def day_night_cycle():
    hour = datetime.now().hour
    return 'day' if hour < 18 else 'night'

def seasonal_theme():
    month = datetime.now().month
    if month in [12,1,2]:
        return 'winter'
    elif month in [3,4,5]:
        return 'spring'
    elif month in [6,7,8]:
        return 'summer'
    else:
        return 'autumn'

def random_event(barakoni):
    if random.random() < 0.1:
        event = random.choice(["storm", "visitor", "strangeNoise"])
        if event == "storm":
            barakoni.happiness = max(barakoni.happiness - 10, 0)
            flash("A sudden storm scared Barakoni, reducing happiness!", 'negative')
        elif event == "visitor":
            barakoni.happiness = min(barakoni.happiness + 10, 100)
            flash("A friendly visitor cheered Barakoni up!", 'positive')
        else:
            barakoni.energy = max(barakoni.energy - 5, 0)
            flash("A strange noise at night disturbed Barakoni's rest.", 'negative')

def check_evolution(barakoni):
    if barakoni.happiness > 80:
        barakoni.happy_streak += 1
        barakoni.unhappy_streak = 0
    elif barakoni.happiness < 30:
        barakoni.unhappy_streak += 1
        barakoni.happy_streak = 0
    else:
        barakoni.happy_streak = 0
        barakoni.unhappy_streak = 0

    if barakoni.happy_streak >= 3:
        barakoni.evolution_stage = 2
    if barakoni.unhappy_streak >= 3:
        barakoni.evolution_stage = 3

def pick_image(barakoni):
    base = 'barakoni.png'
    if barakoni.evolution_stage == 2:
        base = 'barakoni_happy.png'
    elif barakoni.evolution_stage == 3:
        base = 'barakoni.png'

    if barakoni.happiness < 30:
        base = 'barakoni_annoyed.png'

    if getattr(barakoni, 'has_hat', False):
        if barakoni.evolution_stage == 2 and barakoni.happiness >= 30:
            base = 'barakoni_hat_happy.png'
        elif barakoni.happiness < 30:
            base = 'barakoni_hat_annoyed.png'
        else:
            base = 'barakoni_hat.png'

    return base

@app.route('/')
def index():
    barakoni = BarakoniState.query.first()
    global_state = GlobalState.query.first()

    random_event(barakoni)
    check_evolution(barakoni)
    db.session.commit()

    image_filename = pick_image(barakoni)
    day_or_night = day_night_cycle()
    season = seasonal_theme()

    return render_template('index.html',
                           barakoni=barakoni,
                           image_filename=image_filename,
                           points=global_state.points,
                           day_or_night=day_or_night,
                           season=season)

@app.route('/tease', methods=['POST'])
def tease():
    barakoni = BarakoniState.query.first()
    if barakoni:
        barakoni.happiness = max(barakoni.happiness - 10, 0)
        db.session.commit()
        flash("You teased Barakoni! He looks annoyed.", 'negative')
    # If this is an AJAX request, return JSON, else redirect
    if request.is_json:
        return jsonify({"status": "ok"})
    return redirect(url_for('index'))

@app.route('/feed', methods=['POST'])
def feed():
    barakoni = BarakoniState.query.first()
    if barakoni:
        barakoni.hunger = min(barakoni.hunger + 10, 100)
        db.session.commit()
        flash('You fed Barakoni! He munches happily.', 'positive')
    return redirect(url_for('index'))

@app.route('/play', methods=['POST'])
def play():
    barakoni = BarakoniState.query.first()
    if barakoni:
        barakoni.happiness = min(barakoni.happiness + 10, 100)
        barakoni.energy = max(barakoni.energy - 5, 0)
        db.session.commit()
        flash('You played with Barakoni! He looks cheerful, though tired.', 'positive')
    return redirect(url_for('index'))

@app.route('/rest', methods=['POST'])
def rest():
    barakoni = BarakoniState.query.first()
    if barakoni:
        barakoni.energy = min(barakoni.energy + 10, 100)
        db.session.commit()
        flash('Barakoni rested and regained energy!', 'positive')
    return redirect(url_for('index'))

@app.route('/annoy', methods=['POST'])
def annoy():
    barakoni = BarakoniState.query.first()
    if barakoni:
        barakoni.happiness = max(barakoni.happiness - 20, 0)
        barakoni.energy = max(barakoni.energy - 5, 0)
        db.session.commit()
        flash("You really annoyed Barakoni! He glares at you.", 'negative')
    return redirect(url_for('index'))

@app.route('/shop', methods=['GET', 'POST'])
def shop():
    global_state = GlobalState.query.first()
    items = Item.query.all()
    if request.method == 'POST':
        item_name = request.form.get('item_name')
        item = Item.query.filter_by(name=item_name).first()
        if item and not item.owned:
            if global_state.points >= item.cost:
                global_state.points -= item.cost
                item.owned = True
                db.session.commit()
                flash(f"You bought {item.name}!", 'positive')
            else:
                flash("Not enough points!", 'negative')
        else:
            flash("Item already owned or not found!", 'negative')
        return redirect(url_for('shop'))
    return render_template('shop.html', items=items, points=global_state.points)

@app.route('/equip_item', methods=['POST'])
def equip_item():
    barakoni = BarakoniState.query.first()
    item_name = request.form.get('item_name')
    item = Item.query.filter_by(name=item_name).first()
    if item and item.owned:
        if item_name == 'Fancy Hat':
            barakoni.has_hat = not barakoni.has_hat
            flash("Toggled Fancy Hat!", 'positive')
        elif item_name == 'Glasses':
            barakoni.has_glasses = not barakoni.has_glasses
            flash("Toggled Glasses!", 'positive')
        elif item_name == 'Wig':
            barakoni.has_wig = not barakoni.has_wig
            flash("Toggled Wig!", 'positive')
        db.session.commit()
    else:
        flash("You don't own this item!", 'negative')
    return redirect(url_for('shop'))

@app.route('/minigame')
def minigame():
    global_state = GlobalState.query.first()
    return render_template('minigame.html', points=global_state.points)

@app.route('/minigame', methods=['POST'])
def minigame_post():
    guess = request.form.get('guess')
    barakoni = BarakoniState.query.first()
    global_state = GlobalState.query.first()
    secret = session.get('secret_number', random.randint(1,5))
    if guess and guess.isdigit():
        guess = int(guess)
        if guess == secret:
            flash("You guessed correctly! +10 happiness and +10 points!", 'positive')
            barakoni.happiness = min(barakoni.happiness + 10, 100)
            global_state.points += 10
            session['secret_number'] = random.randint(1,5)
        else:
            flash("Wrong guess! -5 happiness", 'negative')
            barakoni.happiness = max(barakoni.happiness - 5, 0)
        db.session.commit()
    return redirect(url_for('minigame'))

DEVOPS_QUESTIONS = [
    {
        "question": "Which of the following tools is commonly used for container orchestration?",
        "options": ["Git", "Kubernetes", "Jenkins", "Docker"],
        "answer": "Kubernetes"
    },
    # ... Add all other 15+ questions as before ...
    {
        "question": "CI/CD stands for:",
        "options": ["Continuous Integration/Continuous Delivery", "Concurrent Integration/Constant Deployment", "Continuous Inspection/Continuous Debugging", "Continuous Improvement/Continuous Design"],
        "answer": "Continuous Integration/Continuous Delivery"
    },
    {
        "question": "Which configuration management tool uses a declarative language and YAML-based playbooks?",
        "options": ["Chef", "Puppet", "Ansible", "SaltStack"],
        "answer": "Ansible"
    },
    {
        "question": "What does 'Infrastructure as Code' mean?",
        "options": ["Using code comments in infrastructure diagrams", "Managing infrastructure using machine-readable definition files", "Manually configuring servers", "Using a code editor to write server configs"],
        "answer": "Managing infrastructure using machine-readable definition files"
    },
    {
        "question": "Which of the following is a popular monitoring and alerting toolkit?",
        "options": ["Prometheus", "Nagios", "Zabbix", "All of the above"],
        "answer": "All of the above"
    },
    {
        "question": "Which practice involves merging code changes into the main branch as soon as they're ready?",
        "options": ["Feature Branching", "Continuous Integration", "Gitflow", "Waterfall Integration"],
        "answer": "Continuous Integration"
    },
    {
        "question": "In DevOps, 'shift left' means:",
        "options": ["Moving deployment scripts to the end of the pipeline", "Finding and fixing issues earlier in the development cycle", "Adding more stages after production deployment", "Only working on tasks from left to right"],
        "answer": "Finding and fixing issues earlier in the development cycle"
    },
    {
        "question": "Which tool is often used to define and provision infrastructure on various providers using a single configuration language?",
        "options": ["Terraform", "Bash Scripts", "Docker Compose", "Vagrant"],
        "answer": "Terraform"
    },
    {
        "question": "Which is a popular solution for service mesh?",
        "options": ["Istio", "GitLab", "Kubeadm", "SonarQube"],
        "answer": "Istio"
    },
    {
        "question": "What is the main purpose of a load balancer in DevOps?",
        "options": ["Store code repositories", "Balance incoming network traffic across multiple servers", "Run unit tests", "Monitor server logs"],
        "answer": "Balance incoming network traffic across multiple servers"
    },
    {
        "question": "Which tool helps automate building, testing, and deploying software?",
        "options": ["Jenkins", "Nginx", "Consul", "Cassandra"],
        "answer": "Jenkins"
    },
    {
        "question": "What is a 'blue-green deployment'?",
        "options": ["A method to toggle between two production environments for minimal downtime", "A type of code formatting style", "A testing strategy for unit tests", "An environment variable naming convention"],
        "answer": "A method to toggle between two production environments for minimal downtime"
    },
    {
        "question": "Containers are typically run using which Linux technology?",
        "options": ["SELinux", "cgroups and namespaces", "AppArmor", "Systemd timers"],
        "answer": "cgroups and namespaces"
    },
    {
        "question": "GitOps primarily focuses on:",
        "options": ["Using Git as a single source of truth for infrastructure and deployments", "Storing binary artifacts in Git", "Running Git commands on production servers", "Logging user activities with Git"],
        "answer": "Using Git as a single source of truth for infrastructure and deployments"
    },
    {
        "question": "DevOps is best described as:",
        "options": ["A tool to automate coding", "A methodology to integrate development and operations for faster delivery", "A programming language", "A database management system"],
        "answer": "A methodology to integrate development and operations for faster delivery"
    },
    {
        "question": "Which tool is commonly used for continuous monitoring and visualization?",
        "options": ["Grafana", "Vim", "Emacs", "Eclipse"],
        "answer": "Grafana"
    }
]

@app.route('/minigame_quiz', methods=['GET', 'POST'])
def minigame_quiz():
    barakoni = BarakoniState.query.first()
    global_state = GlobalState.query.first()

    if request.method == 'POST':
        chosen_answer = request.form.get('answer')
        q_index = session.get('quiz_question')
        if q_index is not None:
            question_data = DEVOPS_QUESTIONS[q_index]
            correct_answer = question_data['answer']
            if chosen_answer == correct_answer:
                flash("Correct! You truly are a DevOps wizard! +10 happiness, +20 points", 'positive')
                barakoni.happiness = min(barakoni.happiness + 10, 100)
                global_state.points += 20
                wins = session.get('devops_quiz_wins', 0)
                wins += 1
                session['devops_quiz_wins'] = wins
            else:
                flash(f"Wrong answer! The correct answer was: {correct_answer}. -5 happiness", 'negative')
                barakoni.happiness = max(barakoni.happiness - 5, 0)
            db.session.commit()

        return redirect(url_for('minigame_quiz'))

    # GET request: show a new question
    q_index = random.randint(0, len(DEVOPS_QUESTIONS)-1)
    session['quiz_question'] = q_index
    question_data = DEVOPS_QUESTIONS[q_index]

    return render_template('minigame_quiz.html',
                           points=global_state.points,
                           question=question_data['question'],
                           options=question_data['options'])

if __name__ == '__main__':
    app.run(debug=True)
