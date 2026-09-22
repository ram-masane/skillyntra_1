# Skillyntra

Skillyntra is a Smart India Hackathon 2026 prototype connecting labour-market demand, skill gaps, learning, company assessments, skill validation, institute curriculum alignment, and district planning.

The **Next.js + FastAPI application is the primary application**. The original Streamlit app remains in `frontend/app.py` only as an optional legacy reference.

> The prototype uses synthetic labour-market data for demonstration.

## Features

- Role-based Student, Partner Company, Training Institute, and Government workspaces.
- Career Copilot using the 1,200-record labour-market dataset.
- Labour Market search, filtering, pagination, salary, experience, and skill evidence.
- Course marketplace seeded from `data/courses.csv`.
- SQLite-backed partner course publishing.
- SQLite-backed assessment authoring, grading, and Industry Validated skills.
- Institute curriculum alignment and course-health views.
- Government district demand versus training-capacity planning.
- CSV export for district planning reports.

## Architecture

```text
apps/web  ->  apps/api  ->  data/jobs.csv
                       ->  data/courses.csv
                       ->  data/training_capacity.csv
                       ->  data/skillyntra.db (local prototype state)
```

- `apps/web`: Next.js, TypeScript, responsive UI, role routes, workflow components.
- `apps/api`: FastAPI routes, data-derived analytics, SQLite persistence services.
- `data/jobs.csv`: primary labour-market source with 1,200 synthetic job records.
- `data/skillyntra.db`: local runtime state for published courses, assessments, and validation records. It is intentionally ignored by Git and recreated/seeded on startup.
- `backend/` and `frontend/`: legacy Streamlit-era reference modules.

## Project Structure

```text
.
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── routes/
│   │   │   ├── services/
│   │   │   ├── database.py
│   │   │   └── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── web/
│       ├── app/
│       ├── components/
│       ├── Dockerfile
│       ├── package.json
│       └── package-lock.json
├── data/
│   ├── jobs.csv
│   ├── courses.csv
│   ├── employer_feedback.csv
│   ├── placements.csv
│   ├── sector_growth.csv
│   └── training_capacity.csv
├── docs/
├── tests/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Requirements

- Python 3.12 or newer
- Node.js 20 or newer
- npm

## Installation and Running

From the repository root, open two terminals.

### Backend

```powershell
Set-Location apps/api
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The API health check is available at `http://127.0.0.1:8000/health`.

### Frontend

```powershell
Set-Location apps/web
npm ci
npm run dev
```

Open `http://localhost:3000`.

The frontend defaults to `http://127.0.0.1:8000`. Set `NEXT_PUBLIC_API_URL` in a local `.env.local` when the API is hosted elsewhere. Use `.env.example` as the template; never commit `.env` or real credentials.

### Docker

```powershell
docker compose up --build
```

The web app runs at `http://localhost:3000` and the API at `http://localhost:8000`.

## Demo Mode

1. Open Student and select `Data Analyst` in Career Copilot.
2. Select current skills and calculate the dataset-derived gap.
3. Inspect matching evidence in Labour Market.
4. Open Courses and enroll in `Data Analytics`.
5. Open Assessments, answer the seeded questions, and submit.
6. Open My Skills to see persisted Industry Validated skills.
7. Switch to Training Institute and open Curriculum Alignment.
8. Switch to Government and open District Planner.
9. Switch to Partner Company to publish a course or author an assessment.

No real authentication is required for the prototype.

## Dataset

`data/jobs.csv` is the primary source for job-market analytics. It contains synthetic records with job title, domain, company, location, state, salary range, experience range, description, and required skills. The application reads it through repository-relative paths and does not require a Windows-specific location.

The dataset is not live labour-market ingestion and should not be presented as real-time industry data.

## Optional Legacy Reference

The previous Streamlit prototype can be run separately when needed:

```powershell
python -m pip install -r requirements.txt
streamlit run frontend/app.py
```

It is not the primary demo or deployment target.

## Troubleshooting

- **`ModuleNotFoundError: backend` in Streamlit:** use the current `frontend/app.py`; it adds the repository root to `sys.path` for legacy compatibility. The modern app does not depend on Streamlit.
- **Frontend cannot reach the API:** confirm the API is running on port 8000 and check `NEXT_PUBLIC_API_URL`.
- **Stale course or validation data:** stop the API and remove the ignored local `data/skillyntra.db`; the seed courses will be recreated on the next start.
- **Build artifacts appear in Git:** run `git status --short`; `.next`, `node_modules`, Python caches, and local databases should be ignored by `.gitignore`.
