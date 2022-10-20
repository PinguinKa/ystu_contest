import smtplib
from flask import Flask, render_template
from email.mime.text import MIMEText
from email.message import EmailMessage


def send_email(recipient, user_password):
    sender = "pinguink.in.box@gmail.com"
    password = 'ltnsekkthdwzywcc'

    try:
        with open("templates/email_message.html", encoding='utf-8') as file:
            template = file.read().replace('{{ login }}', recipient).replace('{{ password }}', user_password)

    except IOError:
        return "The template file doesn't found!"

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(sender, password)
    msg = (MIMEText(template, "html"))
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = "Описание"
    server.sendmail(sender, recipient, msg.as_string())

    return "The message was sent successfully!"

print(send_email('k.melnikova@kodland.team', '123456789'))