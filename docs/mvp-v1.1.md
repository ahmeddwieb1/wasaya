# Wasaya — MVP V1

## 1. What is Wasaya?

Wasaya is a safety check-in platform designed around a simple idea:

> A user periodically confirms that they are okay. If they stop responding,
> Wasaya can notify people they trust.

The system allows a user to define how often they want to be checked on,
when the initial check-in should happen, their timezone, and who should be
contacted if they do not respond.

The MVP focuses on building the complete check-in lifecycle from user
registration to emergency notification.

---

## 2. V1 Goal

The goal of V1 is to prove the core Wasaya workflow end-to-end.

A user should be able to:

1. Create an account.
2. Verify their email.
3. Configure their check-in schedule.
4. Add emergency contacts.
5. Receive periodic check-in emails.
6. Confirm that they are okay.
7. Miss a check-in.
8. Allow the grace period to expire.
9. Trigger an alert to their emergency contacts.
10. Stop the check-in cycle after an unanswered check-in.

V1 is therefore considered complete when the complete check-in lifecycle
works reliably from scheduling through alerting.

---

## 3. Core User Flow

```mermaid
flowchart TD
    A[Create Account]
    B[Verify Email]
    C[Configure Settings]
    D[Add Emergency Contacts]
    E[Wait for Scheduled Check-in]
    F[Receive Check-in]
    G{User Responds?}
    H[Check-in Responded]
    I[Grace Period Expires]
    J[Alert Emergency Contacts]
    K[Stop Check-in Cycle]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G -->|Yes| H
    G -->|No| I
    I --> J
    J --> K
````

The important distinction is that responding to a check-in does not reset the
schedule. The schedule continues according to the configured interval.

---

## 4. Check-in Lifecycle

Each scheduled check-in is represented by a `CheckinEvent`.

The lifecycle is:

```text
PENDING
   │
   ├── User responds
   │       ↓
   │   RESPONDED
   │
   └── Grace period expires
           ↓
        EXPIRED
           ↓
        ALERTED
           ↓
   Check-in cycle stopped
```

### PENDING

A check-in becomes `PENDING` when the scheduler sends a check-in to the user.

The event records:

* `sent_at`
* `expires_at`
* `channel`
* `status`

A confirmation token is also created for the user.

### RESPONDED

When the user confirms the check-in:

* The confirmation token is validated.
* The token is consumed.
* The pending event becomes `RESPONDED`.
* `responded_at` is recorded.
* `last_seen_at` is updated.

The user's schedule is not changed.

### EXPIRED

If the user does not respond before `expires_at`, the scheduler marks the
pending event as `EXPIRED`.

The expiration is based on the check-in's grace period.

### ALERTED

After expiration, Wasaya:

1. Stops the user's check-in cycle.
2. Checks whether automatic alerts are enabled.
3. Sends an email to active emergency contacts that have an email address.
4. Marks the event as `ALERTED`.

The check-in cycle does not continue indefinitely after an unanswered
check-in.

---

## 5. Scheduling Model

Scheduling is based on `next_checkin_at`.

`next_checkin_at` is the authoritative state used by the scheduler to decide
when the next check-in should be sent.

### Initial Schedule

The user provides:

* `checkin_time`
* `timezone`

Wasaya converts the local check-in time into a UTC timestamp and stores it as
`next_checkin_at`.

For example:

```text
Timezone:            Africa/Cairo
Check-in time:       08:00

        ↓

next_checkin_at:     05:00 UTC
```

The exact UTC value depends on the timezone rules for that date.

### Recurring Schedule

After a check-in is successfully sent:

```text
next_checkin_at
        +
check_interval_hours
        ↓
new next_checkin_at
```

For example:

```text
Interval: 2 hours
Anchor:   08:00

08:00 → 10:00 → 12:00 → 14:00 → ...
```

For a 48-hour interval:

```text
Day 1 08:00
Day 3 08:00
Day 5 08:00
Day 7 08:00
```

### `last_seen_at`

`last_seen_at` represents the user's latest activity.

It is updated when the user responds to a check-in.

It is **not** used to calculate the next check-in.

This prevents the user's response time from accidentally shifting the
configured schedule.

---

## 6. Settings

Each user has one `UserSettings` record.

The main scheduling settings are:

| Setting                | Purpose                                               |
| ---------------------- | ----------------------------------------------------- |
| `check_interval_hours` | Time between scheduled check-ins                      |
| `checkin_time`         | Initial local time used as the schedule anchor        |
| `timezone`             | User timezone used when creating the initial schedule |
| `grace_period_hours`   | Time allowed for the user to respond                  |
| `next_checkin_at`      | Authoritative next scheduled check-in                 |
| `checkin_active`       | Determines whether future check-ins can be sent       |
| `preferred_channel`    | Stores the preferred notification channel             |
| `auto_alert_enabled`   | Enables/disables emergency alert emails               |

`legacy_enabled` is stored as part of the current settings model but does not
currently drive V1 behavior.

### Updating Schedule

Changing any of the following:

* `check_interval_hours`
* `checkin_time`
* `timezone`

rebuilds `next_checkin_at` and activates the check-in cycle.

The pause operation sets:

```text
checkin_active = false
```

---

## 7. Emergency Contacts

A user can configure emergency contacts who may be notified when a check-in
is missed.

Each contact can contain:

* Name
* Relation
* Email
* Phone
* Priority
* Active/inactive state

V1 uses email for emergency notifications.

Phone numbers are stored but are not used for notification delivery in V1.

Only active contacts with an email address are considered when sending an
emergency alert.

---

## 8. Notifications

V1 uses email as its notification channel.

There are three main email flows.

### Account Verification

After signup, the user receives an email containing a verification link.

```text
Signup
  ↓
Verification Token
  ↓
Email
  ↓
User verifies account
```

### Check-in

When the scheduled time is reached:

```text
Scheduler
   ↓
Create PENDING event
   ↓
Create confirmation token
   ↓
Send check-in email
```

The user can confirm directly through the check-in link.

### Emergency Alert

When the grace period expires:

```text
PENDING
   ↓
EXPIRED
   ↓
Find active emergency contacts
   ↓
Send alert emails
   ↓
ALERTED
```

---

## 9. Backend Architecture

Wasaya V1 is implemented as a FastAPI backend.

The backend follows a layered structure:

```text
API Routes
    ↓
Services
    ↓
Repositories
    ↓
Database
```

The scheduler uses the same services and repositories:

```text
                    ┌───────────────┐
                    │   FastAPI     │
                    │     API       │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Services    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Repositories  │
                    └───────┬───────┘
                            │
                            ▼
                       ┌────────┐
                       │ MySQL  │
                       └────────┘

                    ┌───────────────┐
                    │   Scheduler   │
                    └───────┬───────┘
                            │
                            ▼
                    Services / Repositories
```

The main backend components are:

* FastAPI
* SQLAlchemy
* MySQL
* APScheduler
* JWT authentication
* SMTP email delivery

---

## 10. Data Model

The core V1 entities are:

```text
User
 │
 ├── UserSettings
 ├── CheckinEvents
 ├── EmergencyContacts
 └── VerificationTokens
```
![ERD-image](docs/mermaid-diagram.png)
---

## 11. Authentication

V1 uses:

* Password hashing
* Email verification
* JWT authentication
* HTTP-only authentication cookies
* Protected API endpoints

Email verification and check-in confirmation use separate one-time tokens.

The check-in confirmation link does not require the user's authenticated
browser session because the confirmation token itself authorizes the action.

---

## 12. Scheduler

Wasaya uses APScheduler to execute background scheduling tasks.

V1 has two main scheduler jobs.

### Send Check-ins

The send job:

1. Finds active and verified users.
2. Loads their settings.
3. Checks `checkin_active`.
4. Checks `next_checkin_at`.
5. Skips users whose schedule is not due.
6. Skips users who already have a pending check-in.
7. Creates the check-in event.
8. Sends the check-in email.
9. Advances `next_checkin_at`.

### Expire Check-ins

The expiration job:

1. Finds expired `PENDING` events.
2. Changes them to `EXPIRED`.
3. Loads the user's settings.
4. Disables the check-in cycle.
5. Sends emergency alerts when enabled.
6. Changes the event to `ALERTED`.

The scheduler currently runs these jobs every minute, which is useful for local
testing and reduces the delay between a scheduled timestamp and job execution.

---

## 13. Local Development

The backend can be run locally using Docker Compose.

The development environment contains:

```text
Backend
   │
   ├── FastAPI
   │
   └── MySQL

Frontend
   │
   └── communicates with Backend

Email
   │
   └── SMTP / MailHog during local development
```

Database schema changes are managed through Alembic migrations.

The application is containerized using Docker.

---

## 14. Infrastructure & Deployment

V1 was also used as the foundation for the project's cloud infrastructure
and deployment workflow.

The infrastructure was designed around AWS services including:

* VPC
* Public and private subnets
* Application Load Balancer
* EC2
* Auto Scaling
* RDS
* S3
* Systems Manager
* Secrets Manager
* Cloudflare / DNS

Infrastructure was managed as Infrastructure as Code using **Terraform**.

Server provisioning and configuration were automated using **Ansible** where
applicable.

The project also uses **GitLab CI/CD** to automate the application delivery
process.

The high-level deployment flow is:

```text
Developer
    │
    ▼
GitLab
    │
    ▼
CI Pipeline
    │
    ├── Test
    │
    ├── Build Docker Image
    │
    ├── Push Image
    │
    └── Deploy
             │
             ▼
        Application
```

The infrastructure and CI/CD implementation are documented in:

* `docs/infrastructure.md`

---

## 15. V1 Engineering Decisions

### Schedule State

`next_checkin_at` is used as the source of truth for scheduling instead of
calculating the next check-in from user activity.

### User Activity vs Schedule

`last_seen_at` records activity but does not control the schedule.

### Check-in Stop Condition

An unanswered check-in eventually stops the user's check-in cycle after the
alert stage.

This prevents Wasaya from continuing to send check-in emails indefinitely
after a missed check-in.

### Timezone

The user's timezone is stored with their scheduling settings.

Local time is used to establish the initial schedule, while the scheduler
works with the stored UTC timestamp.

### Same Application Flow for API and Scheduler

The scheduler uses the same service/repository layers as the API instead of
duplicating business logic.

---

## 16. V1 Status

Wasaya V1 is feature-complete for the MVP check-in workflow.

The implemented flow covers:

```text
Account
   ↓
Verification
   ↓
Settings
   ↓
Scheduling
   ↓
Check-in
   ↓
Response
   │
   └── OR ──→ Expiration
                    ↓
                 Alert
                    ↓
              Stop Cycle
```

The V1 baseline includes the application, database model, scheduler,
notifications, containerization, and cloud deployment workflow.

V1 is the baseline from which future features will be developed.

---

## 17. Future Direction

The next major product direction is **Media Mode**.

Media Mode is not part of V1.

The intended lifecycle is:

```text
Active Check-ins
       ↓
Missed Check-in
       ↓
Grace Period
       ↓
Emergency Alert
       ↓
Media Mode
```

Future development should build on the V1 state model rather than changing
the existing check-in behavior without a clear architectural decision.


