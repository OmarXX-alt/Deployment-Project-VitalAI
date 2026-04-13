# VitalAI

**AI-Powered Health & Wellness Tracker**
**Live URL:** [https://vitalai-dev-60303391.onrender.com/dashboard](https://vitalai-dev-60303391.onrender.com/dashboard)

---

## Course Information

| Item         | Detail                                         |
| ------------ | ---------------------------------------------- |
| Course       | INFS3203 — Systems Deployment & Implementation |
| Semester     | Winter 2026                                    |
| Institution  | UDST                                           |
| Instructor   | Vanilson Burégio                               |
| Presentation | April 8, 2026                                  |

---

## Team & Roles

| Member                     | Role              |
| -------------------------- | ----------------- |
| Omar Al Himsi (60303391)   | Backend + CI Lead |
| Yyan (60306991)            | AI + QA Lead      |
| Sumaya Al Asiri (60304691) | Frontend + DevOps |

---

## About the Project

VitalAI is an intelligent health tracker where **AI reacts instantly** to user inputs such as workouts, meals, sleep, hydration, and mood.

Unlike traditional trackers that only store data, VitalAI provides:

* Real-time AI feedback
* Context-aware insights
* Personalized recommendations

This makes the system proactive rather than passive.

---

## Key Features (Refactored)

### Core Features (MVP)

* User Authentication (JWT-based login/register)
* Workout, Meal, Sleep, Hydration, Mood tracking
* Dashboard with trends visualization

### AI Features

* Reactive AI responses for each log entry
* On-demand wellness insights
* AI Chat Assistant for user interaction

### System Features

* RESTful API with Flask
* MongoDB Atlas database integration
* Secure environment-based configuration

---

## Tech Stack

| Layer            | Choice                  |
| ---------------- | ----------------------- |
| Backend          | Python + Flask          |
| AI               | Google Gemini 2.5 Flash |
| Database         | MongoDB Atlas           |
| Frontend         | HTML/CSS/JS + Chart.js  |
| Containerization | Docker                  |
| CI/CD            | GitHub Actions + Render |
| Testing          | pytest (15+ tests)      |

---

## Local Setup

```bash
# 1. Clone repository
git clone https://github.com/OmarXX-alt/Deployment-Project-VitalAI.git
cd Deployment-Project-VitalAI

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment file
echo "MONGODB_URI=your_uri" > .env
echo "GEMINI_API_KEY=your_key" >> .env
echo "JWT_SECRET_KEY=your_secret" >> .env

# 5. Run application
python app.py
```

### Alternative (run.py entry point)

```bash
python run.py
```

### Docker Setup

```bash
docker build -t vitalai .
docker run -p 5000:5000 --env-file .env vitalai
```

---

## Testing

```bash
pytest tests/ -v
```

* 15+ tests
* Covers authentication, CRUD operations, AI parsing, and error handling

---

## CI/CD Pipeline

| Job | Steps                                     | Status  |
| --- | ----------------------------------------- | ------- |
| CI  | Lint → pytest → Docker build → smoke test | Passing |
| CD  | Render auto-deploy → health check         | Passing |

Secrets are stored securely in GitHub Secrets and Render environment variables.

---

## Deployment

| Item        | Detail                                                                                                     |
| ----------- | ---------------------------------------------------------------------------------------------------------- |
| Platform    | Render.com (Free Tier)                                                                                     |
| Live URL    | [https://vitalai-dev-60303391.onrender.com/dashboard](https://vitalai-dev-60303391.onrender.com/dashboard) |
| Auto-deploy | On push to main                                                                                            |
| Cold start  | 20–30 seconds                                                                                              |

---

## Responsible AI Use

| Concern        | Mitigation                  |
| -------------- | --------------------------- |
| API errors     | Graceful fallback           |
| Bad outputs    | JSON validation + fallback  |
| Data privacy   | Only last 7 days sent to AI |
| Credentials    | Stored securely             |
| AI limitations | Not medical-grade           |

---

## Architecture Overview

User → Frontend → Flask API → MongoDB Atlas
                             ↘ Gemini AI

---

## 3-Week Development Timeline

### Week 1 – Foundation

* Project setup and repo initialization
* Flask backend structure
* MongoDB integration
* User authentication (JWT)

### Week 2 – Core Features

* Implement 5 health loggers (CRUD)
* Integrate Gemini AI for reactive responses
* Build frontend forms and dashboard

### Week 3 – Deployment & Quality

* Add pytest test suite (15+ tests)
* Configure CI/CD pipeline
* Dockerize application
* Deploy to Render
* Final testing and bug fixes

---

## Project Status

### Completed

* Full backend + frontend implementation
* AI integration (5 reactive hooks + chat)
* CI/CD pipeline
* Deployment live

### Known Limitations

* Render cold start delay
* Gemini API rate limits
* Data limited to last 7 days

### Future Improvements

* Medical-grade insights validation
* Faster AI responses
* Extended data storage (1–3 months)
* More advanced analytics
