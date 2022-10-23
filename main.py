import re
import bcrypt
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


UPLOAD_FOLDER = '/files'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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


@app.route('/events/')
def events():
    if check_if_admin():
        return render_template('events.html', admin=1)
    return render_template('events.html', check_login=check_login)


@app.route('/translation/')
def translation():
    if check_if_admin():
        return render_template('translation.html', admin=1)
    return render_template('translation.html', check_login=check_login)


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
    if check_login == 0:
        if request.method == 'POST':
            for key in request.form:
                if request.form[key] == '':
                    return render_template('register.html', message='Все поля должны быть заполнены!')

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
        row = db.users.get('login', request.form['login'])
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
    data = db.users.get('login', session['login'])

    if request.method == 'POST':

        for key in request.form:
            if request.form[key] == '':
                return render_template('edit.html', message='Все поля должны быть заполнены!', data=data,
                                       check_login=check_login)

        row = db.users.get('login', request.form['login'])
        if row:
            if request.form['login'] != session['login']:
                return render_template('edit.html', message='Такой пользователь уже зарегистрирован!', data=data,
                                       check_login=check_login)

        if not re.match(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', request.form['login']):
            return render_template('edit.html', message='Неправильный формат почты', data=data, check_login=check_login)

        db.users.update('login', session['login'], 'last_name', request.form['last_name'])
        db.users.update('login', session['login'], 'first_name', request.form['first_name'])
        db.users.update('login', session['login'], 'middle_name', request.form['middle_name'])
        db.users.update('login', session['login'], 'university', request.form['university'])
        db.users.update('login', session['login'], 'password', request.form['password'])
        db.users.update('login', session['login'], 'login', request.form['login'])
        session['login'] = request.form['login']
        data = db.users.get('login', session['login'])

        send_email.edit(request.form['last_name'], request.form['first_name'], request.form['middle_name'],
                        request.form['university'], request.form['login'], request.form['password'])
        return render_template('edit.html', message='Ваши изменения сохранены!', data=data, check_login=check_login)

    if check_if_admin():
        return render_template('edit.html', data=data, check_login=check_login, admin=1)
    else:
        return render_template('edit.html', data=data, check_login=check_login)


@app.route("/submit/", methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        print(request.files)
        current_user = db.users.get('login', session['login'])
        if 'file' not in request.files:
            return render_template('submit.html', message='Загрузите файл!')

        file = request.files['file']
        if file.filename == '':
            return render_template('submit.html', message='Загрузите файл!')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            db.submit.put({'theme': 'theme', 'filename': filename, 'file': file.read()})
            # file.save(os.path.join(app.config['UPLOAD_FOLDER']), filename)
            return render_template('submit.html', message='Успешно загружено')
        return render_template('submit.html', message='Неверный формат файла')
    return render_template('submit.html')


@app.route('/download/<upload_id>')
def download(upload_id):
    upload = db.submit.get('id', upload_id)
    return send_file(BytesIO(upload.file), download_name=upload.filename, as_attachment=True)


@app.route('/events/<event>')
def event(event):
    return render_template(f'events/{event}.html')


@app.route("/logout/")
@login_required
def logout():
    global check_login
    check_login = 0
    logout_user()
    session.pop('login', None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run()
