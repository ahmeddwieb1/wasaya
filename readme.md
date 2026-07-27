# Wasaya — Backend MVP

A safety and check-in system built with FastAPI + SQLAlchemy 2.0 + MySQL.

---

## Project Structure

```
wasaya/
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── ansible/
│   ├── elwasaya/
│   │   └── defaults/
│   │       └── main.yml
│   │   └──  files/
│   │       ├── docker-compose.yml
│   │       └── nginx.conf
│   │   ├── handlers/
│   │       └── main.yml
│   │   ├── meta/
│   │       └── main.yml
│   │   ├── tasks/
│   │       └── main.yml
│   │   ├── templates/
│   │   ├── tests/
│   │       ├── inventory
│   │       └── test.yml
│   │   └── vars/
│   │       └── main.yml
│   ├── hosts.ini
│   └── playbook1
│   
├── terraform/
│   ├── ec2.tf
│   ├── rtb.tf
│   ├── sg.tf
│   ├── vpc.tf
│   └── cloudwatch.tf
│   
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── dashboard.py
│   │       ├── settings.py
│   │       ├── contacts.py
│   │       └── checkin.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── dependencies.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── session.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── user_settings.py
│   │   ├── emergency_contact.py
│   │   ├── checkin_event.py
│   │   └── verification_token.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── settings.py
│   │   ├── contacts.py
│   │   └── checkin.py
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── settings_repository.py
│   │   ├── contact_repository.py
│   │   ├── checkin_repository.py
│   │   └── token_repository.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── checkin_service.py
│   │   └── notifications_service.py
│   │
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── jobs.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── tokens.py
│   │
│   └── main.py
│
├── .env.example
├── alembic.ini
├── requirements.txt
├── README.md
├── Dockerfile
├── docker-compose.yml
└── .gitignore
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
# aiomysql is required for async SQLAlchemy with MySQL
pip install aiomysql
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your DB credentials, SMTP settings, and SECRET_KEY
```

### 3. Create the database

```sql
CREATE DATABASE wasaya CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Run migrations

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

API docs available at: http://localhost:8000/docs

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/v1/auth/signup | — | Create account |
| POST | /api/v1/auth/login | — | Login, sets cookie |
| POST | /api/v1/auth/logout | — | Clears cookie |
| GET | /api/v1/auth/me | ✓ | Current user |
| GET | /api/v1/auth/verify-email?token= | — | Verify email |
| PUT | /api/v1/settings | ✓ | Update check-in settings |
| POST | /api/v1/contacts | ✓ | Add emergency contact |
| GET | /api/v1/contacts | ✓ | List emergency contacts |
| DELETE | /api/v1/contacts/{id} | ✓ | Remove emergency contact |
| GET | /api/v1/checkin/confirm?token= | — | Confirm check-in |

---

## Check-in Flow

1. **Scheduler** (`_send_checkins_job`) runs every hour
2. For each eligible user (interval elapsed, no pending event), it creates a `CheckinEvent` with `status=PENDING` and emails a confirmation link
3. User clicks the link → `GET /api/v1/checkin/confirm?token=...`
4. Token is validated → event marked `RESPONDED`, `User.last_seen_at` updated

**Expiry flow** (`_expire_checkins_job`) runs every 15 minutes:
1. Finds `PENDING` events where `expires_at` has passed
2. Marks them `EXPIRED`
3. Sends alert emails to all active emergency contacts
4. Marks them `ALERTED`

---

## Authentication

- JWT stored in HTTP-only cookie as `Bearer <token>`
- 24-hour expiry (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- No refresh tokens

---

## Notes

- Add `aiomysql` to your environment — it's the async MySQL driver used by SQLAlchemy 2.0
- For Gmail SMTP: use an [App Password](https://myaccount.google.com/apppasswords), not your main password
- `SECRET_KEY` should be a long random string — generate one with `openssl rand -hex 32`