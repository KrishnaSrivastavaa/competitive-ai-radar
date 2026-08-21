from fastapi.testclient import TestClient


def create_competitor(client: TestClient) -> dict:
    response = client.post(
        "/competitors",
        json={
            "name": "Acme AI",
            "website_url": "https://acme.example",
            "description": "A public AI competitor",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_health_check(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_create_list_and_get_competitor(client: TestClient) -> None:
    competitor = create_competitor(client)

    assert client.get("/competitors").json() == [competitor]
    assert client.get(f"/competitors/{competitor['id']}").json() == competitor


def test_missing_competitor_returns_not_found(client: TestClient) -> None:
    assert client.get("/competitors/999").status_code == 404


def test_create_and_get_source(client: TestClient) -> None:
    competitor = create_competitor(client)
    response = client.post(
        f"/competitors/{competitor['id']}/sources",
        json={
            "name": "Product updates",
            "url": "https://acme.example/updates",
            "source_type": "news",
        },
    )

    assert response.status_code == 201
    source = response.json()
    assert source["competitor_id"] == competitor["id"]
    assert client.get(f"/sources/{source['id']}").json() == source


def test_source_requires_existing_competitor(client: TestClient) -> None:
    response = client.post(
        "/competitors/999/sources",
        json={"name": "Product updates", "url": "https://acme.example/updates"},
    )
    assert response.status_code == 404
