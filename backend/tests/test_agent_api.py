from fastapi.testclient import TestClient

from app.main import app
from app.services.brightdata import get_bright_data_client
from app.services.llm_analysis import LLMError, LLMTimeoutError, get_llm_client


class BrightDataSequence:
    def __init__(self, results):
        self.results = iter(results)

    def create_scraper(self, name, url, description):
        return "c_agent"

    def collect(self, collector_id, source_url):
        return "j_agent", next(self.results)


class AgentLLM:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def answer_question(self, context, question):
        self.calls.append((context, question))
        if self.error:
            raise self.error
        return self.result or {
            "answer": "The available scraped data lists Product A at 39.99.",
            "evidence": [{"source_url": context["sources"][0]["url"], "source_name": context["sources"][0]["name"], "reason": "Latest stored snapshot."}],
        }


def add_source_with_results(client: TestClient, competitor_id: int, name: str, url: str, results) -> dict:
    source = client.post(f"/competitors/{competitor_id}/sources", json={"name": name, "url": url, "extraction_description": "Extract products"}).json()
    bright_data = BrightDataSequence(results)
    app.dependency_overrides[get_bright_data_client] = lambda: bright_data
    client.post(f"/sources/{source['id']}/scraper")
    for _ in results:
        assert client.post(f"/sources/{source['id']}/collect").status_code == 200
    return source


def test_agent_answers_from_latest_competitor_snapshot_only(client: TestClient) -> None:
    target = client.post("/competitors", json={"name":"Target","website_url":"https://target.example"}).json()
    other = client.post("/competitors", json={"name":"Other","website_url":"https://other.example"}).json()
    add_source_with_results(client, other["id"], "Other Products", "https://other.example/products", [[{"title":"Secret","price":99}]])
    source = add_source_with_results(client, target["id"], "Catalog", "https://target.example/products", [[{"title":"Old","price":10}], [{"title":"New","price":20}]])
    llm = AgentLLM()
    app.dependency_overrides[get_llm_client] = lambda: llm

    response = client.post(f"/competitors/{target['id']}/ask", json={"question":"What are the current prices?"})

    assert response.status_code == 200
    context, _ = llm.calls[0]
    assert context["sources"] == [{"name":"Catalog", "url":source["url"], "snapshot_captured_at":context["sources"][0]["snapshot_captured_at"], "data":[{"price":20,"title":"New"}]}]
    assert "Other" not in str(context)
    assert response.json()["evidence"][0]["source_url"] == source["url"]


def test_agent_change_question_includes_existing_changes(client: TestClient) -> None:
    competitor = client.post("/competitors", json={"name":"Changing","website_url":"https://changing.example"}).json()
    add_source_with_results(client, competitor["id"], "Catalog", "https://changing.example/products", [[{"url":"https://changing.example/1","price":10}], [{"url":"https://changing.example/1","price":20}]])
    llm = AgentLLM()
    app.dependency_overrides[get_llm_client] = lambda: llm

    assert client.post(f"/competitors/{competitor['id']}/ask", json={"question":"What changed recently?"}).status_code == 200
    assert llm.calls[0][0]["recent_verified_changes"][0]["type"] == "modified"


def test_agent_rejects_missing_empty_and_no_data_competitors(client: TestClient) -> None:
    assert client.post("/competitors/999/ask", json={"question":"prices"}).status_code == 404
    competitor = client.post("/competitors", json={"name":"Empty","website_url":"https://empty.example"}).json()
    assert client.post(f"/competitors/{competitor['id']}/ask", json={"question":"   "}).status_code == 422
    assert client.post(f"/competitors/{competitor['id']}/ask", json={"question":"prices"}).status_code == 409


def test_agent_rejects_invalid_evidence_and_provider_errors(client: TestClient) -> None:
    competitor = client.post("/competitors", json={"name":"Errors","website_url":"https://errors.example"}).json()
    add_source_with_results(client, competitor["id"], "Catalog", "https://errors.example/products", [[{"title":"A"}]])
    app.dependency_overrides[get_llm_client] = lambda: AgentLLM(result={"answer":"Unsupported", "evidence":[{"source_url":"https://invented.example", "source_name":"Invented", "reason":"No"}]})
    assert client.post(f"/competitors/{competitor['id']}/ask", json={"question":"prices"}).status_code == 409
    app.dependency_overrides[get_llm_client] = lambda: AgentLLM(error=LLMError("failure"))
    assert client.post(f"/competitors/{competitor['id']}/ask", json={"question":"prices"}).status_code == 502
    app.dependency_overrides[get_llm_client] = lambda: AgentLLM(error=LLMTimeoutError("timeout"))
    assert client.post(f"/competitors/{competitor['id']}/ask", json={"question":"prices"}).status_code == 504
