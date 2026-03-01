from fastapi import APIRouter

router = APIRouter()

@router.post("/analyze")
async def analyze(data: dict):
    rows = data.get("rows", [])
    columns = data.get("columns", [])

    return {
        "status": "success",
        "summary": {
            "total_rows": len(rows),
            "total_columns": len(columns)
        },
        "missing_values": {}
    }