import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.provider_key import ProviderKey
from app.models.target_model import TargetModel
from app.services.providers.registry import provider_registry as registry
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/models", tags=["Target Models"], dependencies=[Depends(get_current_user)])


class TargetModelCreate(BaseModel):
    provider: str
    model: str
    label: str = ""
    api_key: str = ""


class TargetModelUpdate(BaseModel):
    label: Optional[str] = None
    api_key: Optional[str] = None


class TargetModelResponse(BaseModel):
    id: str
    provider: str
    model: str
    label: str
    status: str
    total_queries: int
    total_errors: int
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProviderInfo(BaseModel):
    name: str
    models: List[str]
    key_preview: str = ""
    has_key: bool = False


def _get_fernet():
    from cryptography.fernet import Fernet
    import os
    key = os.getenv("FUZZGUARD_ENCRYPTION_KEY")
    if key and len(key) == 44:
        return Fernet(key.encode())
    generated = Fernet.generate_key()
    os.environ["FUZZGUARD_ENCRYPTION_KEY"] = generated.decode()
    return Fernet(generated)


def _encrypt_key(key: str) -> str:
    if not key:
        return ""
    return _get_fernet().encrypt(key.encode()).decode()


def _decrypt_key(encrypted: str) -> str:
    if not encrypted:
        return ""
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except Exception:
        return ""


@router.post("/targets", response_model=TargetModelResponse, status_code=201)
def register_target(payload: TargetModelCreate, db: Session = Depends(get_db)):
    providers = {p["name"] for p in registry.list_providers()}
    if payload.provider not in providers:
        raise HTTPException(400, f"Unknown provider '{payload.provider}'. Available: {sorted(providers)}")

    tgt_id = f"tgt_{uuid.uuid4().hex[:12]}"
    tgt = TargetModel(
        id=tgt_id,
        provider=payload.provider,
        model=payload.model,
        label=payload.label or f"{payload.provider} / {payload.model}",
        api_key_encrypted=_encrypt_key(payload.api_key) if payload.api_key else "",
        status="active" if payload.api_key else "inactive",
    )
    db.add(tgt)
    db.commit()
    db.refresh(tgt)
    return tgt


@router.get("/targets", response_model=List[TargetModelResponse])
def list_targets(db: Session = Depends(get_db)):
    return db.query(TargetModel).all()


@router.get("/targets/{target_id}", response_model=TargetModelResponse)
def get_target(target_id: str, db: Session = Depends(get_db)):
    tgt = db.query(TargetModel).filter(TargetModel.id == target_id).first()
    if not tgt:
        raise HTTPException(404, "Target model not found")
    return tgt


@router.patch("/targets/{target_id}", response_model=TargetModelResponse)
def update_target(target_id: str, payload: TargetModelUpdate, db: Session = Depends(get_db)):
    tgt = db.query(TargetModel).filter(TargetModel.id == target_id).first()
    if not tgt:
        raise HTTPException(404, "Target model not found")
    if payload.label is not None:
        tgt.label = payload.label
    if payload.api_key is not None:
        tgt.api_key_encrypted = _encrypt_key(payload.api_key)
        tgt.status = "active" if payload.api_key else "inactive"
    db.commit()
    db.refresh(tgt)
    return tgt


@router.delete("/targets/{target_id}", status_code=204)
def delete_target(target_id: str, db: Session = Depends(get_db)):
    tgt = db.query(TargetModel).filter(TargetModel.id == target_id).first()
    if not tgt:
        raise HTTPException(404, "Target model not found")
    db.delete(tgt)
    db.commit()


@router.post("/targets/{target_id}/test")
def test_target(target_id: str, db: Session = Depends(get_db)):
    tgt = db.query(TargetModel).filter(TargetModel.id == target_id).first()
    if not tgt:
        raise HTTPException(404, "Target model not found")

    key = _decrypt_key(tgt.api_key_encrypted)

    provider = registry.get(tgt.provider, api_key=key, model=tgt.model)
    result = provider.query("Say 'ok' if you can hear me. Respond with exactly one word.")

    return {
        "status": "ok" if result.get("status_code") == "200" else "error",
        "response_preview": result.get("response", "")[:100],
        "latency": result.get("latency", 0),
    }


@router.get("/providers", response_model=List[ProviderInfo])
def list_providers(db: Session = Depends(get_db)):
    providers = registry.list_providers()
    key_rows = {r.provider: r for r in db.query(ProviderKey).all()}
    result = []
    for p in providers:
        name = p["name"]
        row = key_rows.get(name)
        encrypted = row.api_key_encrypted if row else ""
        preview = ""
        if encrypted:
            try:
                decrypted = _decrypt_key(encrypted)
                preview = decrypted[-4:] if len(decrypted) >= 4 else decrypted
            except Exception:
                preview = ""
        result.append(ProviderInfo(
            name=name,
            models=p["models"],
            key_preview=preview,
            has_key=bool(encrypted),
        ))
    return result
