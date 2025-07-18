from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'simple_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.String(20), nullable=False, default='Low')
    status = db.Column(db.String(20), nullable=False, default='To-Do')

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        tasks = Task.query.filter_by(user_id=session['user_id']).all()
        return render_template('dashboard.html', tasks=tasks)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not email or not password:
            flash("All fields are required.")
            return redirect(url_for('register'))

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()

        if existing_user:
            flash("Username or email already exists.")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password.")

    return render_template('login.html')

@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        task = Task(
            user_id=session['user_id'],
            title=request.form.get('title', '').strip(),
            description=request.form.get('description', '').strip(),
            deadline=request.form.get('deadline', '').strip(),
            priority=request.form.get('priority', 'Low'),
            status=request.form.get('status', 'To-Do')
        )
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('add_task.html', task=None)

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = Task.query.get_or_404(task_id)

    if task.user_id != session['user_id']:
        return redirect(url_for('home'))

    if request.method == 'POST':
        task.title = request.form.get('title', '').strip()
        task.description = request.form.get('description', '').strip()
        task.deadline = request.form.get('deadline', '').strip()
        task.priority = request.form.get('priority', 'Low')
        task.status = request.form.get('status', 'To-Do')

        db.session.commit()
        return redirect(url_for('home'))

    return render_template('add_task.html', task=task)

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = Task.query.get_or_404(task_id)

    if task.user_id == session['user_id']:
        db.session.delete(task)
        db.session.commit()

    return redirect(url_for('home'))

@app.route('/admin')
def admin_panel():
    if 'is_admin' in session and session['is_admin']:
        users = User.query.all()
        users_data = []
        for user in users:
            task_count = Task.query.filter_by(user_id=user.id).count()
            users_data.append({
                'username': user.username,
                'email': user.email,
                'task_count': task_count
            })
        return render_template('admin.html', users=users_data)
    else:
        flash("Access denied.")
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Create admin user if not exists
        admin_email = "admin@gmail.com"
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            hashed_password = generate_password_hash("adminpass")
            admin_user = User(username="admin", email=admin_email, password=hashed_password, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created.")
        else:
            print("Admin user already exists.")

    app.run(debug=True)
