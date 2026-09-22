from pathlib import Path

import pandas as pd
from fastapi import APIRouter

router = APIRouter(prefix="/api/government", tags=["government"])
CAPACITY = pd.read_csv(Path(__file__).resolve().parents[4] / "data" / "training_capacity.csv")


@router.get("/districts")
def districts() -> list[dict]:
    rows = []
    for district, group in CAPACITY.groupby("district"):
        group = group.copy()
        group["gap"] = group.estimated_demand - group.annual_capacity
        priority = group.sort_values("gap", ascending=False).iloc[0]
        # Unified terminology: SHORTAGE, BALANCED, POTENTIAL OVERSUPPLY
        if priority.gap > 0:
            status = "SHORTAGE"
        elif priority.gap < 0:
            status = "POTENTIAL OVERSUPPLY"
        else:
            status = "BALANCED"
        rows.append({"district": district, "priority_skill": priority.skill, "demand": int(group.estimated_demand.sum()), "capacity": int(group.annual_capacity.sum()), "gap": int(group.gap.sum()), "status": status})
    return sorted(rows, key=lambda item: item["gap"], reverse=True)
