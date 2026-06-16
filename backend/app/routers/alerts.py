from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertCountResponse, AlertResponse
from app.schemas.common import StatusResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["Alerts"], dependencies=[Depends(get_current_user)])


@router.get("/alerts", response_model=List[AlertResponse])
def list_alerts(
    project_id: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Alert)
    if project_id:
        q = q.filter(Alert.project_id == project_id)
    if unread_only:
        q = q.filter(Alert.is_read == False)
    return q.order_by(Alert.created_at.desc()).limit(limit).all()


@router.get("/alerts/unread-count", response_model=AlertCountResponse)
def unread_alert_count(db: Session = Depends(get_db)):
    count = db.query(Alert).filter(Alert.is_read == False).count()
    return AlertCountResponse(count=count)


@router.post("/alerts/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(alert_id: str, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/alerts/read-all", response_model=StatusResponse)
def mark_all_alerts_read(db: Session = Depends(get_db)):
    db.query(Alert).filter(Alert.is_read == False).update({"is_read": True})
    db.commit()
    return StatusResponse(status="ok")


@router.delete("/alerts/{alert_id}", response_model=StatusResponse)
def delete_alert(alert_id: str, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    db.delete(alert)
    db.commit()
    return StatusResponse(status="deleted")
