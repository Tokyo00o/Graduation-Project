from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.seed import SeedTemplate
from app.models.seed_library import SeedLibraryItem
from app.services.seed_parser import parse_file
from app.schemas.seed import SeedResponse
from app.schemas.seed_library import (
    SeedLibraryBulkImport,
    SeedLibraryCategoryInfo,
    SeedLibraryCreate,
    SeedLibraryResponse,
    SeedLibraryUpdate,
)
from app.services.seed_presets import CURATED_TEMPLATES
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/seed-library", tags=["Seed Library"], dependencies=[Depends(get_current_user)])


@router.get("/categories", response_model=List[SeedLibraryCategoryInfo])
def list_categories(db: Session = Depends(get_db)):
    rows = db.query(SeedLibraryItem.category, SeedLibraryItem.id).all()
    counts: dict[str, int] = {}
    for cat, _ in rows:
        counts[cat] = counts.get(cat, 0) + 1
    return [SeedLibraryCategoryInfo(category=k, count=v) for k, v in sorted(counts.items())]


@router.get("", response_model=List[SeedLibraryResponse])
def list_library(
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    preset_only: bool = Query(False),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(SeedLibraryItem)
    if category:
        q = q.filter(SeedLibraryItem.category == category)
    if difficulty:
        q = q.filter(SeedLibraryItem.difficulty == difficulty)
    if tag:
        q = q.filter(SeedLibraryItem.tags.contains(tag))
    if preset_only:
        q = q.filter(SeedLibraryItem.is_preset == True)
    if search:
        q = q.filter(SeedLibraryItem.content.ilike(f"%{search}%"))
    return q.order_by(SeedLibraryItem.category, SeedLibraryItem.difficulty).all()


@router.get("/{item_id}", response_model=SeedLibraryResponse)
def get_library_item(item_id: str, db: Session = Depends(get_db)):
    item = db.query(SeedLibraryItem).filter(SeedLibraryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Library item not found")
    return item


@router.post("", response_model=SeedLibraryResponse, status_code=201)
def create_library_item(payload: SeedLibraryCreate, db: Session = Depends(get_db)):
    conv_json = ""
    if payload.conversation:
        import json
        conv_json = json.dumps([t.model_dump() for t in payload.conversation], ensure_ascii=False)
    item = SeedLibraryItem(
        content=payload.content,
        category=payload.category,
        tags=",".join(payload.tags) if payload.tags else "",
        difficulty=payload.difficulty,
        effectiveness=payload.effectiveness,
        source=payload.source,
        is_preset=payload.is_preset,
        is_multi_turn=payload.is_multi_turn or bool(payload.conversation),
        conversation=conv_json,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=SeedLibraryResponse)
def update_library_item(item_id: str, payload: SeedLibraryUpdate, db: Session = Depends(get_db)):
    item = db.query(SeedLibraryItem).filter(SeedLibraryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Library item not found")
    if payload.content is not None:
        item.content = payload.content
        item.version += 1
    if payload.category is not None:
        item.category = payload.category
    if payload.tags is not None:
        item.tags = ",".join(payload.tags)
    if payload.difficulty is not None:
        item.difficulty = payload.difficulty
    if payload.effectiveness is not None:
        item.effectiveness = payload.effectiveness
    if payload.source is not None:
        item.source = payload.source
    if payload.is_multi_turn is not None:
        item.is_multi_turn = payload.is_multi_turn
    if payload.conversation is not None:
        import json
        item.conversation = json.dumps([t.model_dump() for t in payload.conversation], ensure_ascii=False)
        item.is_multi_turn = True
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_library_item(item_id: str, db: Session = Depends(get_db)):
    item = db.query(SeedLibraryItem).filter(SeedLibraryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Library item not found")
    db.delete(item)
    db.commit()


@router.post("/bulk-import", response_model=List[SeedLibraryResponse], status_code=201)
def bulk_import(payload: SeedLibraryBulkImport, db: Session = Depends(get_db)):
    items = []
    for c in payload.items:
        item = SeedLibraryItem(
            content=c.content,
            category=c.category,
            tags=",".join(c.tags) if c.tags else "",
            difficulty=c.difficulty,
            effectiveness=c.effectiveness,
            source=c.source,
            is_preset=c.is_preset,
        )
        db.add(item)
        items.append(item)
    db.commit()
    for item in items:
        db.refresh(item)
    return items


@router.post("/upload", status_code=201)
async def upload_library(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    rows = parse_file(file.filename or "seeds.csv", content)
    items = []
    for r in rows:
        item = SeedLibraryItem(
            content=r.content,
            category=r.category,
            tags=",".join(r.tags),
            difficulty=r.difficulty,
            effectiveness=r.effectiveness,
            source=r.source,
        )
        db.add(item)
        items.append(item)
    db.commit()
    for it in items:
        db.refresh(it)
    return {"imported": len(items), "items": [{"id": it.id, "content": it.content[:80], "category": it.category} for it in items]}


@router.post("/{item_id}/import/{project_id}", response_model=SeedResponse, status_code=201)
def import_to_project(item_id: str, project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    item = db.query(SeedLibraryItem).filter(SeedLibraryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Library item not found")
    seed = SeedTemplate(
        project_id=project_id,
        content=item.content,
        tags=item.tags,
        is_multi_turn=item.is_multi_turn,
        conversation=item.conversation,
    )
    db.add(seed)
    db.commit()
    db.refresh(seed)
    return seed


@router.post("/import-bulk/{project_id}", response_model=List[SeedResponse], status_code=201)
def bulk_import_to_project(project_id: str, payload: SeedLibraryBulkImport, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    seeds = []
    for c in payload.items:
        tags_str = ",".join(c.tags) if c.tags else ""
        conv_json = ""
        if c.conversation:
            import json
            conv_json = json.dumps([t.model_dump() for t in c.conversation], ensure_ascii=False)
        seed = SeedTemplate(
            project_id=project_id,
            content=c.content,
            tags=tags_str,
            is_multi_turn=c.is_multi_turn or bool(c.conversation),
            conversation=conv_json,
        )
        db.add(seed)
        seeds.append(seed)
    db.commit()
    for seed in seeds:
        db.refresh(seed)
    return seeds


@router.post("/load-presets", response_model=int, status_code=201)
def load_presets(db: Session = Depends(get_db)):
    existing = db.query(SeedLibraryItem).filter(SeedLibraryItem.is_preset == True).count()
    if existing > 0:
        return existing
    count = 0
    for tpl in CURATED_TEMPLATES:
        conv_json = ""
        if tpl.get("is_multi_turn") and tpl.get("conversation"):
            import json
            conv_json = json.dumps(tpl["conversation"], ensure_ascii=False)
        item = SeedLibraryItem(
            content=tpl["content"],
            category=tpl["category"],
            tags=",".join(tpl["tags"]),
            difficulty=tpl["difficulty"],
            effectiveness=tpl["effectiveness"],
            source=tpl["source"],
            is_preset=tpl["is_preset"],
            is_multi_turn=tpl.get("is_multi_turn", False),
            conversation=conv_json,
        )
        db.add(item)
        count += 1
    db.commit()
    return count
