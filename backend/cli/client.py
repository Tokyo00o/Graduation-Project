import time
from typing import Any, Optional
from urllib.parse import urljoin

import httpx


class FuzzGuardClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def _url(self, path: str) -> str:
        return urljoin(self.base_url, path)

    # Projects
    def list_projects(self) -> list[dict]:
        r = self.client.get("/api/v1/projects")
        r.raise_for_status()
        return r.json()

    def get_project(self, project_id: str) -> dict:
        r = self.client.get(f"/api/v1/projects/{project_id}")
        r.raise_for_status()
        return r.json()

    def create_project(self, name: str, description: str = "") -> dict:
        r = self.client.post("/api/v1/projects", json={"name": name, "description": description})
        r.raise_for_status()
        return r.json()

    def delete_project(self, project_id: str) -> None:
        r = self.client.delete(f"/api/v1/projects/{project_id}")
        r.raise_for_status()

    # Seeds
    def list_seeds(self, project_id: str) -> list[dict]:
        r = self.client.get(f"/api/v1/projects/{project_id}/seeds")
        r.raise_for_status()
        return r.json()

    def create_seed(self, project_id: str, content: str, tags: Optional[list[str]] = None) -> dict:
        r = self.client.post(f"/api/v1/projects/{project_id}/seeds", json={"content": content, "tags": tags or []})
        r.raise_for_status()
        return r.json()

    # Target Models
    def list_targets(self) -> list[dict]:
        r = self.client.get("/api/v1/models/targets")
        r.raise_for_status()
        return r.json()

    def register_target(self, provider: str, model: str, label: str = "", api_key: str = "") -> dict:
        body = {"provider": provider, "model": model}
        if label:
            body["label"] = label
        if api_key:
            body["api_key"] = api_key
        r = self.client.post("/api/v1/models/targets", json=body)
        r.raise_for_status()
        return r.json()

    def list_providers(self) -> list[dict]:
        r = self.client.get("/api/v1/models/providers")
        r.raise_for_status()
        return r.json()

    # API Keys
    def set_key(self, provider: str, api_key: str, label: str = "") -> dict:
        body = {"api_key": api_key}
        if label:
            body["label"] = label
        r = self.client.put(f"/api/v1/keys/{provider}", json=body)
        r.raise_for_status()
        return r.json()

    def list_keys(self) -> list[dict]:
        r = self.client.get("/api/v1/keys")
        r.raise_for_status()
        return r.json()

    def delete_key(self, provider: str) -> None:
        r = self.client.delete(f"/api/v1/keys/{provider}")
        r.raise_for_status()

    def test_key(self, provider: str) -> dict:
        r = self.client.post(f"/api/v1/keys/{provider}/test")
        r.raise_for_status()
        return r.json()

    # Jobs
    def create_job(self, project_id: str, strategy: str = "random", budget: int = 10,
                   judge: str = "rule", target_model: Optional[str] = None,
                   seed_ids: Optional[list[str]] = None) -> dict:
        body: dict[str, Any] = {"strategy": strategy, "budget": budget, "judge": judge}
        if target_model:
            body["target_model"] = target_model
        if seed_ids:
            body["seed_ids"] = seed_ids
        r = self.client.post(f"/api/v1/projects/{project_id}/jobs", json=body)
        r.raise_for_status()
        return r.json()

    def list_jobs(self, project_id: str) -> list[dict]:
        r = self.client.get(f"/api/v1/projects/{project_id}/jobs")
        r.raise_for_status()
        return r.json()

    def get_job(self, job_id: str) -> dict:
        r = self.client.get(f"/api/v1/jobs/{job_id}")
        r.raise_for_status()
        return r.json()

    def stop_job(self, job_id: str) -> dict:
        r = self.client.post(f"/api/v1/jobs/{job_id}/stop")
        r.raise_for_status()
        return r.json()

    def get_results(self, job_id: str, page: int = 1, limit: int = 50, sort: str = "-reward") -> dict:
        r = self.client.get(f"/api/v1/jobs/{job_id}/results", params={"page": page, "limit": limit, "sort": sort})
        r.raise_for_status()
        return r.json()

    # Reports
    def get_report(self, job_id: str) -> dict:
        r = self.client.get(f"/api/v1/reports/{job_id}")
        r.raise_for_status()
        return r.json()

    def export_json(self, job_id: str) -> bytes:
        r = self.client.get(f"/api/v1/reports/{job_id}/export/json")
        r.raise_for_status()
        return r.content

    def export_csv(self, job_id: str) -> bytes:
        r = self.client.get(f"/api/v1/reports/{job_id}/export/csv")
        r.raise_for_status()
        return r.content

    def export_html(self, job_id: str) -> bytes:
        r = self.client.get(f"/api/v1/reports/{job_id}/export/html")
        r.raise_for_status()
        return r.content

    def report_summary(self, limit: int = 10) -> list[dict]:
        r = self.client.get("/api/v1/reports/summary/all", params={"limit": limit})
        r.raise_for_status()
        return r.json()

    # Judges
    def list_judges(self) -> list[dict]:
        r = self.client.get("/api/v1/judges")
        r.raise_for_status()
        return r.json()

    def train_judge(self) -> dict:
        r = self.client.post("/api/v1/judges/train")
        r.raise_for_status()
        return r.json()

    # Benchmarks
    def list_public_benchmarks(self) -> list[dict]:
        r = self.client.get("/api/v1/benchmarks/public")
        r.raise_for_status()
        return r.json()

    # Helpers
    def find_or_create_project(self, name: str) -> dict:
        projects = self.list_projects()
        for p in projects:
            if p["name"] == name:
                return p
        return self.create_project(name)

    def wait_for_job(self, job_id: str, poll_interval: float = 2.0, timeout: float = 300.0) -> dict:
        deadline = time.time() + timeout
        while time.time() < deadline:
            job = self.get_job(job_id)
            if job["status"] in ("completed", "failed", "stopped"):
                return job
            time.sleep(poll_interval)
        raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")
