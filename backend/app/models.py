from pydantic import BaseModel
from typing import List, Dict, Any


class DatasetRequest(BaseModel):
    dataset_name: str
    row_count: int
    columns: List[str]
    rows: List[Dict[str, Any]]


class AnalysisResponse(BaseModel):
    status: str
    summary: Dict[str, Any]
    missing_values: Dict[str, int]