from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.provider_key import ProviderKey
from app.services.providers.registry import provider_registry as registry
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/keys", tags=["API Keys"], dependencies=[Depends(get_current_user)])


class SetKeyRequest(BaseModel):
    api_key: str
    label: str = ""


class KeyResponse(BaseModel):
    provider: str
    label: str
    key_preview: str
    has_key: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


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


def get_provider_key(provider_name: str, db: Session) -> str:
    row = db.query(ProviderKey).filter(ProviderKey.provider == provider_name).first()
    if row and row.api_key_encrypted:
        return _decrypt_key(row.api_key_encrypted)
    return ""


def get_all_provider_keys(db: Session) -> Dict[str, str]:
    rows = db.query(ProviderKey).all()
    return {r.provider: _decrypt_key(r.api_key_encrypted) for r in rows if r.api_key_encrypted}


@router.get("", response_model=List[KeyResponse])
def list_keys(db: Session = Depends(get_db)):
    providers = registry.list_providers()
    rows = {r.provider: r for r in db.query(ProviderKey).all()}
    result = []
    for p in providers:
        name = p["name"]
        row = rows.get(name)
        encrypted = row.api_key_encrypted if row else ""
        preview = ""
        if encrypted:
            decrypted = _decrypt_key(encrypted)
            preview = decrypted[-4:] if len(decrypted) >= 4 else decrypted
        result.append(KeyResponse(
            provider=name,
            label=row.label if row else "",
            key_preview=preview,
            has_key=bool(encrypted),
            created_at=row.created_at if row else None,
            updated_at=row.updated_at if row else None,
        ))
    return result


@router.put("/{provider}", response_model=KeyResponse)
def set_key(provider: str, payload: SetKeyRequest, db: Session = Depends(get_db)):
    providers = {p["name"] for p in registry.list_providers()}
    if provider not in providers:
        raise HTTPException(400, f"Unknown provider '{provider}'. Available: {sorted(providers)}")

    row = db.query(ProviderKey).filter(ProviderKey.provider == provider).first()
    if row:
        row.api_key_encrypted = _encrypt_key(payload.api_key)
        row.label = payload.label
        row.updated_at = datetime.now(timezone.utc)
    else:
        row = ProviderKey(
            provider=provider,
            api_key_encrypted=_encrypt_key(payload.api_key),
            label=payload.label,
        )
        db.add(row)
    db.commit()
    db.refresh(row)

    preview = payload.api_key[-4:] if len(payload.api_key) >= 4 else payload.api_key
    return KeyResponse(
        provider=row.provider,
        label=row.label,
        key_preview=preview,
        has_key=True,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.delete("/{provider}", status_code=204)
def delete_key(provider: str, db: Session = Depends(get_db)):
    row = db.query(ProviderKey).filter(ProviderKey.provider == provider).first()
    if row:
        db.delete(row)
        db.commit()


@router.post("/{provider}/test")
def test_key(provider: str, db: Session = Depends(get_db)):
    providers = {p["name"] for p in registry.list_providers()}
    if provider not in providers:
        raise HTTPException(400, f"Unknown provider '{provider}'")

    api_key = get_provider_key(provider, db)
    if not api_key:
        raise HTTPException(400, f"No API key configured for {provider}")

    client = registry.get(provider, api_key=api_key)
    result = client.query("Reply with exactly one word: ok")
    status = result.get("status_code", "500")
    return {
        "status": "ok" if status == "200" else "error",
        "response_preview": (result.get("response") or "")[:100],
        "latency": result.get("latency", 0),
        "status_code": status,
    }
