from fastapi_mail import FastMail, MessageSchema  # type: ignore

from app.settings import settings


async def send_email(email, password: str):
    message = MessageSchema(
        subject="Account credentials",
        recipients=[email],
        body=f"Your account has been created.\n\nEmail: "
        f"{email}\nPassword: {password}\n\nPlease keep these credentials safe.",
        subtype="plain",
    )
    fm = FastMail(settings.mail_conf)
    await fm.send_message(message)
