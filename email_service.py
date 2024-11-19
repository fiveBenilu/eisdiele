import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv
import threading
import smtpd
import asyncore

# Laden Sie die Umgebungsvariablen aus der .env-Datei
load_dotenv()

def send_invoice_email(to_email, invoice_path):
    from_email = os.getenv('EMAIL_USER')
    subject = "Ihre Rechnung"
    body = "Bitte finden Sie die angehängte Rechnung."

    # Debugging-Informationen
    print(f"Sending email from {from_email} to {to_email}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print(f"Attachment: {invoice_path}")

    # Erstellen Sie die E-Mail-Nachricht
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Fügen Sie die PDF-Rechnung als Anhang hinzu
    with open(invoice_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(invoice_path)}")
        msg.attach(part)

    # Senden Sie die E-Mail über den lokalen SMTP-Server
    server = smtplib.SMTP('localhost', 1026)
    server.set_debuglevel(1)  # Aktivieren Sie die Debugging-Ausgabe
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()

def start_smtp_server():
    server = smtpd.DebuggingServer(('localhost', 1026), None)
    asyncore.loop()

# Starten Sie den lokalen SMTP-Server in einem separaten Thread
smtp_thread = threading.Thread(target=start_smtp_server)
smtp_thread.start()