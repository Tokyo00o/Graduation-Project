def test_create_project(client):
    resp = client.post("/api/v1/projects", json={"name": "New Project", "description": "desc"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Project"
    assert data["id"].startswith("proj_")


def test_list_projects(client, sample_project):
    resp = client.get("/api/v1/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    ids = [p["id"] for p in data]
    assert sample_project["id"] in ids


def test_get_project(client, sample_project):
    resp = client.get(f"/api/v1/projects/{sample_project['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == sample_project["name"]


def test_get_project_not_found(client):
    resp = client.get("/api/v1/projects/proj_nonexistent")
    assert resp.status_code == 404


def test_delete_project(client, sample_project):
    resp = client.delete(f"/api/v1/projects/{sample_project['id']}")
    assert resp.status_code == 204
    resp2 = client.get(f"/api/v1/projects/{sample_project['id']}")
    assert resp2.status_code == 404
