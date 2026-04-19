import datetime
import stripe
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from .models import db, Booking
from .notifications import send_booking_confirmation

main = Blueprint('main', __name__)

_INDEX = 'main.index'

PRODUCTS = [
    {'id': 1, 'name': 'Silk Oxford Shirt',  'category': 'Shirts',      'desc': 'Premium Egyptian cotton with a silk finish. Italian collar, French cuffs.',        'price': 185, 'emoji': '👔', 'badge': 'New'},
    {'id': 2, 'name': 'Linen Trousers',      'category': 'Bottoms',     'desc': 'Slim-cut European linen. Breathable, refined, and effortlessly timeless.',         'price': 210, 'emoji': '👖', 'badge': None},
    {'id': 3, 'name': 'Cashmere Turtleneck', 'category': 'Knitwear',    'desc': 'Grade-A Mongolian cashmere. Soft, warm, and impeccably structured.',              'price': 320, 'emoji': '🧥', 'badge': 'Bestseller'},
    {'id': 4, 'name': 'Merino Wool Blazer',  'category': 'Outerwear',   'desc': 'Single-breasted Italian merino. Peak lapels, half-lined, unstructured shoulder.', 'price': 485, 'emoji': '🥼', 'badge': None},
    {'id': 5, 'name': 'Suede Chelsea Boots', 'category': 'Footwear',    'desc': 'Hand-stitched Spanish suede with crepe sole. Rich tobacco brown.',                'price': 380, 'emoji': '👞', 'badge': 'Limited'},
    {'id': 6, 'name': 'Silk Pocket Square',  'category': 'Accessories', 'desc': 'Hand-rolled edges, 100% mulberry silk. Classic paisley weave.',                  'price': 65,  'emoji': '🎀', 'badge': None},
]


@main.route('/', methods=['GET'])
def index():
    return render_template('index.html', products=PRODUCTS, year=datetime.date.today().year)


# ── SLOTS ─────────────────────────────────────────────
@main.route('/slots', methods=['GET'])
def slots():
    date_str = request.args.get('date', '')
    try:
        selected_date = datetime.date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'invalid date — use YYYY-MM-DD'}), 400

    taken = {
        b.time_slot for b in Booking.query.filter(
            Booking.date == selected_date,
            Booking.status.notin_(['cancelled']),
        ).all()
    }
    return jsonify({'taken': list(taken)})


# ── BOOKING ───────────────────────────────────────────
@main.route('/book', methods=['POST'])
def book():
    data     = request.get_json(silent=True) or {}
    name     = data.get('name',    '').strip()
    phone    = data.get('phone',   '').strip()
    email    = data.get('email',   '').strip()
    service  = data.get('service', '').strip()
    date_str = data.get('date',    '').strip()
    time_slot = data.get('time',   '').strip()

    if not all([name, phone, email, service, date_str, time_slot]):
        return jsonify({'success': False, 'error': 'All fields are required.'}), 400

    try:
        booking_date = datetime.date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date.'}), 400

    # Verify slot is still free
    clash = Booking.query.filter(
        Booking.date == booking_date,
        Booking.time_slot == time_slot,
        Booking.status.notin_(['cancelled']),
    ).first()
    if clash:
        return jsonify({'success': False, 'error': 'That slot was just taken — please choose another time.'}), 409

    # Create a pending booking (confirmed after payment)
    booking = Booking(
        name=name, phone=phone, email=email,
        service=service, date=booking_date, time_slot=time_slot,
        status='pending',
    )
    db.session.add(booking)
    db.session.commit()

    # Create Stripe Checkout Session
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    deposit_cents  = current_app.config['STRIPE_DEPOSIT_CENTS']
    service_name   = service.split(' —')[0]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': f'Deposit — {service_name}'},
                    'unit_amount': deposit_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('main.booking_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for(_INDEX, _external=True) + '#booking',
            metadata={'booking_id': booking.id},
            customer_email=email,
        )
        booking.stripe_session_id = session.id
        db.session.commit()
        return jsonify({'success': True, 'checkout_url': session.url})
    except Exception as exc:
        current_app.logger.error('Stripe session creation failed: %s', exc)
        db.session.delete(booking)
        db.session.commit()
        return jsonify({'success': False, 'error': 'Payment setup failed. Please try again.'}), 500


@main.route('/booking/success', methods=['GET'])
def booking_success():
    session_id = request.args.get('session_id', '')
    if not session_id:
        return redirect(url_for(_INDEX))

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            booking_id = int(session.metadata.get('booking_id', 0))
            booking = db.session.get(Booking, booking_id)
            if booking and not booking.deposit_paid:
                booking.deposit_paid = True
                booking.status = 'confirmed'
                db.session.commit()
                send_booking_confirmation(booking)
    except Exception as exc:
        current_app.logger.error('Booking success verification failed: %s', exc)

    return redirect(url_for(_INDEX) + '?booked=1#booking')


# ── STRIPE WEBHOOK ────────────────────────────────────
# Handles payment events server-to-server (more reliable than the redirect)
@main.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload    = request.get_data()
    sig_header = request.headers.get('Stripe-Signature', '')
    secret     = current_app.config.get('STRIPE_WEBHOOK_SECRET', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return '', 400

    if event['type'] == 'checkout.session.completed':
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        s          = event['data']['object']
        booking_id = int(s['metadata'].get('booking_id', 0))
        booking    = db.session.get(Booking, booking_id)
        if booking and not booking.deposit_paid:
            booking.deposit_paid = True
            booking.status = 'confirmed'
            db.session.commit()
            send_booking_confirmation(booking)

    return '', 200
