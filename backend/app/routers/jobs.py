from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.iteration import JobIteration
from app.models.job import FuzzJob
from app.models.judgment import JudgmentResult
from app.models.mutation import MutatedTemplate
from app.models.project import Project
from app.models.response import TargetResponse
from app.schemas.common import PaginatedResponse, StatusResponse
from app.schemas.iterations import IterationFullResponse
from app.schemas.job import JobCreate, JobResponse
from app.services.auth import get_current_user
from app.services.engine import run_fuzz_job, stop_job_worker
from app.services.mcts_tree import MCTSTreeService

router = APIRouter(prefix="/api/v1", tags=["Jobs"], dependencies=[Depends(get_current_user)])


def _get_project(project_id: str, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.post("/projects/{project_id}/jobs", response_model=JobResponse, status_code=201)
def create_job(
    project_id: str,
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    _get_project(project_id, db)
    job = FuzzJob(
        project_id=project_id,
        strategy=payload.strategy,
        budget=payload.budget,
        judge=payload.judge,
        target_model=payload.target_model,
        status="created",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_fuzz_job, job.id, payload.seed_ids)
    return job


@router.get("/projects/{project_id}/jobs", response_model=List[JobResponse])
def list_jobs(project_id: str, db: Session = Depends(get_db)):
    _get_project(project_id, db)
    return db.query(FuzzJob).filter(FuzzJob.project_id == project_id).all()


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(FuzzJob).filter(FuzzJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/jobs/{job_id}/stop", response_model=StatusResponse)
def stop_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(FuzzJob).filter(FuzzJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    job.status = "stopping"
    db.commit()
    stop_job_worker(job_id)
    return StatusResponse(status="stopping")


@router.get("/jobs/{job_id}/results")
def get_job_results(
    job_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    job = db.query(FuzzJob).filter(FuzzJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    q = db.query(JobIteration).filter(JobIteration.job_id == job_id)
    total = q.count()

    if sort:
        desc = sort.startswith("-")
        col = sort.lstrip("-")
        order_col = getattr(JobIteration, col, None)
        if order_col:
            q = q.order_by(order_col.desc() if desc else order_col.asc())

    iterations = q.offset((page - 1) * limit).limit(limit).all()
    items = []
    for it in iterations:
        mutation = db.query(MutatedTemplate).filter(MutatedTemplate.iteration_id == it.id).first()
        resp = db.query(TargetResponse).filter(TargetResponse.iteration_id == it.id).first()
        judgment = db.query(JudgmentResult).filter(JudgmentResult.iteration_id == it.id).first()
        items.append(IterationFullResponse(
            id=it.id,
            job_id=it.job_id,
            iteration_number=it.iteration_number,
            reward=it.reward,
            status=it.status,
            created_at=it.created_at,
            mutation=mutation,
            response=resp,
            judgment=judgment,
        ))

    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.get("/jobs/{job_id}/report", response_model=StatusResponse)
def generate_report(job_id: str, db: Session = Depends(get_db)):
    job = db.query(FuzzJob).filter(FuzzJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return StatusResponse(status="ok", data={"report_url": f"/api/v1/reports/{job_id}"})


@router.get("/jobs/{job_id}/mcts-tree")
def get_mcts_tree(job_id: str, db: Session = Depends(get_db)):
    job = db.query(FuzzJob).filter(FuzzJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    tree = MCTSTreeService.build_tree_snapshot(db, job_id)
    if not tree:
        return {"nodes": []}
    return tree
