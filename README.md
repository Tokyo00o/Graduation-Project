# FuzzGuard

Automated LLM red-teaming platform with evolutionary fuzzing, multi-turn attack templates, and MCTS-guided jailbreak discovery.

## Architecture

```
fuzzguard/
├── backend/          FastAPI + SQLAlchemy + SQLite
├── frontend/         React + Vite + TypeScript
├── cli/              Click-based CLI tool
├── .github/          GitHub Actions CI/CD
└── docker-compose.yml
```

## Quick Start

### Development

**Terminal 1 — Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`, sign up, create a project, and run your first job.

### Docker
```bash
docker compose up --build
```

Open `http://localhost:80`.

## Features

- **Fuzzing Strategies** — random, round-robin, UCB, MCTS
- **Multi-turn Attack Templates** — rapport-building, progressive escalation, socratic questioning, emotional manipulation, distraction, and more
- **Mutation Operators** — generate, expand, shorten, crossover, rephrase
- **Judgment Engine** — rule-based + ML classifier (TF-IDF/LogisticRegression) with automatic fallback
- **Target Models** — OpenAI, Anthropic, Google, Cohere, Mistral, HuggingFace, Self-hosted
- **Observability** — Prometheus metrics, structured JSON logging, OpenTelemetry tracing
- **Scheduling** — cron-based job scheduling with ASR breach alerts (Slack/Webhook)
- **RBAC** — viewer, analyst, engineer, admin roles with JWT auth
- **Reporting** — JSON/CSV/HTML/PDF exports with OWASP, NIST AI RMF, EU AI Act compliance mapping
- **Real-time** — WebSocket live iteration streaming, MCTS tree visualization
- **CI/CD** — GitHub Actions with backend/frontend tests, ASR regression checks, Docker build

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FUZZGUARD_DATABASE_URL` | `sqlite:///data/fuzzguard.db` | Database connection string |
| `FUZZGUARD_JWT_SECRET` | auto-generated | JWT signing secret |
| `FUZZGUARD_ENCRYPTION_KEY` | auto-generated | Fernet key for API key storage |
| `FUZZGUARD_SCHEDULER_ENABLED` | `true` | Enable background scheduler |
| `OPENAI_API_KEY` | — | OpenAI provider key |
| `ANTHROPIC_API_KEY` | — | Anthropic provider key |
| `GOOGLE_API_KEY` | — | Google provider key |

## CLI

```bash
# Install
pip install -e .

# Usage
fuzzguard run --project <id> --budget 500
fuzzguard report <job-id>
fuzzguard diff <job-a> <job-b>
fuzzguard benchmark --budget 200
```

## Testing

```bash
# Backend (72 tests)
cd backend && python -m pytest tests/

# Frontend (15 tests)
cd frontend && npm test -- --run

# ASR regression
cd backend && python scripts/run_asr_benchmark.py
```

## License

MIT
