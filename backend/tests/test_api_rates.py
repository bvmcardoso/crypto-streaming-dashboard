from fastapi.testclient import TestClient


def test_get_current_returns_valid_structure(client: TestClient) -> None:
    # The endpoint should return a JSON object with a "pairs" key
    response = client.get("/api/v1/rates/current")
    assert response.status_code == 200

    data = response.json()
    assert "pairs" in data
    assert isinstance(data["pairs"], list)

    # If there are pairs, validate basic structure
    if data["pairs"]:
        item = data["pairs"][0]
        assert "pair" in item
        assert "price" in item
        assert "hourly_avg" in item
        assert "last_update" in item
