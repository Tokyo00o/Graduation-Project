from unittest.mock import patch


def test_create_job(client, sample_project, sample_seed):
    pid = sample_project["id"]
    resp = client.post(f"/api/v1/projects/{pid}/jobs", json={
        "strategy": "round_robin", "budget": 5, "target_model": "", "seed_ids": [sample_seed["id"]]
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"].startswith("job_")
    assert data["status"] == "created"
    assert data["strategy"] == "round_robin"


def test_list_jobs(client, sample_project, sample_job):
    pid = sample_project["id"]
    resp = client.get(f"/api/v1/projects/{pid}/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    ids = [j["id"] for j in data]
    assert sample_job["id"] in ids


def test_get_job(client, sample_job):
    resp = client.get(f"/api/v1/jobs/{sample_job['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == sample_job["id"]


def test_get_job_not_found(client):
    resp = client.get("/api/v1/jobs/job_nonexistent")
    assert resp.status_code == 404


def test_stop_job(client, sample_job):
    resp = client.post(f"/api/v1/jobs/{sample_job['id']}/stop")
    assert resp.status_code == 200
    assert resp.json()["status"] == "stopping"


def test_job_results_empty(client, sample_job):
    resp = client.get(f"/api/v1/jobs/{sample_job['id']}/results")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@patch("app.routers.jobs.run_fuzz_job")
def test_create_job_triggers_background(mock_run, client, sample_project, sample_seed):
    pid = sample_project["id"]
    resp = client.post(f"/api/v1/projects/{pid}/jobs", json={
        "strategy": "random", "budget": 3, "seed_ids": [sample_seed["id"]]
    })
    assert resp.status_code == 201
    mock_run.assert_called_once()
    args, _ = mock_run.call_args
    assert args[0] == resp.json()["id"]


def test_job_report_stub(client, sample_job):
    resp = client.get(f"/api/v1/jobs/{sample_job['id']}/report")
    assert resp.status_code == 200
    data = resp.json()
    assert "report_url" in data.get("data", {})
