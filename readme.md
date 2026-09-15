# Wasaya

> A safety check-in system designed around a simple question: **"Are you still here?"**

Wasaya allows a user to configure periodic check-ins. If the user stops responding and the configured grace period expires, Wasaya stops the check-in cycle and can notify selected emergency contacts.

The project started as a backend MVP and evolved into a full application with a production-oriented infrastructure and deployment workflow.

---

## How Wasaya Works

The core lifecycle is:

```text
User configures check-in
        ↓
Wasaya sends a check-in
        ↓
User responds
        ↓
Next check-in is scheduled
```

If the user does not respond:

```text
Check-in sent
      ↓
Grace period expires
      ↓
Check-in EXPIRED
      ↓
Emergency contacts notified
      ↓
Check-in cycle stops
```

The schedule is controlled by:

* **Check-in interval** — how often Wasaya asks
* **Check-in time** — the user's local starting time
* **Timezone** — timezone used for the schedule
* **Grace period** — how long an unanswered check-in remains valid
* **Emergency contacts** — people who can receive an alert

---

## V1

The first version focuses on the complete check-in lifecycle rather than trying to implement every future Wasaya feature.

V1 includes:

* User registration and email verification
* Authentication using JWT stored in an HTTP-only cookie
* User check-in settings
* Timezone-aware scheduling
* Periodic check-in emails
* Check-in confirmation
* Grace-period expiration
* Emergency contact management
* Automatic alert emails
* Persistent scheduling state
* Docker-based local development
* AWS infrastructure
* Terraform infrastructure as code
* Ansible server provisioning
* GitLab-based application delivery

The detailed V1 behavior and implementation are documented in:

**[`docs/mvp-v1.1.md`](docs/mvp-v1.md)**

---

## Architecture

At the application level, Wasaya follows a layered structure:

```text
API
 ↓
Services
 ↓
Repositories
 ↓
Database
```

The backend is built with:

* **FastAPI**
* **SQLAlchemy 2.0**
* **MySQL**
* **Alembic**
* **Pydantic**

The main domain components are:

```text
User
 ├── UserSettings
 ├── EmergencyContacts
 └── CheckinEvents
```

The scheduler is responsible for creating check-ins and processing expired events.

Notification delivery is handled separately from the scheduling logic.

---

## Infrastructure

Wasaya's infrastructure is built around AWS.

```text
                    Internet
                       │
                       ↓
                  Cloudflare
                       │
                       ↓
                      ALB
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
        Frontend              Backend
                                │
                                ↓
                               RDS
                               
                         S3 ← Media
```

The infrastructure includes:

* VPC and networking
* Application Load Balancer
* EC2 / Auto Scaling
* RDS MySQL
* S3
* IAM
* AWS Systems Manager
* Cloudflare / DNS

Infrastructure is defined with **Terraform**, while server-level configuration is handled with **Ansible**.

More details:

**[`docs/infrastructure.md`](docs/infrastructure.md)**

---

## Development

### Requirements

* Python 3.12+
* MySQL
* Docker / Docker Compose

### Run locally

Clone the repository:

```bash
git clone <repository-url>
cd wasaya
```

Create the environment file:

```bash
cp .env.example .env
```

Configure the database, SMTP settings, and application secrets.

Then run:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

---

## API

Main API areas:

| Area        | Purpose                                         |
| ----------- | ----------------------------------------------- |
| `/auth`     | Registration, login, logout, email verification |
| `/settings` | Check-in configuration                          |
| `/contacts` | Emergency contacts                              |
| `/checkin`  | Check-in confirmation                           |

Swagger provides the complete interactive API documentation.

---

## Repository Structure

```text
wasaya/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── scheduler/
│   └── main.py
│
├── alembic/
├── ansible/
├── terraform/
├── docs/
│   ├── mvp-v1.md
│   └── infrastructure.md
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Engineering Approach

Wasaya was built incrementally.

The infrastructure and application were not designed once and left unchanged. They evolved as real problems appeared during development, deployment, scheduling, and testing.

Some of the important principles that shaped the project are:

* Keep scheduling state explicit.
* Separate scheduling from user activity.
* Separate expiration from notification delivery.
* Keep development isolated from production.
* Use infrastructure as code instead of relying on manual infrastructure.
* Separate infrastructure provisioning from server configuration.
* Build and run the application as containers.
* Keep application configuration and secrets outside the image.

The important engineering decisions and problems encountered during development are documented in the project history and source code rather than turning the README into a technical manual.

---

## Project Status

**MVP V1 — Completed**

The core Wasaya check-in lifecycle is implemented and tested:

```text
Signup
  ↓
Email Verification
  ↓
Login
  ↓
Configure Check-in
  ↓
Scheduled Check-in
  ↓
User Response
  ↓
Next Check-in
```

And the failure path:

```text
Scheduled Check-in
        ↓
No Response
        ↓
Grace Period Expires
        ↓
Alert Emergency Contacts
        ↓
Stop Check-in Cycle
```

Future versions can build on this foundation with additional Wasaya features.

---

## Documentation

* **[MVP V1](docs/mvp-v1.1.md)** — What Wasaya V1 does and how the core system works.
* **[Infrastructure](docs/infrastructure.md)** — AWS infrastructure, Terraform, Ansible, networking, and deployment environment.

---

## License

This project is currently under development.
