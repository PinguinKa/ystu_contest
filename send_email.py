import smtplib
from email.mime.text import MIMEText


sender = "pinguink.in.box@gmail.com"
password = 'ltnsekkthdwzywcc'
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(sender, password)


def registration(recipient, user_password):
    with open("templates/emails/registration.html", encoding='utf-8') as file:
        template = file.read()

    template = template.replace('{{ login }}', recipient)
    template = template.replace('{{ password }}', user_password)

    msg = (MIMEText(template, "html"))
    msg["From"] = "Конкурсный портал ЯГТУ"
    msg["To"] = recipient
    msg["Subject"] = "Регистрация на конкурсном портале ЯГТУ"
    server.sendmail(sender, recipient, msg.as_string())


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
    msg["From"] = "Конкурсный портал ЯГТУ"
    msg["To"] = recipient
    msg["Subject"] = "Изменение данных учётной записи"
    server.sendmail(sender, recipient, msg.as_string())


def participation(recipient, event):
    with open("templates/emails/participation.html", encoding='utf-8') as file:
        template = file.read()

    template = template.replace('{{ login }}', recipient)
    template = template.replace('{{ event }}', event)

    msg = (MIMEText(template, "html"))
    msg["From"] = "Конкурсный портал ЯГТУ"
    msg["To"] = recipient
    msg["Subject"] = f"Вы зарегистрированы на мероприятие {0}".format(event)
    server.sendmail(sender, recipient, msg.as_string())
