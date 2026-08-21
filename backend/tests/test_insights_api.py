from fastapi.testclient import TestClient

from app.main import app
from app.schemas.insight import InsightAnalysis
from app.services.brightdata import get_bright_data_client
from app.services.llm_analysis import LLMError, LLMTimeoutError, get_llm_client


class SequencedBrightData:
    def __init__(self, results):
        self.results = iter(results)

    def create_scraper(self, name, url, description):
        return "c_test"

    def collect(self, collector_id, source_url):
        return "j_test", next(self.results)


class FakeLLM:
    def __init__(self, result=None, error=None):
        self.result = result or InsightAnalysis(
            title="Pricing changed",
            analysis="Observed price changed from 29.99 to 39.99.",
            competitive_impact="This may affect competitive positioning.",
            recommendation="Review comparable pricing.",
            confidence=0.8,
            evidence=[{"source_url": "https://example.com/products/1", "reason": "Verified before and after records."}],
        )
        self.error = error

    def analyze_change(self, evidence):
        if self.error:
            raise self.error
        return self.result


def setup_change(client: TestClient, results) -> tuple[dict, dict]:
    competitor = client.post("/competitors", json={"name": "Insight Co", "website_url": "https://example.com"}).json()
    source = client.post(
        f"/competitors/{competitor['id']}/sources",
        json={"name": "Products", "url": "https://example.com/products", "extraction_description": "Extract products"},
    ).json()
    bright_data = SequencedBrightData(results)
    app.dependency_overrides[get_bright_data_client] = lambda: bright_data
    client.post(f"/sources/{source['id']}/scraper")
    for _ in results:
        client.post(f"/sources/{source['id']}/collect")
    return competitor, client.get(f"/sources/{source['id']}/changes").json()[0]


def test_modified_change_creates_and_returns_insight(client: TestClient) -> None:
    previous = [{"product_page_url": "https://example.com/products/1", "price": 29.99}]
    current = [{"product_page_url": "https://example.com/products/1", "price": 39.99}]
    competitor, change = setup_change(client, [previous, current])
    app.dependency_overrides[get_llm_client] = lambda: FakeLLM()

    response = client.post(f"/changes/{change['id']}/analyze")

    assert response.status_code == 201
    insight = response.json()
    assert insight["competitor_id"] == competitor["id"]
    assert insight["change_id"] == change["id"]
    assert insight["evidence"][0]["source_url"] == "https://example.com/products/1"
    assert client.get(f"/insights/{insight['id']}").json() == insight
    assert client.get(f"/competitors/{competitor['id']}/insights").json() == [insight]


def test_added_and_removed_changes_can_be_analyzed(client: TestClient) -> None:
    base = [{"url": "https://example.com/1", "title": "A"}]
    _, added = setup_change(client, [base, base + [{"url": "https://example.com/2", "title": "B"}]])
    app.dependency_overrides[get_llm_client] = lambda: FakeLLM()
    assert client.post(f"/changes/{added['id']}/analyze").status_code == 201

    # New test database context is avoided; use a separate source in this test.
    competitor = client.post("/competitors", json={"name": "Removed Co", "website_url": "https://removed.example"}).json()
    source = client.post(f"/competitors/{competitor['id']}/sources", json={"name":"Products","url":"https://removed.example/products","extraction_description":"Extract"}).json()
    bright_data = SequencedBrightData([base + [{"url":"https://example.com/2"}], base])
    app.dependency_overrides[get_bright_data_client] = lambda: bright_data
    client.post(f"/sources/{source['id']}/scraper")
    client.post(f"/sources/{source['id']}/collect"); client.post(f"/sources/{source['id']}/collect")
    removed = client.get(f"/sources/{source['id']}/changes").json()[0]
    assert client.post(f"/changes/{removed['id']}/analyze").status_code == 201


def test_initial_unchanged_invalid_output_and_errors_do_not_persist(client: TestClient) -> None:
    row = [{"url": "https://example.com/1"}]
    _, initial = setup_change(client, [row])
    assert client.post(f"/changes/{initial['id']}/analyze").status_code == 409

    competitor = client.post("/competitors", json={"name": "Same Co", "website_url": "https://same.example"}).json()
    source = client.post(f"/competitors/{competitor['id']}/sources", json={"name":"Products","url":"https://same.example/products","extraction_description":"Extract"}).json()
    bright_data = SequencedBrightData([row, row])
    app.dependency_overrides[get_bright_data_client] = lambda: bright_data
    client.post(f"/sources/{source['id']}/scraper"); client.post(f"/sources/{source['id']}/collect"); client.post(f"/sources/{source['id']}/collect")
    unchanged = client.get(f"/sources/{source['id']}/changes").json()[0]
    assert client.post(f"/changes/{unchanged['id']}/analyze").status_code == 409

    modified_source = client.post(f"/competitors/{competitor['id']}/sources", json={"name":"Other","url":"https://same.example/other","extraction_description":"Extract"}).json()
    bright_data = SequencedBrightData([[{"url":"https://a","price":1}], [{"url":"https://a","price":2}]])
    app.dependency_overrides[get_bright_data_client] = lambda: bright_data
    client.post(f"/sources/{modified_source['id']}/scraper"); client.post(f"/sources/{modified_source['id']}/collect"); client.post(f"/sources/{modified_source['id']}/collect")
    change = client.get(f"/sources/{modified_source['id']}/changes").json()[0]
    app.dependency_overrides[get_llm_client] = lambda: FakeLLM(result={"confidence": 2})
    assert client.post(f"/changes/{change['id']}/analyze").status_code == 502
    app.dependency_overrides[get_llm_client] = lambda: FakeLLM(error=LLMError("failure"))
    assert client.post(f"/changes/{change['id']}/analyze").status_code == 502
    app.dependency_overrides[get_llm_client] = lambda: FakeLLM(error=LLMTimeoutError("timeout"))
    assert client.post(f"/changes/{change['id']}/analyze").status_code == 504
    assert client.get(f"/competitors/{competitor['id']}/insights").json() == []


def test_confidence_bounds_are_validated() -> None:
    base = {"title":"t", "analysis":"a", "competitive_impact":"i", "recommendation":"r", "evidence":[]}
    for confidence in (-0.1, 1.1):
        try:
            InsightAnalysis(**base, confidence=confidence)
        except ValueError:
            continue
        raise AssertionError("confidence outside [0, 1] was accepted")
