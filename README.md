# PolicyAI — Agentic AI Economic Policy Simulator


https://github.com/user-attachments/assets/1fe28409-977b-423a-b793-832889ef3967


A bilingual English/Arabic decision-support platform for exploring model-based economic policy scenarios. It combines World Bank historical data, time-aware forecasting, XGBoost/Ridge scenario modelling, LangGraph orchestration, regional comparison, sector sensitivity analysis, interactive Plotly charts, PostgreSQL persistence, and PDF reports.

## Completed feature set

- Natural-language policy questions in English/Arabic
- LangGraph query → simulation → explanation workflow
- What-if simulations for investment, FDI, government consumption, exports, imports, and household consumption
- Short- and long-horizon projections (1–10 years)
- GDP growth, inflation, unemployment, and household-income proxy targets
- Baseline vs scenario trajectories
- Multi-scenario comparison API (2–6 scenarios)
- Regional/country comparison across GCC + selected markets
- Sector impact layer for agriculture, industry, manufacturing, and services
- Interactive Plotly historical and scenario charts
- Persisted scenario history
- Downloadable PDF reports
- PostgreSQL production Docker stack with SQLite local fallback
- Frontend + backend Docker integration
- Explicit uncertainty/disclaimer language; outputs are estimates, not policy recommendations

## Architecture

React/Vite → FastAPI → LangGraph + simulation services → World Bank data → PostgreSQL/SQLite

The LLM interprets and explains policy questions. Numerical results are produced by the data/forecasting/simulation layer rather than invented by the LLM.

## Local development

### Backend

```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Set `VITE_API_BASE_URL=http://127.0.0.1:8000` in `frontend/.env` if needed.

### Docker — full stack

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- PostgreSQL: localhost:5432

## Main API endpoints

- `POST /api/agent/query`
- `POST /api/scenario/simulate`
- `POST /api/scenario/compare`
- `POST /api/scenario/sector-impact`
- `GET /api/insights/regional-comparison`
- `GET /api/insights/sector-comparison/{country}`
- `POST /api/insights/sector-policy-impact`
- `GET /api/forecast/{country}/{indicator}`
- `GET /api/scenarios`
- `GET /api/reports/{scenario_id}.pdf`

## Important modelling note

Sector impacts use explicit sensitivity coefficients as a transparent scenario layer. They are not presented as causal econometric estimates. Country-specific calibration and additional economic controls are required before using the platform for real policy decisions.
