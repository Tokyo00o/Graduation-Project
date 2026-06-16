def test_list_keys_empty(client):
    resp = client.get("/api/v1/keys")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for k in data:
        assert not k["has_key"]


def test_set_key(client):
    resp = client.put("/api/v1/keys/openai", json={"api_key": "sk-test-abcdef123456", "label": "My key"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "openai"
    assert data["has_key"]
    assert data["key_preview"] == "3456"


def test_set_key_invalid_provider(client):
    resp = client.put("/api/v1/keys/badprovider", json={"api_key": "test"})
    assert resp.status_code == 400


def test_get_keys_after_set(client):
    client.put("/api/v1/keys/anthropic", json={"api_key": "sk-ant-test"})
    resp = client.get("/api/v1/keys")
    data = resp.json()
    anthropic = next(k for k in data if k["provider"] == "anthropic")
    assert anthropic["has_key"]


def test_delete_key(client):
    client.put("/api/v1/keys/cohere", json={"api_key": "test1234"})
    resp = client.delete("/api/v1/keys/cohere")
    assert resp.status_code == 204
    resp2 = client.get("/api/v1/keys")
    cohere = next(k for k in resp2.json() if k["provider"] == "cohere")
    assert not cohere["has_key"]


def test_test_key_no_key(client):
    resp = client.post("/api/v1/keys/mistral/test")
    assert resp.status_code == 400
    assert "No API key" in resp.json()["detail"]
