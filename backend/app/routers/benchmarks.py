from typing import Dict, List

from fastapi import APIRouter, Depends

from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/benchmarks", tags=["Benchmarks"], dependencies=[Depends(get_current_user)])

PUBLIC_BENCHMARKS = [
    {"id": "harmbench", "name": "HarmBench", "description": "Standard harmfulness benchmark"},
    {"id": "advbench", "name": "AdvBench", "description": "Adversarial benchmark dataset"},
    {"id": "jailbreakchat", "name": "JailbreakChat", "description": "Community jailbreak templates"},
    {"id": "anthropic-hh", "name": "Anthropic HH", "description": "Anthropic helpful/harmless dataset"},
]


@router.get("/public")
def list_public_benchmarks():
    return {"benchmarks": PUBLIC_BENCHMARKS}
