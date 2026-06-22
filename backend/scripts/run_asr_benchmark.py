#!/usr/bin/env python3
"""
ASR Regression Check Script.

Runs a deterministic fuzzing benchmark using MockLLMClient and compares
the resulting ASR against a stored baseline. Exits with non-zero if the ASR
has regressed beyond the configured tolerance.

Usage:
    python scripts/run_asr_benchmark.py

Environment variables:
    FUZZGUARD_ASR_BASELINE: path to baseline JSON (default: scripts/asr_baseline.json)
    FUZZGUARD_ASR_OUTPUT:   path to write result JSON   (default: scripts/asr_result.json)
"""

import json
import os
import sys
import tempfile
import threading
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Point to a temp database before any app imports
import app.config as cfg
_db_path = os.path.join(tempfile.gettempdir(), f"fuzzguard_benchmark_{os.getpid()}.db")
cfg.settings.database_url = f"sqlite:///{_db_path}"

# Now safe to import app modules
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.config import settings

# Import all models so tables get registered
from app.models.project import Project
from app.models.seed import SeedTemplate
from app.models.job import FuzzJob
from app.models.iteration import JobIteration
from app.models.mutation import MutatedTemplate
from app.models.response import TargetResponse
from app.models.judgment import JudgmentResult
from app.models.schedule import JobSchedule
from app.models.alert import Alert

# Re-create engine with the test DB URL
bench_engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

@event.listens_for(bench_engine, "connect")
def _set_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.close()

BenchSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=bench_engine)


def _load_baseline(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def run_benchmark(budget: int = 100, strategy: str = "random") -> float:
    """Run a fuzzing job and return job ASR."""
    Base.metadata.create_all(bind=bench_engine)
    db: Session = BenchSessionLocal()
    try:
        # Create a project
        project = Project(name="CI Benchmark", description="Automated ASR regression check")
        db.add(project)
        db.flush()

        # Import seeds from CURATED_TEMPLATES
        from app.services.seed_presets import CURATED_TEMPLATES
        seed_ids = []
        for tpl in CURATED_TEMPLATES[:10]:  # use first 10 presets
            seed = SeedTemplate(
                project_id=project.id,
                content=tpl["content"],
                tags=",".join(tpl["tags"]),
                is_multi_turn=tpl.get("is_multi_turn", False),
                conversation=json.dumps(tpl.get("conversation", []), ensure_ascii=False) if tpl.get("conversation") else "",
            )
            db.add(seed)
            db.flush()
            seed_ids.append(seed.id)

        # Create the job
        job = FuzzJob(
            project_id=project.id,
            strategy=strategy,
            budget=budget,
            target_model="mock",
            judge="roberta",
            status="created",
        )
        db.add(job)
        db.commit()

        # Override SessionLocal for the engine thread
        import app.database as db_mod
        original_session_local = db_mod.SessionLocal
        db_mod.SessionLocal = BenchSessionLocal

        try:
            from app.services.engine import run_fuzz_job
            job_thread = threading.Thread(target=run_fuzz_job, args=(job.id, seed_ids), daemon=True)
            job_thread.start()
            job_thread.join(timeout=120)

            if job_thread.is_alive():
                print("ERROR: Benchmark job timed out after 120 seconds", file=sys.stderr)
                sys.exit(1)
        finally:
            db_mod.SessionLocal = original_session_local

        # Refresh job to get updated state
        db.refresh(job)
        if job.status != "completed":
            print(f"ERROR: Job did not complete (status={job.status}, error={job.error_message})", file=sys.stderr)
            sys.exit(1)

        return job.asr
    finally:
        db.close()
        # Clean up temp database
        try:
            bench_engine.dispose()
            os.remove(_db_path)
        except OSError:
            pass


def main():
    base_dir = Path(__file__).parent
    baseline_path = os.environ.get("FUZZGUARD_ASR_BASELINE", str(base_dir / "asr_baseline.json"))
    output_path = os.environ.get("FUZZGUARD_ASR_OUTPUT", str(base_dir / "asr_result.json"))

    if not os.path.exists(baseline_path):
        print(f"Baseline file not found: {baseline_path}", file=sys.stderr)
        sys.exit(1)

    baseline = _load_baseline(baseline_path)
    expected_asr = baseline["mock_asr_expected"]
    tolerance = baseline.get("mock_asr_tolerance", 0.05)
    budget = baseline.get("budget", 100)
    strategy = baseline.get("strategy", "random")

    print(f"Running ASR benchmark (budget={budget}, strategy={strategy})...")
    actual_asr = run_benchmark(budget=budget, strategy=strategy)
    print(f"Measured ASR: {actual_asr:.4f} (expected: {expected_asr:.4f} ± {tolerance:.4f})")

    result = {
        "asr": actual_asr,
        "expected_asr": expected_asr,
        "tolerance": tolerance,
        "passed": abs(actual_asr - expected_asr) <= tolerance,
        "budget": budget,
        "strategy": strategy,
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Results written to {output_path}")

    if not result["passed"]:
        diff = actual_asr - expected_asr
        print(f"FAIL: ASR regression detected! Diff={diff:+.4f} (tolerance=±{tolerance})", file=sys.stderr)
        sys.exit(1)

    print("PASS: ASR within expected range.")
    sys.exit(0)


if __name__ == "__main__":
    main()
