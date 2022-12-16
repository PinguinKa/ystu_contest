import re
import bcrypt
import decimal
import send_email
from io import BytesIO
from ystu_db import db
from datetime import datetime, timedelta
from flask import Flask, render_template, request, url_for, redirect, session, send_file, Markup
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

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


def check_rights():
    if 'login' in session:
        if session['login'] == 'AdminAccess1812':
            rights = {'admin': True, 'jury': False, 'login': True}
        elif session['login'] == 'JuryMember3310':
            rights = {'admin': False, 'jury': True, 'login': True}
        else:
            rights = {'admin': False, 'jury': False, 'login': True}
    else:
        rights = {'admin': False, 'jury': False, 'login': False}
    return rights


@app.route('/')
def index():
    return render_template('index.html', rights=check_rights())


@app.route('/info/')
def info():
    return render_template('info.html', rights=check_rights())


@app.route('/events/')
def events():
    data = db.events.get_all()
    return render_template('events.html', rights=check_rights(), data=data)


@app.route('/events/<event_name>', methods=['GET', 'POST'])
def event(event_name):
    if request.method == 'GET':
        session['event'] = event_name
        event_info = db.events.get('name', event_name)[0]
        end_date = datetime.strptime(event_info.exp_date, "%d.%m.%Y") + timedelta(days=1)

        return render_template(f'events/{event_name}.html', rights=check_rights(),
                               event_ended=datetime.now() > end_date)

    if request.method == 'POST':
        session['event'] = event_name
        return redirect(url_for('submit'))


def hash_password(plain_text_password):
    return bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if check_rights()['login']:
        return redirect(url_for('edit'))

    if request.method == 'GET':
        return render_template('register.html', rights=check_rights())

    if request.method == 'POST':

        row = db.users.get('login', request.form['login'])
        if row:
            return render_template('register.html', rights=check_rights(), message='Такой пользователь уже существует!')

        if request.form['password'] != request.form['password_check']:
            return render_template('register.html', rights=check_rights(), message='Пароли не совпадают')

        if not re.match(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', request.form['login']):
            return render_template('register.html', rights=check_rights(), message='Неправильный формат почты')

        data = dict(request.form)
        data['id'] = len(db.users.get_all())
        data['participation'] = 'Этот пользователь ещё нигде не участвовал'
        data['password'] = hash_password(request.form['password'])
        data.pop('password_check')

        db.users.put(data=data)
        send_email.registration(request.form['login'], request.form['password'])
        return render_template('register.html', rights=check_rights(), message='Регистрация прошла успешно!' + Markup('<br/>') + 'На указанный почтовый ящик отправленно письмо подтверждения.' + Markup('<br/>') + 'Если вы не видите письма, пожалуйста, проверьте спам и правильность указанного адреса.' + Markup('<br/>') + 'Если адрес был указан неправильно, то замените его в настройках аккаунта.')


def check_password(plain_text_password, hashed_password):
    return bcrypt.checkpw(plain_text_password.encode('utf-8'), hashed_password)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', rights=check_rights())

    if request.method == 'POST':
        row = db.users.get('login', request.form['login'])
        if not row:
            return render_template('login.html', rights=check_rights(), message='Неправильный логин или пароль')

        if check_password(request.form['password'], row[0].password):
            user = User(login)
            login_user(user)
            session.modified = True
            session['login'] = request.form['login']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', rights=check_rights(), message='Неправильный логин или пароль')


@app.route('/edit/', methods=['GET', 'POST'])
@login_required
def edit():
    if not check_rights()['login']:
        return redirect(url_for('index'))

    data = db.users.get('login', session['login'])[0]

    if request.method == 'GET':
        return render_template('edit.html', rights=check_rights(), data=data)

    if request.method == 'POST':
        row = db.users.get('login', request.form['login'])
        if row:
            if request.form['login'] != session['login']:
                return render_template('edit.html', rights=check_rights(),
                                       message='Такой пользователь уже зарегистрирован!', data=data)

        if not re.match(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', request.form['login']):
            return render_template('edit.html', rights=check_rights(), message='Неправильный формат почты', data=data)

        if request.form['password'] != request.form['password_check']:
            return render_template('edit.html', rights=check_rights(), message='Пароли не совпадают', data=data)

        db.users.update('login', session['login'], 'last_name', request.form['last_name'])
        db.users.update('login', session['login'], 'first_name', request.form['first_name'])
        db.users.update('login', session['login'], 'middle_name', request.form['middle_name'])
        db.users.update('login', session['login'], 'university', request.form['university'])
        db.users.update('login', session['login'], 'password', hash_password(request.form['password']))
        db.users.update('login', session['login'], 'login', request.form['login'])
        session['login'] = request.form['login']
        data = db.users.get('login', session['login'])[0]

        send_email.edit(request.form['last_name'], request.form['first_name'], request.form['middle_name'],
                        request.form['university'], request.form['login'], request.form['password'])
        return render_template('edit.html', rights=check_rights(), message='Ваши изменения сохранены!', data=data)


ALLOWED_TEXT_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
def allowed_text_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_TEXT_EXTENSIONS

@app.route("/submit/", methods=['GET', 'POST'])
@login_required
def submit():
    if check_rights()['admin'] or check_rights()['jury']:
        return redirect(url_for('index'))

    events = db.events.get_all()
    themes = []
    for event in events:
        themes.append(event.themes.split(', '))

    event_name = ''
    if session['event']:
        event_name = session['event']

    if request.method == 'GET':
        return render_template('submit.html', rights=check_rights(), events=events, themes=themes, event_name=event_name)

    if request.method == 'POST':
        event = db.events.get('name', session['event'])[0]
        begin_date = datetime.strptime(event.begin_date, "%d.%m.%Y")
        exp_date = datetime.strptime(event.exp_date, "%d.%m.%Y")

        if datetime.now() < begin_date or datetime.now() > exp_date + timedelta(days=1):
            return render_template('submit.html', rights=check_rights(),
                                   message='По этому мероприятию работы не принимаются', events=events, themes=themes, event_name=event_name)



        if 'video' not in session['event']:
            if 'file' not in request.files:
                return render_template('submit.html', rights=check_rights(), message='Загрузите файл!', events=events,
                                       themes=themes, event_name=event_name)
            file = request.files['file']
            if file.filename == '':
                return render_template('submit.html', message='Загрузите файл!', rights=check_rights(), events=events,
                                       themes=themes, event_name=event_name)

            if file and allowed_text_file(file.filename):
                user_submits = db.submits.get('login', session['login'])
                for user_submit in user_submits:
                    if user_submit.event == session['event'] and user_submit.theme == request.form['theme']:
                        return render_template('submit.html', rights=check_rights(),
                                               message='Вы уже участвовали в этой номинации', events=events, themes=themes, event_name=event_name)
            else:
                return render_template('submit.html', rights=check_rights(), message='Неверный формат файла', events=events,
                                       themes=themes, event_name=event_name)

            id = len(db.submits.get_all()) + 1
            db.submits.put({'id': id,
                            'login': session['login'],
                            'filename': file.filename,
                            'file': file.read(),
                            'event': session['event'],
                            'theme': request.form['theme'],
                            'scientific_director': request.form['scientific_director'],
                            'num_of_checks': 0
                            })

        else:

            if not re.match(r'(?:https?:\/\/)?(?:www\.)?youtu(?:\.be\/|be.com\/\S*(?:watch|embed)(?:(?:(?=\/[-a-zA-Z0-9_]{11,}(?!\S))\/)|(?:\S*v=|v\/)))([-a-zA-Z0-9_]{11,})', request.form['link']):
                return render_template('submit.html', rights=check_rights(), message='Неправильный формат ссылки',
                                       events=events, themes=themes, event_name=event_name)

            link = request.form['link']
            if 'youtu.be' in link:
                link = link.split('/')[-1]
            else:
                link = link.split('=')[-1]

            id = len(db.submits.get_all()) + 1
            db.submits.put({'id': id,
                            'login': session['login'],
                            'filename': link,
                            'event': session['event'],
                            'theme': request.form['theme'],
                            'scientific_director': request.form['scientific_director'],
                            'num_of_checks': 0
                            })

        rows = db.users.get('login', session['login'])[0]
        event = db.events.get('name', session['event'])[0]
        participation = f"{event.title} - {request.form['theme']};  "
        if rows.participation == 'Этот пользователь ещё нигде не участвовал':
            db.users.update('login', session['login'], 'participation', participation)
        else:
            db.users.update('login', session['login'], 'participation', rows.participation + participation)

        send_email.participation(session['login'], db.events.get('name', session['event'])[0].title,
                                 request.form['theme'], str(id))
        return render_template('submit.html', rights=check_rights(),
                               message='Успешно загружено! Уникальный код работы отправлен Вам на почту. Если вы не получили письмо, проверьте папки Спам и Удаленные',
                               events=events, themes=themes, event_name=event_name)


@app.route('/participants/')
@login_required
def participants():
    if not check_rights()['admin']:
        return redirect(url_for('index'))
    data = db.users.get_all()
    data.pop(0)
    data.pop(0)
    return render_template('participants.html', rights=check_rights(), data=data)


@app.route('/review/', methods=['GET', 'POST'])
@login_required
def review():
    events = db.events.get_all()
    themes = []
    for event in events:
        themes.append(event.themes.split(', '))

    if not check_rights()['jury']:
        return redirect(url_for('index'))

    if request.method == 'POST':
        data = db.submits.get_all()
        event, theme = request.form['event'], request.form['theme']
        session['jury'] = request.form['jury']
        return render_template('review.html', rights=check_rights(), events=events, event=event, themes=themes,
                               theme=theme, data=data, visibility='visible', jury_name=request.form['jury'],
                               event_name=request.form['event'], theme_name=request.form['theme'])
    return render_template('review.html', rights=check_rights(), events=events, themes=themes, visibility='hidden')


@app.route('/review/download/<id>')
def download(id):
    if not check_rights()['admin'] and not check_rights()['jury']:
        return redirect(url_for('index'))

    upload = db.submits.get('id', id)[0]
    return send_file(BytesIO(upload.file), download_name=upload.filename, as_attachment=True)


@app.route('/review/<id>', methods=['GET', 'POST'])
def review_check(id):
    if not check_rights()['jury']:
        return redirect(url_for('index'))

    data = db.submits.get('id', int(id))[0]

    if request.method == 'GET':
        checks = db.reviews.get('id', int(id))
        for check in checks:
            if check.id == int(id) and session['jury'] == check.jury:
                return render_template('review_id.html', rights=check_rights(), data=data,
                                       message='Вы уже проверили эту работу')

    if request.method == 'POST':
        checks = db.reviews.get('id', int(id))
        for check in checks:
            if check.id == int(id) and session['jury'] == check.jury:
                return render_template('review_id.html', rights=check_rights(), data=data,
                                       message='Вы уже проверили эту работу')

        if request.form.get('requirements_met'):
            criteria1 = int(request.form['criteria1'])
            criteria2 = int(request.form['criteria2'])
            criteria3 = int(request.form['criteria3'])
            criteria4 = int(request.form['criteria4'])
        else:
            criteria1 = 0
            criteria2 = 0
            criteria3 = 0
            criteria4 = 0

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

        return render_template('review_id.html', rights=check_rights(), data=data,
                               message='Работа проверена')
    return render_template('review_id.html', rights=check_rights(), data=data)


@app.route('/rating/', methods=['GET', 'POST'])
def rating():
    if not check_rights()['admin']:
        return redirect(url_for('index'))

    events = db.events.get_all()
    themes = []
    for event in events:
        themes.append(event.themes.split(', '))

    if request.method == 'GET':
        return render_template('rating.html', rights=check_rights(), events=events, themes=themes, visibility='hidden')

    if request.method == 'POST':
        event, theme = request.form['event'], request.form['theme']
        submits = db.submits.get_all()
        for submit in submits:
            if submit.num_of_checks > 0:
                user = db.users.get('login', submit.login)[0]

                reviews = db.reviews.get('id', submit.id)
                score = 0
                for review in reviews:
                    score += review.sum

                final_score = score / len(reviews)
                final_score = decimal.Decimal(final_score).quantize(decimal.Decimal('0.00'),
                                                                    rounding=decimal.ROUND_HALF_UP)

                existence = db.rating.get('submit_id', submit.id)
                if existence:
                    db.rating.update('submit_id', submit.id, 'final_score', final_score)
                else:
                    data = {
                        'login': user.login,
                        'last_name': user.last_name,
                        'first_name': user.first_name,
                        'middle_name': user.middle_name,
                        'submit_id': submit.id,
                        'link': submit.filename,
                        'university': user.university,
                        'event': submit.event,
                        'theme': submit.theme,
                        'scientific_director': submit.scientific_director,
                        'final_score': final_score
                    }

                    db.rating.put(data)

        data = db.rating.get_all()
        return render_template('rating.html', rights=check_rights(), events=events, event=event, themes=themes,
                               theme=theme, data=data, visibility='visible', event_name=request.form['event'],
                               theme_name=request.form['theme'])


@app.route("/logout/")
@login_required
def logout():
    if not check_rights()['login']:
        return redirect(url_for('index'))
    logout_user()
    session.pop('login', None)
    session.pop('jury', None)
    session.pop('event', None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run()