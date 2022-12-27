import smtplib
import mimetypes
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from ystu_db import db
import time


sender_name = "Кафедра иностранных языков ЯГТУ"

def _send(recipient, msg):
    sender = "inyaz.731@gmail.com"
    password = 'smmognwylaclzpbj'

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())


def rewarding(recipient, last_name, event, theme):
    with open("templates/emails/rewarding.html", encoding='utf-8') as file:
        template = file.read()
        
    template = template.replace('{{ login }}', recipient)
    template = template.replace('{{ event }}', event)
    template = template.replace('{{ theme }}', theme)
        
    msg = MIMEMultipart()
    msg.attach(MIMEText(template, "html"))
    msg["From"] = sender_name
    msg["To"] = recipient
    msg["Subject"] = f'Сертификат участника конкурса реферативного перевода и видеопрезентаций'
    
    filename = 'Сертификат.pdf'
    
    file =  f"Сертификат {last_name}.pdf"
    ftype, encoding = mimetypes.guess_type(file)
    file_type, subtype = ftype.split("/")
    
    try:
        with open(f"certificates/{event}/{theme}/Сертификат {last_name}.pdf", "rb") as f:
            file = MIMEBase(file_type, subtype)
            file.set_payload(f.read())
            encoders.encode_base64(file)
    except:
        print(f'Не доставлен сертификат на почту {recipient}. Конкурс "{event}", Номинация "{theme}"')
        return
        
    file.add_header('content-disposition', 'attachment', filename=filename)
    msg.attach(file)
    _send(recipient, msg)
    
    
participants = db.rating.get_all()
for participant in participants:
    rewarding(participant.login, participant.last_name, participant.event, participant.theme)
    time.sleep(2)
