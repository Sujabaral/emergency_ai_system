
# Emergency Detection & Incident Management System

## Overview

The Emergency Detection System is a scalable backend platform designed to detect, classify, manage, and escalate operational incidents across enterprise infrastructure.

The system continuously monitors multiple signal sources—including application logs, database metrics, uptime monitors, error tracking platforms, and support systems—and automatically converts incoming events into structured incidents.

Key capabilities include:

* Centralized event ingestion
* Multi-stage severity classification
* Duplicate alert suppression
* Automated notification routing
* Incident persistence and reporting
* Escalation management
* Extensible source and notification integrations

The architecture is designed to remain vendor-neutral, scalable, and easy to extend as infrastructure grows.

---

# System Architecture

The platform consists of two independent components:

## 1. Core Python Application

The Python application acts as the central processing engine and is responsible for:

* Event normalization
* Deduplication
* Severity classification
* Incident creation
* Database persistence
* Notification delivery
* Report generation
* Escalation management

All business logic resides within this component.



## 2. Workflow Integration Layer (n8n)

n8n serves as an integration and automation layer.

Responsibilities include:

* Receiving external webhooks
* Running scheduled polling tasks
* Forwarding events to the Python API

n8n does not contain any classification or incident-management logic.

This separation allows integrations to evolve independently from the incident-processing engine.

# High-Level Workflow

Every event follows the same processing lifecycle.

Signal Source
      │
      ▼
 Event Ingestion
      │
      ▼
 Normalization
      │
      ▼
 Deduplication
      │
      ▼
 Classification
      │
      ▼
 Incident Creation
      │
      ▼
 Persistence
      │
      ▼
 Notification Routing
      │
      ▼
 Report Generation
      │
      ▼
 Escalation Monitoring

# Event Sources

The platform supports multiple operational signal sources.

| Source Type       | Example                    |
| ----------------- | -------------------------- |
| Application Logs  | Runtime errors, exceptions |
| Database Metrics  | High CPU, slow queries     |
| Uptime Monitoring | Service unavailable        |
| Error Tracking    | Sentry exceptions          |
| Support Systems   | Customer-reported outages  |

All incoming events are converted into a common event structure before processing.


# Event Normalization

Different monitoring tools produce different payload formats.

To ensure consistent processing, all incoming data is normalized into a standard internal event model.

The normalized event contains:

* Source
* Message
* Timestamp
* Metadata

This abstraction allows new integrations to be added without modifying downstream processing logic.

---

# Deduplication

Operational incidents often generate repeated alerts.

The deduplication module prevents alert flooding by identifying events that represent the same underlying issue.

The process:

1. Normalize event content.
2. Generate a fingerprint.
3. Check existing fingerprints within a configurable time window.
4. Suppress duplicates.
5. Continue processing only unique events.

Benefits:

* Reduced alert fatigue
* Cleaner incident timelines
* Lower notification volume

---

# Severity Classification

The platform uses a multi-layer classification pipeline to determine incident severity.

## Classification Levels

| Severity | Description                                   |
| -------- | --------------------------------------------- |
| P1       | Critical outage or business-impacting failure |
| P2       | Major degradation requiring urgent attention  |
| P3       | Minor degradation or warning                  |
| P4       | Informational event                           |

---

## Classification Strategy

A cascading architecture balances speed, cost, and accuracy.

### Layer 1 — Rule Engine

Uses:

* Keywords
* Regular expressions
* Source reliability scores

Best for:

* Known patterns
* High-confidence failures

---

### Layer 2 — Machine Learning Model

Uses:

* Historical incident data
* TF-IDF features
* Logistic Regression

Best for:

* Previously observed incidents
* Organizational-specific patterns

---

### Layer 3 — Large Language Model (LLM)

Used only when earlier layers cannot confidently classify an event.

Best for:

* Ambiguous alerts
* Previously unseen scenarios

---

# Incident Lifecycle

Once classified, an event becomes an Incident.

An incident contains:

* Unique identifier
* Severity
* Source
* Classification result
* Confidence score
* Timestamp
* Metadata

The incident becomes the central object used throughout the platform.

---

# Data Persistence

All incidents are stored in PostgreSQL.

The database supports:

* Incident history
* Auditability
* Reporting
* Analytics
* Trend analysis

Indexes are applied to frequently queried fields such as:

* Severity
* Source
* Timestamp
* Fingerprint

---

# Notification Framework

Notifications are routed according to severity.

| Severity | Notification Channels         |
| -------- | ----------------------------- |
| P1       | Voice, Email, Slack, Telegram |
| P2       | Email, Slack, Telegram        |
| P3       | Slack                         |
| P4       | Database only                 |

The notification framework is modular and allows additional channels to be added without changing incident-processing logic.

---

# Reporting

The reporting subsystem generates structured incident reports.

Reports typically contain:

* Incident summary
* Timeline
* Impact assessment
* Classification reasoning
* Recommended actions

Reports can be generated:

* Per incident
* Daily digest
* Weekly summary



# Escalation Management

Critical incidents require continuous attention.

The escalation engine periodically evaluates unresolved incidents.

If acknowledgment is not received within configured thresholds:

* Additional notifications are sent
* Escalation contacts are notified
* Escalation actions are logged

This ensures critical incidents are not missed.


# Component Responsibilities

| Component            | Responsibility                      |
| -------------------- | ----------------------------------- |
| Ingestion Layer      | Collect external events             |
| Normalization Layer  | Standardize event format            |
| Deduplication Layer  | Prevent duplicate incidents         |
| Classification Layer | Determine severity                  |
| Incident Manager     | Create and track incidents          |
| Storage Layer        | Persist incident data               |
| Notification Layer   | Deliver alerts                      |
| Reporting Layer      | Generate reports                    |
| Escalation Engine    | Monitor unresolved incidents        |
| n8n                  | Integration and workflow automation |



# Folder Structure

```
emergency_detection/
│
├── config/                         # All configuration — rules, settings, routing
│   ├── settings.py                 # App-wide settings loaded from .env via pydantic-settings
│   ├── severity_rules.yaml         # P1/P2/P3/P4 keyword lists, regex patterns, source weights
│   └── notification_routes.yaml    # Which severity triggers which notification channels
│
├── ingestion/                      # Data collection from all sources
│   ├── __init__.py
│   ├── base_ingestor.py            # Abstract base class all ingestors inherit from
│   ├── log_ingestor.py             # Tails log files using Watchdog, detects new lines
│   ├── db_ingestor.py              # Polls PostgreSQL/MySQL metrics (pg_stat, slow queries)
│   ├── webhook_receiver.py         # FastAPI endpoints for Sentry/UptimeRobot webhooks
│   └── ticket_ingestor.py          # Polls Jira/Linear for tickets with alert keywords
│
├── classifier/                     # The classification brain — 3-tier cascade
│   ├── __init__.py
│   ├── base_classifier.py          # Abstract interface all classifiers implement
│   ├── rule_classifier.py          # Tier 1: regex + keyword matching against severity_rules.yaml
│   ├── ml_classifier.py            # Tier 2: TF-IDF + Logistic Regression (scikit-learn)
│   ├── llm_classifier.py           # Tier 3: Groq free API / Ollama local LLM
│   ├── ensemble_classifier.py      # Chains T1 → T2 → T3, returns final result
│   └── training/
│       ├── __init__.py
│       ├── labeled_data.csv        # Historical incidents with severity labels for ML training
│       └── train_model.py          # Script to train and save the ML model
│
├── alerting/                       # Incident lifecycle management
│   ├── __init__.py
│   ├── incident.py                 # Incident + RawEvent dataclasses, Severity/Source enums
│   ├── deduplicator.py             # Fingerprint hashing, cache lookup, duplicate suppression
│   └── escalation.py              # Auto-escalate unacknowledged incidents after timeout
│
├── notifications/                  # Alert delivery to all channels
│   ├── __init__.py
│   ├── base_notifier.py            # Abstract BaseNotifier with send(incident) interface
│   ├── slack_notifier.py           # Sends formatted Slack blocks via incoming webhook
│   ├── telegram_notifier.py        # Sends message via Telegram Bot API
│   ├── email_notifier.py           # Sends HTML email via Gmail SMTP
│   ├── voice_notifier.py           # Twilio voice call with AI-generated message text
│   └── notification_router.py      # Reads notification_routes.yaml, fires correct notifiers
│
├── reports/                        # Incident report generation
│   ├── __init__.py
│   ├── report_generator.py         # Generates reports from Incident data using Jinja2
│   ├── pdf_exporter.py             # Converts HTML reports to PDF using WeasyPrint
│   └── templates/
│       ├── incident_report.html    # Jinja2 template for single incident report
│       └── daily_digest.html       # Jinja2 template for daily summary email
│
├── storage/                        # Data persistence and caching
│   ├── __init__.py
│   ├── database.py                 # PostgreSQL engine, SessionLocal, IncidentModel, IncidentRepository
│   └── cache.py                    # TTL cache: InMemoryCache (default) or RedisCache
│
├── api/                            # HTTP API — the single entry point for all events
│   ├── __init__.py
│   ├── main.py                     # FastAPI app instantiation, middleware, startup hooks
│   └── routes/
│       ├── __init__.py
│       ├── ingest.py               # POST /ingest — runs full pipeline for incoming events
│       └── incidents.py            # GET /incidents, GET /incidents/{id}, POST /acknowledge, /resolve
│
├── n8n/                            # n8n workflow definitions (JSON export)
│   ├── sentry_webhook_to_python.json       # Sentry → POST /ingest
│   ├── uptime_robot_to_python.json         # UptimeRobot → POST /ingest
│   └── daily_digest_schedule.json          # Cron 9am → GET /incidents/digest → email
│
├── tests/                          # pytest test suite
│   ├── __init__.py
│   ├── test_rule_classifier.py     # 25 tests for P1/P2/P3/P4 classification + edge cases
│   ├── test_phase2.py              # 19 tests for cache, deduplicator, settings
│   ├── test_ensemble_classifier.py # Tests for the full 3-tier cascade
│   └── test_notifications.py       # Tests for each notifier using mocks
│
├── requirements.txt                # All Python dependencies with pinned versions
├── .env.example                    # Template for environment variables (safe to commit)
├── .env                            # Your actual secrets — NEVER commit this file
├── docker-compose.yml              # Runs PostgreSQL + Redis + n8n locally
├── setup_project.py                # Run once to scaffold the folder structure
└── README.md                       # This file
```



# Extending the Platform

## Adding a New Event Source

1. Create a new ingestion module.
2. Convert incoming data to the standard event format.
3. Register the source type.
4. Configure source classification weights.
5. Connect the source through API or workflow automation.

---

## Adding a New Notification Channel

1. Implement the notification interface.
2. Configure required credentials.
3. Register the notifier.
4. Define routing rules.


## Summary

The Emergency Detection System provides a centralized, scalable, and extensible approach to incident management. By combining structured event ingestion, intelligent classification, automated notifications, and escalation workflows, the platform enables organizations to respond to operational issues quickly while minimizing alert fatigue and manual intervention.
