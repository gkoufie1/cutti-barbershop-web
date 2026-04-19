import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

    # Database
    SQLALCHEMY_DATABASE_URI    = os.environ.get('DATABASE_URL', 'postgresql://cuttiworld:password@db:5432/cuttiworld')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail
    MAIL_SERVER         = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT           = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS        = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')

    BOOKING_EMAIL = os.environ.get('BOOKING_EMAIL', 'bookings@cuttiworld.com')

    # Stripe
    STRIPE_SECRET_KEY      = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET  = os.environ.get('STRIPE_WEBHOOK_SECRET')
    STRIPE_DEPOSIT_CENTS   = int(os.environ.get('STRIPE_DEPOSIT_CENTS', 1000))  # $10.00

    # Twilio
    TWILIO_ACCOUNT_SID  = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN   = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
