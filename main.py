import re
import bcrypt
from datetime import datetime
from ystu_db import db
import send_email
from flask import Flask, render_template, request, url_for, redirect, session, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.utils import secure_filename
from io import BytesIO


def hash_password(plain_text_password):
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
    def __init__(self, user_id):
        self.id = user_id


@login_manager.user_loader
def load_user(user_login):
    return User(user_login)


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


check_login = 0


def check_if_admin():
    if 'login' in session:
        if session['login'] == 'admin':
            return True


@app.route('/')
def index():
    if check_if_admin():
        return render_template('index.html', admin=1)
    return render_template('index.html', check_login=check_login)


@app.route('/info/')
def info():
    if check_if_admin():
        return render_template('info.html', admin=1)
    return render_template('info.html', check_login=check_login)


# http://127.0.0.1:5000/events/stc-2021 добавить к чек листу ссылку на рекомендации
@app.route('/events/')
def events():
    data = db.events.get_all()
    if check_if_admin():
        return render_template('events.html', admin=1, data=data)
    return render_template('events.html', check_login=check_login, data=data)


@app.route('/translation/')
def translation():
    if check_if_admin():
        return render_template('translation.html', admin=1)
    return render_template('translation.html', check_login=check_login)


@app.route('/review/', methods=['GET', 'POST'])
def review():
    events = db.events.get_all()
    themes = []
    for event in events:
        themes.append(event.themes.split())

    if check_if_admin():
        if request.method == 'POST':
            data = db.submits.get_all()
            event, theme = request.form['event'], request.form['theme']
            session['jury'] = request.form['jury']
            return render_template('review.html', admin=1, events=events, event=event, themes=themes, theme=theme,
                                   data=data, visibility='visible', jury_name=request.form['jury'], event_name=request.form['event'], theme_name=request.form['theme'])
        return render_template('review.html', admin=1, events=events, themes=themes, visibility='hidden')
    return redirect(url_for('index'))


@app.route('/participants/')
def participants():
    if check_if_admin():
        data = db.users.get_all()
        data.pop(0)
        return render_template('participants.html', admin=1, data=data)
    return redirect(url_for('index'))


@app.route('/rating/')
def rating():
    if check_if_admin():
        data = db.review.get_all()
        return render_template('rating.html', admin=1, data=data)
    return redirect(url_for('index'))


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if check_login == 0:
        if request.method == 'POST':

            row = db.users.get('login', request.form['login'])
            if row:
                return render_template('register.html', message='Такой пользователь уже существует!')

            if request.form['password'] != request.form['password_check']:
                return render_template('register.html', message='Пароли не совпадают')

            if not re.match(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', request.form['login']):
                return render_template('register.html', message='Неправильный формат почты')

            data = dict(request.form)
            data['id'] = len(db.users.get_all())
            data.pop('password_check')
            db.users.put(data=data)
            send_email.registration(request.form['login'], request.form['password'])
            return render_template('register.html', message='Регистрация прошла успешно')

        return render_template('register.html')
    return redirect(url_for('edit'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    global check_login
    if request.method == 'POST':
        row = db.users.get('login', request.form['login'])[0]
        if not row:
            return render_template('login.html', error='Неправильный логин или пароль')

        if request.form['password'] == row.password:
            user = User(login)
            login_user(user)
            check_login = 1
            session.modified = True
            session['login'] = request.form['login']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неправильный логин или пароль')
    return render_template('login.html')


@app.route('/edit/', methods=['GET', 'POST'])
def edit():
    data = db.users.get('login', session['login'])[0]

    if request.method == 'POST':

        row = db.users.get('login', request.form['login'])
        if row:
            if request.form['login'] != session['login']:
                return render_template('edit.html', message='Такой пользователь уже зарегистрирован!', data=data,
                                       check_login=check_login)

        if not re.match(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', request.form['login']):
            return render_template('edit.html', message='Неправильный формат почты', data=data, check_login=check_login)

        if request.form['password'] != request.form['password_check']:
            return render_template('edit.html', message='Пароли не совпадают')

        db.users.update('login', session['login'], 'last_name', request.form['last_name'])
        db.users.update('login', session['login'], 'first_name', request.form['first_name'])
        db.users.update('login', session['login'], 'middle_name', request.form['middle_name'])
        db.users.update('login', session['login'], 'university', request.form['university'])
        db.users.update('login', session['login'], 'password', request.form['password'])
        db.users.update('login', session['login'], 'login', request.form['login'])
        session['login'] = request.form['login']
        data = db.users.get('login', session['login'])[0]

        send_email.edit(request.form['last_name'], request.form['first_name'], request.form['middle_name'],
                        request.form['university'], request.form['login'], request.form['password'])
        return render_template('edit.html', message='Ваши изменения сохранены!', data=data, check_login=check_login)

    if check_if_admin():
        return render_template('edit.html', data=data, check_login=check_login, admin=1)
    else:
        return render_template('edit.html', data=data, check_login=check_login)


@app.route("/submit/", methods=['GET', 'POST'])
@login_required
def submit():
    events = db.events.get_all()
    themes = []
    for event in events:
        themes.append(event.themes.split())

    if check_if_admin():
        return redirect(url_for('index'))

    if request.method == 'POST':
        event = db.events.get('name', request.form['event'])[0]
        begin_date = datetime.strptime(event.begin_date, "%d.%m.%Y")
        exp_date = datetime.strptime(event.exp_date, "%d.%m.%Y")

        if datetime.now() < begin_date or datetime.now() > exp_date:
            return render_template('submit.html', message='По этому мероприятию работы не принимаются',
                                   check_login=check_login, events=events, themes=themes)

        if 'file' not in request.files:
            return render_template('submit.html', message='Загрузите файл!', check_login=check_login, events=events,
                                   themes=themes)

        file = request.files['file']
        if file.filename == '':
            return render_template('submit.html', message='Загрузите файл!', check_login=check_login, events=events,
                                   themes=themes)

        if file and allowed_file(file.filename):
            user_submits = db.submits.get('login', session['login'])
            for user_submit in user_submits:
                if user_submit.event == request.form['event'] and user_submit.theme == request.form['theme']:
                    return render_template('submit.html', message='Вы уже участвовали в этой номинации',
                                           check_login=check_login, events=events, themes=themes)

            db.submits.put({'id': len(db.submits.get_all()) + 1,
                            'login': session['login'],
                            'filename': file.filename,
                            'file': file.read(),
                            'event': request.form['event'],
                            'theme': request.form['theme'],
                            'num_of_checks': 0
                            })

            send_email.participation(session['login'], db.events.get('name', request.form['event'])[0].title,
                                     request.form['theme'])
            return render_template('submit.html', message='Успешно загружено', check_login=check_login, events=events,
                                   themes=themes)

        return render_template('submit.html', message='Неверный формат файла', check_login=check_login, events=events,
                               themes=themes)

    event_name = ''
    if session['event']:
        event_name = session['event']
    return render_template('submit.html', check_login=check_login, events=events, themes=themes, event_name=event_name)


@app.route('/review/download/<id>')
def download(id):
    if check_if_admin():
        upload = db.submits.get('id', id)[0]
        return send_file(BytesIO(upload.file), download_name=upload.filename, as_attachment=True)
    return redirect(url_for('index'))


@app.route('/review/<id>', methods=['GET', 'POST'])
def review_check(id):
    if check_if_admin():
        data = db.submits.get('id', int(id))[0]
        if request.method == 'POST':

            check = db.reviews.get('id', int(id))
            if check:
                check = check[0]
                if check.id == int(id) and session['jury'] == check.jury:
                    return render_template('review_id.html', admin=1, data=data, message='Вы уже проверили эту работу')

            criteria1 = int(request.form['criteria1'])
            criteria2 = int(request.form['criteria2'])
            criteria3 = int(request.form['criteria3'])
            criteria4 = int(request.form['criteria4'])
            sum = criteria1 + criteria2 + criteria3 + criteria4

            db.reviews.put({
                'id': int(id),
                'jury': session['jury'],
                'criteria1': criteria1,
                'criteria2': criteria2,
                'criteria3': criteria3,
                'criteria4': criteria4,
                'sum': sum
            })

            count = data.num_of_checks
            db.submits.update('id', int(id), 'num_of_checks', count + 1)
            if data.jury_members:
                jury_members = data.jury_members + ', ' + session['jury']
                db.submits.update('id', int(id), 'jury_members', jury_members)
            else:
                db.submits.update('id', int(id), 'jury_members', session['jury'])

            return render_template('review_id.html', admin=1, data=data)
        return render_template('review_id.html', admin=1, data=data)
    return redirect(url_for('index'))


@app.route('/events/<event>', methods=['GET', 'POST'])
@login_required
def event(event):
    if check_if_admin():
        return render_template(f'events/{event}.html', admin=1, check_login=1)
    if request.method == 'POST':
        session['event'] = event
        return redirect(url_for('submit'))
    return render_template(f'events/{event}.html', check_login=1)


@app.route("/logout/")
@login_required
def logout():
    global check_login
    check_login = 0
    logout_user()
    session.pop('login', None)
    session.pop('jury', None)
    session.pop('event', None)

    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run()
