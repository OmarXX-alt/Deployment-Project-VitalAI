## Course Information
Item	Detail
Course	INFS3203 — Systems Deployment & Implementation
Semester	Winter 2026
Institution	UDST
Instructor	Vanilson Burégio
Presentation	April 8, 2026

## Team & Roles

| Member | Role |
|--------|------|
| Omar Al Himsi (60303391) | Backend + CI Lead |
| Yyan (60306991) | AI + QA Lead |
| Sumaya Al Asiri (60304691) | Frontend + DevOps |

# VitalAI
**AI-Powered Health & Wellness Tracker**
**Live URL:** https://vitalai-dev-60303391.onrender.com/dashboard
---

## About the Project

VitalAI is a health tracker where **AI reacts instantly** when you log workouts, meals, sleep, hydration, or mood. Each entry triggers personalised insight. Most trackers are passive — VitalAI gives context-aware guidance at every interaction.

---
## Key Features
| Feature | AI? | Status |
|---------|-----|--------|
| User Registration & Login | No | Done |
| Workout Logger | Reactive AI | Done |
| Meal Logger | Reactive AI | Done |
| Sleep Tracker | Reactive AI | Done |
| Hydration Tracker | Reactive AI | Done |
| Mood Check-in | Reactive AI | Done |
| Dashboard & Trends | No | Done |
| AI Wellness Insights | On-demand | Done |
| AI Chat Assistant | Extension | Done |

**Note:** Extensions were planned but out of scope for final delivery. We prioritized MVP Core + CI/CD stability.

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | Python + Flask |
| AI | Google Gemini 2.5 Flash |
| Database | MongoDB Atlas |
| Frontend | HTML/CSS/JS + Chart.js |
| Containerization | Docker |
| CI/CD | GitHub Actions + Render |
| Testing | pytest (15+ tests) |


## Local Setup (5 steps)
```bash
# 1. Clone
git clone https://github.com/OmarXX-alt/Deployment-Project-VitalAI.git
cd Deployment-Project-VitalAI

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
echo "MONGODB_URI=your_uri" > .env
echo "GEMINI_API_KEY=your_key" >> .env
echo "JWT_SECRET_KEY=your_secret" >> .env

# 5. Run
python app.py
```
Docker alternative:
```bash
docker build -t vitalai .
docker run -p 5000:5000 --env-file .env vitalai
```
## Testing
```bash
pytest tests/ -v
```
Coverage: 15+ tests covering auth routes, all 5 log CRUD endpoints, AI response parsing, and error handling. All tests pass in CI.

## CI/CD Pipeline
| Job | Steps | Status |
|-----|-------|--------|
| CI | Lint → pytest (15+) → Docker build → smoke test | Passing |
| CD | Trigger Render webhook → auto-deploy → health check | Passing |
**Secrets:** Stored in GitHub Secrets + Render Environment Variables. Never committed to code.

## Deployment
| Item | Detail |
|------|--------|
| Platform | Render.com (Free Tier) |
| Live URL | https://vitalai-dev-60303391.onrender.com/dashboard |
| Auto-deploy | On push to main |
| Cold start | ~20-30 seconds after idle |

## Responsible AI Use
| Concern | Mitigation |
|---------|------------|
| API errors | Graceful fallback — save succeeds |
| Bad outputs | JSON parsing → fallback message |
| Data privacy | Only last 7 days of logs sent to Gemini |
| Credentials | Secrets only, never in code |
| AI limits | Not medical-grade. Users use judgment |

## Architecture Overview
User → Browser (HTML/CSS/JS) → Flask API → MongoDB Atlas
                              ↘ Gemini AI (reactive hooks)

## Project Status
Completed
GitHub repo with branch protection
MongoDB Atlas (6 collections)
JWT authentication
All 5 log CRUD endpoints
5× reactive AI hooks
Wellness Insights endpoint
pytest suite (15+ tests)
CI/CD pipeline (GitHub Actions + Render)
Frontend: 5 forms + dashboard
Live deployment verified
AI Chat Assistant

Known Limitations
Render cold start delay
Gemini rate limits (occasional fallback)
Limited to last 7 days of logs
