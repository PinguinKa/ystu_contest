import re
import bcrypt
from kodland_db import db
from random import randint
from datetime import datetime, timedelta
from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user


def hashed_password(plain_text_password):
    # Мы добавляем "соль" к нашему пароль, чтобы сделать его декодирование невозможным
    return bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    return bcrypt.checkpw(plain_text_password.encode('utf-8'), hashed_password)


app = Flask(__name__)

all_orders = []

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
            return render_template('register.html', message='Пороли не совпадают')
        data = dict(request.form)
        data.pop('password_check')
        db.users.put(data=data)
        return render_template('register.html', message='Регистрация прошла успешно')
    return render_template('register.html')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/info/')
def info():
    return render_template('info.html')


@app.route('/events/')
def events():
    return render_template('events.html')


# main.py
@app.route('/products/', methods=['GET', 'POST'])
def products():
    if request.method == 'POST':
        item_id = request.form['item_id']
        row = db.cart.get('item_id', item_id)
        if not row:
            data = {'item_id': item_id, 'amount': 1}
            db.cart.put(data)
        else:
            data = {'item_id': item_id, 'amount': row.amount + 1}
            db.cart.delete('item_id', item_id)
            db.cart.put(data)

    data = db.items.get_all()
    for row in data:
        res = db.cart.get('item_id', row.id)
        if res:
            row.amount = res.amount
        else:
            row.amount = 0
    return render_template('products.html', data=data)


@app.route('/cart/')
@login_required
def cart():
    data = db.cart.get_all()
    total_sum = 0
    for row in data:
        item_row = db.items.get('id', row.item_id)
        row.name = item_row.name
        row.description = item_row.description
        row.price = item_row.price
        row.total = row.amount * item_row.price
        total_sum += row.total
    return render_template('cart.html', data=data, total_sum=total_sum)


@app.route('/contacts/')
@login_required
def contacts():
    return render_template('contacts.html')


@app.route('/about/')
@login_required
def about():
    return render_template('about.html')


@app.route('/product1/')
@login_required
def product1():
    end_date = datetime.now() + timedelta(days=7)
    end_date = end_date.strftime('%d.%m.%Y')
    return render_template('product1.html',
                           action_name='Весенние скидки!',
                           end_date=end_date,
                           lucky_num=randint(1, 5))


@app.route('/product2/')
@login_required
def product2():
    brands = ['Colla', 'Pepppssi', 'Orio', 'Macdak']
    return render_template('product2.html', brands=brands)


@app.route('/order/', methods=['GET', 'POST'])
@login_required
def order():
    if request.method == 'POST':
        for key in request.form:
            if request.form[key] == '':
                return render_template('order.html', error='Не все поля заполнены!')
            if key == 'email':
                if not re.match('\w+@\w+\.(ru|com)', request.form[key]):
                    return render_template('order.html', error='Неправильный формат почты')
            if key == 'phone_number':
                if not re.match('\+7\d{9}', request.form[key]):
                    return render_template('order.html', error='Неправильный формат номера телефона')

        cart_data = db.cart.get_all()
        order_data = db.orders.get_all()

        id_ = order_data[-1].id + 1 if order_data else 1
        for row in cart_data:
            item = {'id': id_, 'item_id': row.item_id, 'amount': row.amount}
            db.orders.put(item)

        for row in cart_data:
            db.cart.delete('item_id', row.item_id)

        payload = dict(request.form)
        payload['order_id'] = id_
        all_orders.append(payload)
        return redirect(url_for('cart'))

    return render_template('order.html')


@app.route('/api/orders/')
def api_orders():
    return jsonify(all_orders)


@app.route('/order_list/')
@login_required
def order_list():
    return render_template('order_list.html')


# main.py
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        row = db.users.get('login', request.form['login'])
        if not row:
            return render_template('login.html', error='Неправильный логин или пароль')

        if request.form['password'] == row.password:
            user = User(login)  # Создаем пользователя
            login_user(user)  # Логинем пользователя
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неправильный логин или пароль')
    return render_template('login.html')


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return 'Пока'


@app.route('/lootbox/')
@login_required
def lootbox():
    num = randint(1, 100)
    if num < 50:
        chance = 50
    elif 50 < num < 95:
        chance = 45
    elif 95 < num < 99:
        chance = 4
    else:
        chance = 1
    return render_template('lootbox.html', chance=chance)


if __name__ == "__main__":
    app.run(debug=True)
