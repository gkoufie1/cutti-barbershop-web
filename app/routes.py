import datetime
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_mail import Message
from . import mail

main = Blueprint('main', __name__)

PRODUCTS = [
    {'id': 1, 'name': 'Silk Oxford Shirt',   'category': 'Shirts',       'desc': 'Premium Egyptian cotton with a silk finish. Italian collar, French cuffs.',              'price': 185, 'emoji': '👔', 'badge': 'New'},
    {'id': 2, 'name': 'Linen Trousers',       'category': 'Bottoms',      'desc': 'Slim-cut European linen. Breathable, refined, and effortlessly timeless.',               'price': 210, 'emoji': '👖', 'badge': None},
    {'id': 3, 'name': 'Cashmere Turtleneck',  'category': 'Knitwear',     'desc': 'Grade-A Mongolian cashmere. Soft, warm, and impeccably structured.',                    'price': 320, 'emoji': '🧥', 'badge': 'Bestseller'},
    {'id': 4, 'name': 'Merino Wool Blazer',   'category': 'Outerwear',    'desc': 'Single-breasted Italian merino. Peak lapels, half-lined, unstructured shoulder.',       'price': 485, 'emoji': '🥼', 'badge': None},
    {'id': 5, 'name': 'Suede Chelsea Boots',  'category': 'Footwear',     'desc': 'Hand-stitched Spanish suede with crepe sole. Rich tobacco brown.',                      'price': 380, 'emoji': '👞', 'badge': 'Limited'},
    {'id': 6, 'name': 'Silk Pocket Square',   'category': 'Accessories',  'desc': 'Hand-rolled edges, 100% mulberry silk. Classic paisley weave.',                        'price': 65,  'emoji': '🎀', 'badge': None},
]


@main.route('/')
def index():
    return render_template('index.html', products=PRODUCTS, year=datetime.date.today().year)


@main.route('/book', methods=['POST'])
def book():
    data    = request.get_json(silent=True) or {}
    name    = data.get('name',    '').strip()
    phone   = data.get('phone',   '').strip()
    service = data.get('service', '').strip()
    date    = data.get('date',    '').strip()
    time    = data.get('time',    '').strip()

    if not all([name, phone, service, date, time]):
        return jsonify({'success': False, 'error': 'All fields are required.'}), 400

    booking_email = current_app.config['BOOKING_EMAIL']

    try:
        msg = Message(
            subject=f"Booking Request — {service.split(' —')[0]} on {date}",
            recipients=[booking_email],
            body=(
                f'New booking request:\n\n'
                f'Name:    {name}\n'
                f'Phone:   {phone}\n'
                f'Service: {service}\n'
                f'Date:    {date}\n'
                f'Time:    {time}\n'
            ),
        )
        mail.send(msg)
    except Exception as exc:
        current_app.logger.error('Email send failed: %s', exc)
        return jsonify({'success': False, 'error': 'Could not send confirmation. Please call us directly.'}), 500

    return jsonify({'success': True})
