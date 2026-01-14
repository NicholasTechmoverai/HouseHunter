import random
import os
import smtplib
import datetime as datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# from config import Config, WEB_SERVER
WEB_SERVER=""

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))


async def send_email(
    recipient_email: str, html_content: str, subject: str = "Verification Code"
) -> bool:
    """
    Sends a verification email with HTML content to the specified recipient.

    Args:
        recipient_email (str): The recipient's email address.
        html_content (str): The HTML message body to send.

    Returns:
        bool: True if the email was sent successfully.

    Raises:
        ValueError: If the email or message is invalid.
        smtplib.SMTPException: For SMTP-related errors.
        Exception: For any other unexpected issues.
    """
    if not recipient_email or "@" not in recipient_email:
        raise ValueError("Invalid recipient email address.")

    if not html_content:
        raise ValueError("Email message content cannot be empty.")

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, recipient_email, msg.as_string())

        return True

    except smtplib.SMTPException as smtp_err:
        print(f"[SMTP Error] {smtp_err}")
        raise
    except Exception as ex:
        print(f"[Unexpected Error] {ex}")
        raise

# import asyncio
# res = asyncio.run(send_email("techmoversai@gmail.com","<p>hello</p>"))
# print(res)


# usagge
# html_message = form_email_message(code_template.format(code="123456"))

# # Or with a link
# html_message = form_email_message(verify_link_template.format(link="https://example.com/verify?token=abc123"))

