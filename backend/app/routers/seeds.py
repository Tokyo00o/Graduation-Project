from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.seed import SeedTemplate
from app.schemas.seed import ConvertMultiTurnResponse, ConversationTurn, SeedCreate, SeedResponse, SeedUpdate
from app.schemas.common import StatusResponse
from app.services.auth import get_current_user
from app.services.multi_turn import (
    apply_wrapper,
    convert_single_to_multi_turn,
    get_available_wrappers,
)
from app.services.seed_parser import parse_file

router = APIRouter(prefix="/api/v1/projects/{project_id}/seeds", tags=["Seeds"], dependencies=[Depends(get_current_user)])


def _get_project(project_id: str, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.post("", response_model=SeedResponse, status_code=201)
def create_seed(project_id: str, payload: SeedCreate, db: Session = Depends(get_db)):
    _get_project(project_id, db)
    tags_str = ",".join(payload.tags) if payload.tags else ""
    conv_json = ""
    if payload.conversation:
        import json
        conv_json = json.dumps([t.model_dump() for t in payload.conversation], ensure_ascii=False)
    seed = SeedTemplate(
        project_id=project_id,
        content=payload.content,
        tags=tags_str,
        is_multi_turn=payload.is_multi_turn or bool(payload.conversation),
        conversation=conv_json,
    )
    db.add(seed)
    db.commit()
    db.refresh(seed)
    return seed


@router.post("/upload", status_code=201)
async def upload_seeds(project_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    _get_project(project_id, db)
    content = await file.read()
    rows = parse_file(file.filename or "seeds.csv", content)
    seeds = []
    for r in rows:
        seed = SeedTemplate(project_id=project_id, content=r.content, tags=",".join(r.tags))
        db.add(seed)
        seeds.append(seed)
    db.commit()
    for s in seeds:
        db.refresh(s)
    return {"imported": len(seeds), "seeds": [{"id": s.id, "content": s.content[:80], "tags": s.tags} for s in seeds]}


@router.get("", response_model=List[SeedResponse])
def list_seeds(
    project_id: str,
    tag: Optional[str] = Query(None),
    version: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    _get_project(project_id, db)
    q = db.query(SeedTemplate).filter(SeedTemplate.project_id == project_id)
    if tag:
        q = q.filter(SeedTemplate.tags.contains(tag))
    if version:
        q = q.filter(SeedTemplate.version == version)
    return q.all()


@router.get("/{seed_id}", response_model=SeedResponse)
def get_seed(project_id: str, seed_id: str, db: Session = Depends(get_db)):
    _get_project(project_id, db)
    seed = db.query(SeedTemplate).filter(SeedTemplate.id == seed_id, SeedTemplate.project_id == project_id).first()
    if not seed:
        raise HTTPException(404, "Seed not found")
    return seed


@router.patch("/{seed_id}", response_model=SeedResponse)
def update_seed(project_id: str, seed_id: str, payload: SeedUpdate, db: Session = Depends(get_db)):
    _get_project(project_id, db)
    seed = db.query(SeedTemplate).filter(SeedTemplate.id == seed_id, SeedTemplate.project_id == project_id).first()
    if not seed:
        raise HTTPException(404, "Seed not found")
    if payload.content is not None:
        seed.content = payload.content
        seed.version += 1
    if payload.tags is not None:
        seed.tags = ",".join(payload.tags)
    if payload.is_multi_turn is not None:
        seed.is_multi_turn = payload.is_multi_turn
    if payload.conversation is not None:
        import json
        seed.conversation = json.dumps([t.model_dump() for t in payload.conversation], ensure_ascii=False)
        seed.is_multi_turn = True
    db.commit()
    db.refresh(seed)
    return seed


@router.delete("/{seed_id}", status_code=204)
def delete_seed(project_id: str, seed_id: str, db: Session = Depends(get_db)):
    _get_project(project_id, db)
    seed = db.query(SeedTemplate).filter(SeedTemplate.id == seed_id, SeedTemplate.project_id == project_id).first()
    if not seed:
        raise HTTPException(404, "Seed not found")
    db.delete(seed)
    db.commit()


# --- Multi-turn conversion ---

@router.get("/multi-turn/wrappers")
def list_wrappers():
    return get_available_wrappers()


@router.post("/{seed_id}/convert-multi-turn", response_model=ConvertMultiTurnResponse, status_code=201)
def convert_seed_to_multi_turn(
    project_id: str,
    seed_id: str,
    wrapper: str = Query("", description="Specific wrapper name, or empty for random"),
    db: Session = Depends(get_db),
):
    _get_project(project_id, db)
    seed = db.query(SeedTemplate).filter(SeedTemplate.id == seed_id, SeedTemplate.project_id == project_id).first()
    if not seed:
        raise HTTPException(404, "Seed not found")

    conversation = apply_wrapper(seed.content, wrapper) if wrapper else convert_single_to_multi_turn(seed.content)
    conv_json = json.dumps(conversation, ensure_ascii=False)
    new_seed = SeedTemplate(
        project_id=project_id,
        content=seed.content,
        tags=seed.tags + ",multi-turn",
        is_multi_turn=True,
        conversation=conv_json,
    )
    db.add(new_seed)
    db.commit()
    db.refresh(new_seed)

    resp = SeedResponse.model_validate(new_seed)
    return ConvertMultiTurnResponse(original_id=seed_id, new_seeds=[resp])


@router.post("/multi-turn/convert-bulk", response_model=List[SeedResponse], status_code=201)
def convert_bulk_seeds_to_multi_turn(
    project_id: str,
    wrapper: str = Query("", description="Wrapper name, or empty for random"),
    seed_ids: Optional[str] = Query(None, description="Comma-separated seed IDs, or empty for all"),
    db: Session = Depends(get_db),
):
    _get_project(project_id, db)
    q = db.query(SeedTemplate).filter(SeedTemplate.project_id == project_id)
    if seed_ids:
        ids = [s.strip() for s in seed_ids.split(",") if s.strip()]
        q = q.filter(SeedTemplate.id.in_(ids))
    seeds = q.all()

    new_seeds = []
    for seed in seeds:
        conversation = apply_wrapper(seed.content, wrapper) if wrapper else convert_single_to_multi_turn(seed.content)
        conv_json = json.dumps(conversation, ensure_ascii=False)
        ns = SeedTemplate(
            project_id=project_id,
            content=seed.content,
            tags=seed.tags + ",multi-turn",
            is_multi_turn=True,
            conversation=conv_json,
        )
        db.add(ns)
        new_seeds.append(ns)
    db.commit()
    for ns in new_seeds:
        db.refresh(ns)
    return new_seeds
