from fastapi.testclient import TestClient

from app.main import app
from app.services.brightdata import BrightDataError, get_bright_data_client


class FakeBrightDataClient:
    def __init__(self, *, collector_id: str = "c_demo", result=None, error: Exception | None = None):
        self.collector_id = collector_id
        self.result = [{"title": "Launch announcement"}] if result is None else result
        self.error = error

    def create_scraper(self, name: str, url: str, description: str) -> str:
        if self.error:
            raise self.error
        return self.collector_id

    def collect(self, collector_id: str, source_url: str):
        if self.error:
            raise self.error
        return "j_demo", self.result


def create_source(client: TestClient, *, description: str | None = "Extract titles") -> dict:
    competitor = client.post(
        "/competitors",
        json={"name": "Radar Co", "website_url": "https://radar.example"},
    ).json()
    payload = {
        "name": "Newsroom",
        "url": "https://radar.example/news",
        "extraction_description": description,
    }
    response = client.post(f"/competitors/{competitor['id']}/sources", json=payload)
    assert response.status_code == 201
    return response.json()


def use_fake_client(fake: FakeBrightDataClient) -> None:
    app.dependency_overrides[get_bright_data_client] = lambda: fake


def test_successful_scraper_creation(client: TestClient) -> None:
    source = create_source(client)
    use_fake_client(FakeBrightDataClient(collector_id="c_created"))

    response = client.post(f"/sources/{source['id']}/scraper")

    assert response.status_code == 200
    assert response.json() == {"collector_id": "c_created", "status": "done"}
    assert client.get(f"/sources/{source['id']}").json()["collector_id"] == "c_created"


def test_failed_scraper_creation(client: TestClient) -> None:
    source = create_source(client)
    use_fake_client(FakeBrightDataClient(error=BrightDataError("Bright Data API returned 401")))

    response = client.post(f"/sources/{source['id']}/scraper")

    assert response.status_code == 502
    assert client.get(f"/sources/{source['id']}").json()["collector_id"] is None


def test_successful_collection_and_history(client: TestClient) -> None:
    source = create_source(client)
    use_fake_client(FakeBrightDataClient(collector_id="c_created"))
    assert client.post(f"/sources/{source['id']}/scraper").status_code == 200

    response = client.post(f"/sources/{source['id']}/collect")

    assert response.status_code == 200
    run = response.json()
    assert run["status"] == "succeeded"
    assert run["health_status"] == "healthy"
    assert run["record_count"] == 1
    assert run["bright_data_collection_id"] == "j_demo"
    assert client.get(f"/sources/{source['id']}/runs").json() == [run]


def test_failed_collection_is_persisted(client: TestClient) -> None:
    source = create_source(client)
    use_fake_client(FakeBrightDataClient(collector_id="c_created"))
    client.post(f"/sources/{source['id']}/scraper")
    use_fake_client(FakeBrightDataClient(error=BrightDataError("Bright Data request failed")))

    run = client.post(f"/sources/{source['id']}/collect").json()

    assert run["status"] == "failed"
    assert run["health_status"] == "failed"
    assert run["error_message"] == "Bright Data request failed"


def test_empty_or_malformed_results_are_degraded(client: TestClient) -> None:
    source = create_source(client)
    use_fake_client(FakeBrightDataClient(collector_id="c_created"))
    client.post(f"/sources/{source['id']}/scraper")

    use_fake_client(FakeBrightDataClient(result=[]))
    empty_run = client.post(f"/sources/{source['id']}/collect").json()
    assert empty_run["health_status"] == "degraded"
    assert empty_run["record_count"] == 0

    use_fake_client(FakeBrightDataClient(result={"status": "unexpected"}))
    malformed_run = client.post(f"/sources/{source['id']}/collect").json()
    assert malformed_run["health_status"] == "degraded"
    assert malformed_run["error_message"] == "Bright Data returned an unexpected dataset format"


def test_missing_source_and_source_without_scraper(client: TestClient) -> None:
    assert client.post("/sources/999/collect").status_code == 404
    assert client.get("/sources/999/runs").status_code == 404

    source = create_source(client)
    response = client.post(f"/sources/{source['id']}/collect")
    assert response.status_code == 409
