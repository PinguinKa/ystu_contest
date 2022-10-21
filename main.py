import re
import bcrypt
from ystu_db import db
from random import randint
from datetime import datetime, timedelta
from send_email import send_email
from flask import Flask, render_template, request, url_for, redirect, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user



def hashed_password(plain_text_password):
    # Мы добавляем "соль" к нашему пароль, чтобы сделать его декодирование невозможным
    return bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    return bcrypt.checkpw(plain_text_password.encode('utf-8'), hashed_password)


app = Flask(__name__)


app.config.update(
    SECRET_KEY='WOW SUCH SECRET'
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(login):
    return User(login)


def check_if_admin():
    if 'login' in session:
        if session['login'] == 'admin':
            return True


@app.route('/')
def index():
    if check_if_admin():
        return render_template('index.html', admin=1)
    return render_template('index.html')


@app.route('/info/')
def info():
    if check_if_admin():
        return render_template('info.html', admin=1)
    return render_template('info.html')


@app.route('/events/')
def events():
    if check_if_admin():
        return render_template('events.html', admin=1)
    return render_template('events.html')


@app.route('/review/')
def review():
    if check_if_admin():
        return render_template('review.html', admin=1)
    return redirect(url_for('index'))


@app.route('/participants/')
def participants():
    if check_if_admin():
        data = db.users.get_all()
        data.pop(0)
        print(db.users.get('id', len(data)).id)
        return render_template('participants.html', admin=1, data=data)
    return redirect(url_for('index'))


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        for key in request.form:
            if request.form[key] == '':
                return render_template('register.html', message='Все поля должны быть заполнены!')


        row = db.users.get('login', request.form['login'])
        if row:
            return render_template('register.html', message='Такой пользователь уже существует!')

        if request.form['password'] != request.form['password_check']:
            return render_template('register.html', message='Пароли не совпадают')

        if not re.match('(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', request.form['login']):
            return render_template('register.html', message='Неправильный формат почты')

        data = dict(request.form)
        data['id'] = len(db.users.get_all())
        data.pop('password_check')
        db.users.put(data=data)
        send_email(request.form['login'], request.form['password'])
        return render_template('register.html', message='Регистрация прошла успешно')
    return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        row = db.users.get('login', request.form['login'])
        if not row:
            return render_template('login.html', error='Неправильный логин или пароль')

        if request.form['password'] == row.password:
            user = User(login)
            login_user(user)
            session['login'] = request.form['login']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неправильный логин или пароль')
    return render_template('login.html')


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    session.pop('login', None)
    return 'Пока'


















if __name__ == "__main__":
    app.run()
