# VANALY — Sustainable AI Health Coach

> Intervene at the moment before you swallow — diagnose real hunger and keep your routine.

[한국어 README →](README.ko.md)

---

## Core Values

| Value | Description |
|---|---|
| **Consistency** | Daily meal & emotion data builds a sustainable rhythm |
| **Intervention** | 3-second breathing Friction calms the amygdala before impulse wins |
| **Zero Judgment** | No criticism — a caring friend, always by your side |

---

## Tech Stack

- **Backend**: Python 3.12 · FastAPI · SQLite
- **Frontend**: Vanilla JS · Tailwind CSS (CDN) · PWA
- **AI**: GPT-4o Vision (meal analysis) · GPT-4o-mini (emotional coaching)
- **i18n**: Auto-detects browser language (Korean / English)

---

## Project Structure

```
VANALY/
├── backend/
│   ├── main.py              # FastAPI entry point, router registration
│   ├── database.py          # SQLite connection, schema init & migrations
│   ├── routers/
│   │   ├── users.py         # User creation, lookup, goal management
│   │   ├── meals.py         # Meal photo upload, analysis, history
│   │   └── coach.py         # AI coaching sessions (create, chat, close)
│   └── services/
│       ├── vision.py        # GPT-4o Vision image analysis
│       └── coach_ai.py      # Emotional coaching AI (situation-based prompts)
├── frontend/
│   ├── index.html           # PWA main screen
│   ├── src/
│   │   ├── i18n.js          # i18n module — language detection + t() function
│   │   ├── app.js           # Meal upload & result rendering
│   │   └── coach.js         # Breathing overlay & coaching modal
│   ├── manifest.json
│   └── service-worker.js    # Network-first caching strategy
├── requirements.txt
├── .env.example
└── CLAUDE.md                # AI development rules & project philosophy
```

---

## Features

### 1. Meal Analysis Engine
- Photo upload (gallery / camera / drag & drop) → GPT-4o Vision analysis
- Returns: food names, calories, carbs/protein/fat/fiber, sodium, blood sugar impact, energy peak
- Injects today's meal history as context → "You had 75g carbs at breakfast, so current hunger may be a blood sugar dip"
- Non-food or blurry images return a friendly guidance message

### 2. Find Calm (AI Emotional Coaching)
- **3-second Breathing Friction**: On button click, a full-screen blur overlay appears with concentric circle pulse animation and countdown — calms the amygdala before coaching begins
- Bottom sheet slides up smoothly after breathing completes
- **Situation-based instant empathy**: Binge Urge 🍔 / Stressed 😮‍💨 / Just Rough 🫂 — AI speaks first
- **Mission-driven prompts**: `binge` mode strictly forbids recommending high-calorie foods and mandates redirection (water, 10-min wait, walk)
- Today's meal data injected in real time for context-aware coaching
- Crisis keyword detection → 1393 mental health crisis banner auto-shown
- Session summary + next steps on close

### 3. Bilingual (EN / KO)
- Detects `navigator.language` on first load → persisted in `localStorage`
- All UI strings, AI coaching responses, and analysis feedback served in the detected language

### 4. PWA
- Offline caching (service worker, network-first strategy)
- Add to home screen (manifest.json)
- Mobile-optimized layout

---

## Quick Start

```bash
# 1. Environment setup
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Run dev server
uvicorn backend.main:app --reload
# → http://127.0.0.1:8000
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Server health check |
| `POST` | `/users` | Create user |
| `GET` | `/users/{id}` | Get user |
| `PUT` | `/users/{id}/goals` | Update nutrition goals |
| `POST` | `/meals/analyze` | Analyze meal photo |
| `GET` | `/meals/history` | Meal history |
| `POST` | `/coach/session` | Start coaching session |
| `POST` | `/coach/session/{id}/message` | Send message |
| `POST` | `/coach/session/{id}/close` | Close session + summary |

> Full API docs: `http://127.0.0.1:8000/docs`

---

## Environment Variables

```
OPENAI_API_KEY=sk-...
```
