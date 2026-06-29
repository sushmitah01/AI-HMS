# AI-HMS — AI-Powered Hospital Management System

A full-stack, decision-support-oriented healthcare information system built as an undergraduate capstone project. It combines a Flask REST API, a React frontend, a PostgreSQL database, scikit-learn ML models, and an LLM-based chatbot into a single, modular platform for managing hospital workflows and assisting clinical staff with patient risk analysis.

**Live demo:** [ai-hms-one.vercel.app](https://ai-hms-one.vercel.app) *(backend cold-start on Render may cause a short delay on first load)*

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [User Roles](#user-roles)
- [Machine Learning Pipeline](#machine-learning-pipeline)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Limitations & Roadmap](#limitations--roadmap)
- [Ethical Disclaimer](#ethical-disclaimer)
- [License](#license)

---

## Overview

AI-HMS automates the day-to-day administrative workflows of a hospital (patient registration, appointments, medical records) while layering an ML-driven decision support engine on top. Doctors get a risk score for each patient — Low / Medium / High — derived from their medical history. A domain-restricted chatbot explains those predictions and summarises patient timelines in plain language.

The system is **not** a diagnostic tool. Every AI output is advisory; clinical decisions remain with the medical staff.

---

## Architecture

```
┌─────────────────────────────────────────┐
│           React + Tailwind (Vite)        │  ← Frontend (Vercel)
│  Recharts dashboards · Role-based UI     │
└────────────────────┬────────────────────┘
                     │ REST API (JSON)
┌────────────────────▼────────────────────┐
│              Flask (Python)              │  ← Backend (Render)
│  SQLAlchemy ORM · JWT Auth · Blueprint   │
└──────────┬───────────────────┬──────────┘
           │                   │
┌──────────▼──────┐   ┌────────▼─────────┐
│   PostgreSQL     │   │   ML Engine       │
│  (primary store) │   │  scikit-learn     │
│  JSONB for semi- │   │  Logistic Reg.    │
│  structured data │   │  Random Forest    │
└─────────────────┘   │  TF-IDF vectors   │
                       └────────┬─────────┘
                                │
                       ┌────────▼─────────┐
                       │  LLM Chatbot API  │
                       │  (domain-scoped)  │
                       └──────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js, Tailwind CSS, Recharts, Vite |
| Backend | Flask, SQLAlchemy ORM, Flask-JWT-Extended |
| Database | PostgreSQL with JSONB support |
| ML | scikit-learn (Logistic Regression, Random Forest, TF-IDF) |
| Chatbot | LLM API (external, domain-restricted prompt) |
| Deployment | Vercel (frontend), Render (backend) |

---

## Features

### Patient Management
- Register and update patient profiles
- Track full medical history across visits
- Store clinical notes with JSONB for flexible semi-structured data
- Longitudinal view of a patient's treatment timeline

### Appointment & Queue Management
- Schedule appointments with conflict detection
- Per-doctor queue views
- Full appointment lifecycle: pending → confirmed → completed / cancelled

### Medical Records
- Attach diagnoses, prescriptions, and test recommendations to each visit
- Records are linked to both the patient and the attending doctor

### AI Decision Support
The ML module reads structured patient data, engineers features, and outputs a risk tier:

| Risk Level | Meaning |
|---|---|
| 🟢 Low | Routine monitoring |
| 🟡 Medium | Elevated attention recommended |
| 🔴 High | Prioritise for review |

Predictions are stored in the database alongside the input features, so they are reproducible and auditable.

### Analytics Dashboard
- Daily patient intake and discharge trends (Recharts)
- Doctor workload distribution
- High-risk patient list for rapid review
- Hospital utilisation over time

### AI Chatbot Assistant
A prompt-engineered, domain-locked chatbot that can:
- Explain what drove a patient's risk score
- Summarise a patient's recent visit history in plain language
- Answer questions about hospital workflows

> The chatbot is explicitly prevented from providing medical diagnoses or treatment recommendations.

### Security
- Passwords stored as hashes (never plain text)
- JWT-based stateless authentication
- Role-based route guards (backend + frontend)
- Input validation on all API endpoints
- Audit log table tracks sensitive actions

---

## User Roles

| Role | What they can do |
|---|---|
| **Admin** | Manage user accounts, view analytics, oversee the full system |
| **Doctor** | View/edit patient records, see AI risk scores, use the chatbot |
| **Receptionist** | Register patients, schedule and manage appointments |

---

## Machine Learning Pipeline

```
PostgreSQL patient data
        ↓
  Data retrieval (SQLAlchemy)
        ↓
  Preprocessing (Pandas)
   - handle missing values
   - encode categorical fields
        ↓
  Feature engineering
   - visit frequency, diagnosis codes,
     age, comorbidity flags, etc.
        ↓
  Model training
   - Logistic Regression (baseline)
   - Random Forest (primary)
   - TF-IDF for clinical text fields
        ↓
  Prediction API endpoint
        ↓
  Results stored in ml_predictions table
        ↓
  Chatbot explanation layer
```

The trained model is serialised and loaded at API startup. Re-training can be triggered by calling the admin-only `/api/ml/retrain` endpoint.

---

## Database Schema

Key tables and their relationships:

```
users ──────────────── patients
  │                       │
  │ (doctor FK)           │ (patient FK)
  ▼                       ▼
appointments ────── medical_records
                          │
                          ▼
                    ml_predictions

audit_logs (references users + any table)
```

- **users** — all staff accounts with role field
- **patients** — demographics and contact info
- **appointments** — datetime, doctor, status, conflict flags
- **medical_records** — diagnosis, prescription, test orders; JSONB for extensible clinical data
- **ml_predictions** — risk tier, confidence score, feature snapshot, timestamp
- **audit_logs** — who did what and when

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### 1. Clone the repo

```bash
git clone https://github.com/sushmitah01/AI-HMS.git
cd AI-HMS
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Activate:
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your values (see [Environment Variables](#environment-variables)), then:

```bash
flask db upgrade      # run migrations
python app.py         # starts on http://localhost:5000
```

### 3. Frontend

```bash
cd ../frontend
npm install
npm run dev           # starts on http://localhost:5173
```

---

## Environment Variables

Create `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_hms

# Auth
JWT_SECRET_KEY=your-secret-key

# LLM Chatbot
LLM_API_KEY=your-llm-api-key
LLM_API_URL=https://api.your-llm-provider.com/v1/chat

# Flask
FLASK_ENV=development
```

---

## Project Structure

```
AI-HMS/
├── backend/
│   ├── app.py              # Flask app factory & entry point
│   ├── models/             # SQLAlchemy models
│   │   ├── user.py
│   │   ├── patient.py
│   │   ├── appointment.py
│   │   ├── medical_record.py
│   │   └── ml_prediction.py
│   ├── routes/             # API blueprints
│   │   ├── auth.py
│   │   ├── patients.py
│   │   ├── appointments.py
│   │   ├── records.py
│   │   ├── analytics.py
│   │   ├── ml.py
│   │   └── chatbot.py
│   ├── ml/                 # ML training & inference
│   │   ├── pipeline.py
│   │   └── model.pkl       # serialised model (generated)
│   ├── migrations/
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── pages/          # route-level components
    │   ├── components/     # shared UI components
    │   ├── hooks/          # custom React hooks
    │   └── api/            # Axios API client
    ├── package.json
    └── vite.config.js
```

---

## Limitations & Roadmap

**Current limitations**
- Prototype; not cleared for clinical deployment
- ML models trained on a small synthetic/limited dataset — predictions should not be trusted in real settings
- No real-time device or EHR integration
- Single-region deployment

**Planned improvements**
- Enhance Security Issues across all user login
- Disease Classifer using image
- Deep learning models for richer clinical text analysis
- FHIR-compatible data exchange for EHR integration
- Mobile app (React Native)
- Real-time alerting for critical risk-level changes
- Advanced NLP summarisation of discharge notes

---

## Ethical Disclaimer

This system is a **prototype built for academic purposes**. It is not validated for, nor intended to be used in, real clinical environments. All AI outputs are for demonstration only and must not influence patient care decisions.

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push and open a pull request

Please open an issue first for significant changes so we can discuss the approach.

---

## License

[MIT](LICENSE)
