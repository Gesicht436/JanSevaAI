# JanSevaAI (NagrikPulse)

> **Verifiable, Hallucination-Free Government Scheme Matching for Indian Citizens**

JanSevaAI is an AI-powered civic platform that matches Indian citizens with central and state government welfare schemes with **zero hallucination**, verifiable citations, and multi-turn conversational intake.

---

## Key Features

1. **Natural Language & Voice Intake**: Describe your situation naturally via conversational text or browser microphone voice recording.
2. **Comprehensive Profile Modeling**: Captures demographics, education, work experience, industry sector (IT, farming, manufacturing, crafts), business/loan intent, and socio-economic markers.
3. **Two-Stage Hybrid Matching Engine**:
   - **Stage 1 (Deterministic Hard-Gate)**: Instantly eliminates impossible schemes (< 15ms) based on statutory age limits, state borders, and active deadlines.
   - **Stage 2 (LLM Contextual Matcher)**: Semantically evaluates the candidate pool against complex qualitative conditions (e.g. degree equivalence, enterprise credit feasibility) with verbatim citations.
4. **Targeted Follow-Up & Progressive Unlocking**: Suggests the highest-leverage missing details to unlock Tier 2 (Needs More Info) schemes, highlighting newly unlocked benefits with animated badges.
5. **Text-to-Speech (TTS)**: Reads grounded eligibility explanations aloud in Indian English for low-literacy citizens.
6. **Self-Contained Deployment**: Runs frontend SPA and backend API together on a single server, backed by local SQLite.

---

## Quick Start

### 1. Install Dependencies
```bash
# Sync Python environment
uv sync --all-extras

# Install Frontend dependencies
cd frontend
npm install
npm run build
cd ..
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your LLM / TTS keys if using live AI generation
```

### 3. Run Application
```bash
# Start backend API (serves built frontend SPA on port 8000)
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
Visit `http://localhost:8000` in your web browser.

### 4. Run Automated Tests
```bash
# Backend pytest suite
uv run pytest backend/tests -v

# Frontend Vitest suite
cd frontend && npm test
```
