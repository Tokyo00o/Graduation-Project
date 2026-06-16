def test_create_seed(client, sample_project):
    pid = sample_project["id"]
    resp = client.post(f"/api/v1/projects/{pid}/seeds", json={"content": "Test seed content"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "Test seed content"
    assert data["id"].startswith("seed_")


def test_list_seeds(client, sample_seed):
    pid = sample_seed["project_id"]
    resp = client.get(f"/api/v1/projects/{pid}/seeds")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    ids = [s["id"] for s in data]
    assert sample_seed["id"] in ids


def test_delete_seed(client, sample_seed):
    pid = sample_seed["project_id"]
    resp = client.delete(f"/api/v1/projects/{pid}/seeds/{sample_seed['id']}")
    assert resp.status_code == 204
    resp2 = client.get(f"/api/v1/projects/{pid}/seeds")
    assert sample_seed["id"] not in [s["id"] for s in resp2.json()]


def test_create_seed_invalid_project(client):
    resp = client.post("/api/v1/projects/proj_nonexistent/seeds", json={"content": "test"})
    assert resp.status_code == 404
