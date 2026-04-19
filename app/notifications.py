from flask import current_app, render_template
from flask_mail import Message
from . import mail


def send_booking_confirmation(booking):
    _send_email(booking)
    _send_sms(booking)


def _send_email(booking):
    try:
        msg = Message(
            subject='Your CuttiWorld Appointment is Confirmed ✂️',
            recipients=[booking.email],
            html=render_template('emails/confirmation.html', booking=booking),
        )
        mail.send(msg)
    except Exception as exc:
        current_app.logger.error('Confirmation email failed: %s', exc)


def _send_sms(booking):
    sid   = current_app.config.get('TWILIO_ACCOUNT_SID')
    token = current_app.config.get('TWILIO_AUTH_TOKEN')
    from_ = current_app.config.get('TWILIO_PHONE_NUMBER')
    if not all([sid, token, from_]):
        return
    try:
        from twilio.rest import Client
        service_name = booking.service.split(' —')[0]
        body = (
            f"Hi {booking.name}! Your {service_name} at CuttiWorld is confirmed "
            f"for {booking.date.strftime('%A, %B %d')} at {booking.time_slot}. "
            f"See you then! ✂️"
        )
        Client(sid, token).messages.create(body=body, from_=from_, to=booking.phone)
    except Exception as exc:
        current_app.logger.error('SMS failed: %s', exc)
