# CuttiWorld Barbershop

A full-stack booking and e-commerce web application for a luxury barber studio. Built with Flask, PostgreSQL, Stripe payments, and deployed to AWS EC2 via a fully automated GitHub Actions CI/CD pipeline.

---

## Features

- **Online booking** — customers pick a service, date, and time slot; real-time slot availability prevents double-bookings
- **Stripe deposit** — $10 deposit collected at booking via Stripe Checkout
- **Email & SMS confirmations** — automated booking confirmation via Gmail (Flask-Mail) and Twilio SMS
- **Shop / cart** — product listings with a client-side cart and checkout flow
- **Admin dashboard** — protected portal to view upcoming bookings and update their status (pending → confirmed → completed)
- **Zero-downtime deploys** — only the web container is restarted; the database and nginx stay up

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, Flask 3 |
| Database | PostgreSQL 16, SQLAlchemy, Flask-Migrate |
| Payments | Stripe Checkout |
| Notifications | Flask-Mail (Gmail), Twilio SMS |
| Web server | Gunicorn + nginx (reverse proxy) |
| Containerisation | Docker (multi-stage build), Docker Compose |
| CI/CD | GitHub Actions → GitHub Container Registry → AWS EC2 |

---

## Project Structure

```
├── app/
│   ├── __init__.py          # App factory, extensions, CLI commands
│   ├── config.py            # Environment-based configuration
│   ├── models.py            # Booking and Admin models
│   ├── routes.py            # Public routes (home, booking, Stripe webhook)
│   ├── admin.py             # Admin blueprint (/admin/*)
│   ├── notifications.py     # Email + SMS helpers
│   └── templates/
│       ├── index.html       # Main site (booking, shop, gallery)
│       ├── admin/           # Admin dashboard & login
│       └── emails/          # HTML email templates
├── migrations/              # Alembic migration files
├── Dockerfile               # Multi-stage production image
├── docker-compose.yml       # Local development stack
├── docker-compose.prod.yml  # Production stack (uses pre-built image)
├── nginx.conf               # Reverse proxy config
├── run.py                   # WSGI entry point
├── requirements.txt
└── .env.example             # Required environment variables
```

---

## Local Development

### Prerequisites

- Docker + Docker Compose
- Python 3.13 (optional, for running without Docker)

### 1. Clone and configure

```bash
git clone https://github.com/your-username/cuttiworld.git
cd cuttiworld
cp .env.example .env
# Edit .env with your real values
```

### 2. Start the stack

```bash
docker compose up --build
```

The app will be available at `http://localhost`.

### 3. Run migrations

```bash
docker compose exec web flask db upgrade
```

### 4. Create an admin account

```bash
docker compose exec web flask create-admin <username> <password>
```

Admin dashboard is at `http://localhost/admin`.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in all values.

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session secret — use a long random string |
| `DB_PASSWORD` | PostgreSQL password |
| `DATABASE_URL` | Full Postgres connection string |
| `MAIL_USERNAME` | Gmail address for sending confirmations |
| `MAIL_PASSWORD` | Gmail App Password (not your account password) |
| `BOOKING_EMAIL` | Address that receives booking notifications |
| `STRIPE_SECRET_KEY` | Stripe secret key (`sk_test_...` or `sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (`whsec_...`) |
| `STRIPE_DEPOSIT_CENTS` | Deposit amount in cents (e.g. `1000` = $10) |
| `TWILIO_ACCOUNT_SID` | Twilio account SID (optional) |
| `TWILIO_AUTH_TOKEN` | Twilio auth token (optional) |
| `TWILIO_PHONE_NUMBER` | Twilio sender number (optional) |

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yml`) runs on every push to `main`.

**Job 1 — Build & Push**
1. Builds the Docker image using a multi-stage build
2. Tags it with the commit SHA and `latest`
3. Pushes to GitHub Container Registry (`ghcr.io`)

**Job 2 — Deploy**
1. SSHs into the AWS EC2 server
2. Copies `docker-compose.prod.yml` and `nginx.conf` via SCP
3. Pulls the new image from the registry
4. Restarts the `web` container only (`--no-deps`)
5. Ensures `db` and `nginx` are running if they were stopped

### Required GitHub Secrets

| Secret | Value |
|---|---|
| `SERVER_HOST` | EC2 public IP address |
| `SERVER_USER` | SSH username (e.g. `ubuntu`) |
| `SERVER_SSH_KEY` | Full private key (`-----BEGIN ...`) |

---

## Production Server Setup

On a fresh Ubuntu EC2 instance:

```bash
# Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker ubuntu

# Create app directory and .env file
mkdir -p /opt/cuttiworld
nano /opt/cuttiworld/.env   # paste your production env vars
```

The pipeline handles all subsequent deploys automatically.

---

## Stripe Webhook

Register the following endpoint in your Stripe dashboard:

```
https://yourdomain.com/stripe/webhook
```

Select the event: `checkout.session.completed`

---

## License

Private — all rights reserved.
