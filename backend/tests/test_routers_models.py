def test_list_judges(client):
    resp = client.get("/api/v1/judges")
    assert resp.status_code == 200
    data = resp.json()
    names = [j["name"] for j in data]
    assert "roberta" in names
    assert "rule" in names
    assert "gpt4" in names


def test_list_providers(client):
    resp = client.get("/api/v1/models/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    names = [p["name"] for p in data]
    assert "openai" in names
    assert "anthropic" in names
    for p in data:
        assert "has_key" in p
        assert "key_preview" in p


def test_get_default_training_data(client):
    resp = client.get("/api/v1/judges/default-train")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    for item in data:
        assert "text" in item
        assert "label" in item


def test_register_target_model(client):
    resp = client.post("/api/v1/models/targets", json={
        "provider": "openai", "model": "gpt-4o"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"].startswith("tgt_")
    assert data["provider"] == "openai"
    assert data["status"] == "inactive"


def test_register_target_invalid_provider(client):
    resp = client.post("/api/v1/models/targets", json={
        "provider": "unknown_provider", "model": "x"
    })
    assert resp.status_code == 400


def test_list_target_models(client, sample_target_model):
    resp = client.get("/api/v1/models/targets")
    assert resp.status_code == 200
    data = resp.json()
    ids = [t["id"] for t in data]
    assert sample_target_model["id"] in ids


def test_update_target_model(client, sample_target_model):
    resp = client.patch(f"/api/v1/models/targets/{sample_target_model['id']}", json={"label": "Updated label"})
    assert resp.status_code == 200
    assert resp.json()["label"] == "Updated label"


def test_delete_target_model(client, sample_target_model):
    resp = client.delete(f"/api/v1/models/targets/{sample_target_model['id']}")
    assert resp.status_code == 204
