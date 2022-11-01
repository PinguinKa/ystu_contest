import smtplib
from email.mime.text import MIMEText


sender_name = "Кафедра иностранных языков ЯГТУ"


def _send(recipient, msg):
    sender = "pinguink.in.box@gmail.com"
    password = 'ltnsekkthdwzywcc'

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())


def registration(recipient, user_password):
    with open("templates/emails/registration.html", encoding='utf-8') as file:
        template = file.read()

    template = template.replace('{{ login }}', recipient)
    template = template.replace('{{ password }}', user_password)

    msg = (MIMEText(template, "html"))
    msg["From"] = sender_name
    msg["To"] = recipient
    msg["Subject"] = "Регистрация на сайте кафедры иностранных языков ЯГТУ"

    _send(recipient, msg)


def edit(last_name, first_name, middle_name, university, recipient, user_password):
    with open("templates/emails/edit.html", encoding='utf-8') as file:
        template = file.read()

    template = template.replace('{{ last_name }}', last_name)
    template = template.replace('{{ first_name }}', first_name)
    template = template.replace('{{ middle_name }}', middle_name)
    template = template.replace('{{ university }}', university)
    template = template.replace('{{ login }}', recipient)
    template = template.replace('{{ password }}', user_password)

    msg = (MIMEText(template, "html"))
    msg["From"] = sender_name
    msg["To"] = recipient
    msg["Subject"] = "Изменение данных учётной записи"

    _send(recipient, msg)


def participation(recipient, event, theme, id):
    with open("templates/emails/participation.html", encoding='utf-8') as file:
        template = file.read()

    template = template.replace('{{ login }}', recipient)
    template = template.replace('{{ event }}', event)
    template = template.replace('{{ theme }}', theme)
    template = template.replace('{{ id }}', id)

    msg = (MIMEText(template, "html"))
    msg["From"] = sender_name
    msg["To"] = recipient
    msg["Subject"] = f'Спасибо за участие в мероприятии "{event}"'

    _send(recipient, msg)
