from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.economic_data import (
    router as economic_router,
)
from backend.app.api.preprocessing import (
    router as preprocessing_router,
)
from backend.app.api.forecasting import (
    router as forecasting_router,
)
from backend.app.api.scenario import (
    router as scenario_router,
)
from backend.app.api.agent import (
    router as agent_router,
)
from backend.app.api.insights import router as insights_router
from backend.app.api.history import router as history_router
from backend.app.api.reports import router as reports_router
from backend.app.db.database import Base, engine


app = FastAPI(
    title="Agentic AI Economic Policy Simulator",
    description=(
        "Bilingual agentic AI platform for "
        "data-driven economic policy scenario analysis"
    ),
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# API Routers
# ---------------------------------------------------------

app.include_router(economic_router)
app.include_router(preprocessing_router)
app.include_router(forecasting_router)
app.include_router(scenario_router)
app.include_router(agent_router)
app.include_router(insights_router)
app.include_router(history_router)
app.include_router(reports_router)

# Create persistence tables for local development; PostgreSQL is used when DATABASE_URL points to it.
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------
# Root
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "success",
        "message": (
            "Agentic AI Economic Policy "
            "Simulator API is running"
        ),
        "version": "1.0.0",
    }


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "economic-policy-simulator",
        "version": "1.0.0",
    }
