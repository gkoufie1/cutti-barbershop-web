from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class Booking(db.Model):
    __tablename__ = 'bookings'

    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(100), nullable=False)
    phone            = db.Column(db.String(30),  nullable=False)
    email            = db.Column(db.String(120), nullable=False)
    service          = db.Column(db.String(100), nullable=False)
    date             = db.Column(db.Date,        nullable=False)
    time_slot        = db.Column(db.String(20),  nullable=False)
    status           = db.Column(db.String(20),  nullable=False, default='pending')
    stripe_session_id = db.Column(db.String(200), nullable=True)
    deposit_paid     = db.Column(db.Boolean,     nullable=False, default=False)
    created_at       = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    # Prevent double-booking the same slot on the same day
    __table_args__ = (
        db.UniqueConstraint('date', 'time_slot', name='uq_date_slot'),
    )

    def __repr__(self):
        return f'<Booking {self.id} {self.name} {self.date} {self.time_slot}>'


class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'

    id            = db.Column(db.Integer,    primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'
