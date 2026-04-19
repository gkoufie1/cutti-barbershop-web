from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from .models import db, Admin, Booking
from .notifications import send_booking_confirmation

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password.')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    week_end = today + timedelta(days=7)
    bookings = (
        Booking.query
        .filter(Booking.date >= today, Booking.date <= week_end)
        .filter(Booking.status.notin_(['cancelled']))
        .order_by(Booking.date, Booking.time_slot)
        .all()
    )
    pending_count   = sum(1 for b in bookings if b.status == 'pending')
    confirmed_count = sum(1 for b in bookings if b.status == 'confirmed')
    return render_template(
        'admin/dashboard.html',
        bookings=bookings,
        today=today,
        pending_count=pending_count,
        confirmed_count=confirmed_count,
    )


@admin_bp.route('/bookings/<int:booking_id>/confirm', methods=['POST'])
@login_required
def confirm(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    booking.status = 'confirmed'
    db.session.commit()
    send_booking_confirmation(booking)
    flash(f'Booking for {booking.name} confirmed — confirmation sent.')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/bookings/<int:booking_id>/complete', methods=['POST'])
@login_required
def complete(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    booking.status = 'completed'
    db.session.commit()
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    booking.status = 'cancelled'
    db.session.commit()
    flash(f'Booking for {booking.name} cancelled.')
    return redirect(url_for('admin.dashboard'))
