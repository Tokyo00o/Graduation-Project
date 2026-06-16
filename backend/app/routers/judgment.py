from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import FuzzJob
from app.services.judgment import judge_registry
from app.services.judgment.metrics import ASRMetrics
from app.schemas.common import StatusResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/judges", tags=["Judgment"], dependencies=[Depends(get_current_user)])


class TrainItem(BaseModel):
    text: str
    label: str


class TrainRequest(BaseModel):
    samples: List[TrainItem]


class JudgeInfo(BaseModel):
    name: str
    type: str


@router.get("", response_model=List[JudgeInfo])
def list_judges():
    return judge_registry.list_judges()


@router.post("/train", response_model=StatusResponse)
def train_judge(payload: TrainRequest):
    ml = judge_registry.ml_judge
    if not ml:
        raise HTTPException(400, "ML judge not available")

    texts = [s.text for s in payload.samples]
    labels = [s.label for s in payload.samples]

    valid_labels = {"full_refusal", "partial_refusal", "partial_compliance", "full_compliance"}
    for label in labels:
        if label not in valid_labels:
            raise HTTPException(400, f"Invalid label: {label}")

    ml.train(texts, labels)
    ml.save()
    return StatusResponse(status="ok", message=f"Trained on {len(texts)} samples")


@router.get("/default-train", response_model=List[TrainItem])
def get_default_training_data():
    from app.services.judgment.ml_judge import DEFAULT_TRAINING_DATA
    return [TrainItem(text=t, label=l) for t, l in DEFAULT_TRAINING_DATA]


@router.post("/set-fallback", response_model=StatusResponse)
def set_fallback(order: List[str]):
    available = {j["name"] for j in judge_registry.list_judges()}
    for name in order:
        if name not in available:
            raise HTTPException(400, f"Judge '{name}' not registered")
    judge_registry.set_fallback(order)
    return StatusResponse(status="ok", message=f"Fallback order: {order}")


@router.get("/metrics/{job_id}")
def get_job_metrics(job_id: str, db: Session = Depends(get_db)):
    job = db.query(FuzzJob).filter(FuzzJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    metrics = ASRMetrics(db, job_id)
    return metrics.full_report()
