def test_report_not_found(client):
    resp = client.get("/api/v1/reports/job_nonexistent")
    assert resp.status_code == 404


def test_report_empty_job(client, sample_job):
    resp = client.get(f"/api/v1/reports/{sample_job['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["job_id"] == sample_job["id"]
    assert data["summary"]["status"] == sample_job["status"]
    assert data["iterations"] == []
    assert data["top_jailbreaks"] == []
    assert data["worst_performers"] == []


def test_report_json_export(client, sample_job):
    resp = client.get(f"/api/v1/reports/{sample_job['id']}/export/json")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert "report_" in resp.headers.get("content-disposition", "")


def test_report_csv_export(client, sample_job):
    resp = client.get(f"/api/v1/reports/{sample_job['id']}/export/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


def test_report_html_export(client, sample_job):
    resp = client.get(f"/api/v1/reports/{sample_job['id']}/export/html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "FuzzGuard Report" in resp.text


def test_report_summary_all(client, sample_job):
    resp = client.get("/api/v1/reports/summary/all")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    ids = [j["job_id"] for j in data]
    assert sample_job["id"] in ids
