# AI-HMS: AI consultation scribe for busy OPD clinics

> Doctors in high-volume outpatient clinics spend a large share of each consultation writing notes and prescriptions by hand. AI-HMS turns a doctor's rough, mixed English/Bangla note into a structured record, checks the prescription against deterministic safety rules, and saves **nothing** until the doctor has reviewed and accepted it.

**Status: academic prototype. Not clinically validated. Not for real patient care.**

---

## The problem and who it is for

- **User:** a doctor seeing dozens of OPD patients a day in a small or mid-size clinic where records are paper or barely digital.
- **Pain:** documentation time, illegible or incomplete prescriptions, and no systematic check for dangerous drug combinations or allergies.
- **Goal:** cut minutes per consultation without removing the doctor's judgement.
- **Success metric:** *how often does the doctor accept the AI draft unchanged, and which fields do they keep correcting?* The system measures this itself (see [Evaluation](#evaluation)).

The rest of the app (patients, appointments, billing, notifications) exists to give the scribe real context: who the patient is, which doctor owns the visit, and where the finished record goes.

---

## How the scribe works

```
Doctor types / dictates rough note  ──►  POST /api/scribe/draft
                                              │
        access check: doctor must have a relationship with the patient
                                              │
                      LLM (Gemini) structures the note into JSON
                      - may only use facts present in the note
                      - leaves fields empty rather than guessing
                      - lists phrases it could not interpret ("uncertain")
                                              │
                 server-side schema validation + sanitising
                                              │
        deterministic safety rules (no LLM): interactions, duplicates,
        allergy / class cross-match, incomplete order lines
                                              │
            Doctor reviews & edits ──► POST /api/scribe/<id>/review
                 • accept → becomes a MedicalRecord (author = logged-in doctor)
                 • reject → logged with reason
                 • high-severity flags must be explicitly acknowledged
                                              │
            ai_suggestions table keeps draft vs final, per-field edits
```

Design choices that matter:

1. **The AI is a structurer, not a clinician.** It never produces diagnoses or doses the doctor did not state.
2. **Rules decide whether to warn.** An LLM saying "no interactions" is not evidence of safety, so medication checks are deterministic (`services/med_safety.py`).
3. **Human in the loop by construction.** A draft is not a record. Every accept/edit/reject is logged.
4. **Fails honestly.** If the AI is unavailable or returns junk, the API returns a 503, never fabricated output.

---

## What is real and what is a stub

| Component | Status |
|---|---|
| Auth (JWT, hashed passwords, staff whitelist), roles, rate limits | Working |
| Record-level access control (doctor→own patients, patient→self, receptionist→no clinical data) | Working, covered by tests |
| Patients, appointments, records, billing, notifications | Working (basic CRUD) |
| **AI consultation scribe** (Gemini → validated JSON → review → record) | Working; needs `GEMINI_API_KEY` |
| **Medication safety rules** | Working but a **small hand-curated starter set**, not a full interaction database |
| Evaluation logging + metrics (`/api/scribe/metrics`) | Working; **no published accuracy numbers yet** |
| Health-risk and readmission models (`ml/`) | **Demo stubs.** Trained on synthetic, rule-labelled data; they re-learn the rule that generated them. Responses carry a disclaimer. Not connected to patient records. |
| Symptom checker / "AI Insights" Gemini wrappers | Prototype. Free-text LLM output, no clinical validation |
| Chat widget (`chat_service.py`) | Keyword matcher, **not an LLM** |

Things this README previously claimed that the code does **not** do have been removed: TF-IDF, `ml_predictions` and audit-log tables, `/api/ml/retrain`, Flask-Migrate, FHIR, JSONB, PostgreSQL-only storage.

---

## Evaluation

The scribe is only useful if doctors keep what it writes. Every reviewed draft stores the model output and the final text, so we can compute:

- **Unchanged-accept rate**, **accepted-after-edit rate**, **rejection rate**
- **Edits by field** (e.g. are medicines edited far more than diagnoses?)
- **Drafts with safety flags**

`GET /api/scribe/metrics` returns these per doctor (or globally for Admin).

**Before any claim of accuracy**, build a gold set: ~50-100 de-identified or fabricated consultation notes (mixed English/Bangla, abbreviations, messy dictation) with doctor-written reference records. Score field-level accuracy, **hallucinated drugs/doses** (target: zero), and unsafe omissions. No such numbers exist yet; do not quote any.

---

## Architecture

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind, Recharts |
| Backend | Flask, SQLAlchemy, PyJWT, Flask-Limiter |
| Database | SQLite by default; PostgreSQL via `DATABASE_URL` |
| AI | Google Gemini (structured JSON output, low temperature); scikit-learn demo models |
| Tests | pytest (56 tests: auth, access control, safety rules, scribe flow with mocked LLM) |

Key files: `backend/routes/scribe_routes.py`, `backend/services/scribe_service.py`, `backend/services/med_safety.py`, `backend/utils/access.py`, `backend/models/ai_suggestion.py`, `frontend/src/pages/Scribe.jsx`.

### Access rules

| Role | Patients | Clinical records | Scribe |
|---|---|---|---|
| Admin | all | all | metrics only |
| Doctor | only patients they have an appointment/record with | only those patients; edit/delete only own | yes |
| Receptionist | all demographics | **none** | no |
| Patient | self only | self only | no |

Record authorship comes from the login token, never from a client-supplied `doctor_id`.

---

## Getting started

```bash
git clone https://github.com/sushmitah01/AI-HMS.git && cd AI-HMS/backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # set SECRET_KEY and GEMINI_API_KEY
python app.py            # http://localhost:5000

cd ../frontend && npm install && npm run dev          # http://localhost:5173
cd ../backend && pip install -r requirements-dev.txt && pytest
```

Tables are created automatically (`db.create_all()`). Existing databases pick up the new `ai_suggestions` table on next start; no existing columns changed.

---

## Known limitations / roadmap

**Safety & compliance (highest priority)**
- Patient notes are sent to a third-party LLM. Needs explicit consent, a data-processing agreement, redaction of direct identifiers, and a regional/self-hosted option before any real use.
- Replace the starter interaction table with an authoritative source (RxNorm + a drug-knowledge database) and a local brand→generic formulary.
- Add allergies as a first-class patient field (currently entered per draft).
- Short-lived tokens with refresh/revocation, a real audit log, and migrations (Alembic).

**Scribe**
- Voice input (speech-to-text for Bangla/English code-switching), then the same pipeline.
- Gold-set evaluation and a published results table.
- Prescription print/PDF in the patient's language.

**Other directions**
- No-show prediction from real appointment history; queue/wait-time forecasting.
- Lab-report and paper-prescription digitisation (OCR → structured data).
- Replace the demo ML stubs with models trained on real data and calibrated, or remove them.

---

## Ethical disclaimer

Prototype for academic purposes. AI output is a draft for a qualified clinician to verify. It must not be used to make or influence real clinical decisions.

## License

[MIT](LICENSE)
