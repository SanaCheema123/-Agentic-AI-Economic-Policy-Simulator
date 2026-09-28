from pydantic import BaseModel, Field
from backend.app.schemas.scenario import ScenarioRequest

class ScenarioCompareRequest(BaseModel):
    scenarios: list[ScenarioRequest] = Field(min_length=2, max_length=6)
