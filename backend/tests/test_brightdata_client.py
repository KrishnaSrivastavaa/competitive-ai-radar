import subprocess
from unittest.mock import Mock, patch

import httpx
import pytest

from app.core.config import Settings
from app.services.brightdata import BrightDataClient, BrightDataError, BrightDataTimeoutError


def make_client(*, poll_timeout: float = 1) -> BrightDataClient:
    return BrightDataClient(
        Settings(
            app_name="test",
            database_url="sqlite://",
            bright_data_api_key="test-key",
            bright_data_api_base_url="https://api.brightdata.com",
            bright_data_timeout_seconds=1,
            bright_data_poll_interval_seconds=0,
            bright_data_poll_timeout_seconds=poll_timeout,
            bright_data_cli_command="brightdata",
            bright_data_cli_timeout_seconds=600,
        )
    )


def response(status_code: int, body) -> httpx.Response:
    return httpx.Response(status_code, json=body)


def test_cli_scraper_creation_returns_collector_id() -> None:
    client = make_client()
    completed = subprocess.CompletedProcess(
        args=[], returncode=0, stdout='{"collector_id":"c_created","status":"done"}', stderr=""
    )

    with (
        patch("app.services.brightdata.shutil.which", return_value="brightdata") as which,
        patch("app.services.brightdata.subprocess.run", return_value=completed) as run,
    ):
        assert client.create_scraper("Example", "https://example.com", "Extract title") == "c_created"

    which.assert_called_once_with("brightdata")
    assert run.call_args.args[0] == [
        "brightdata",
        "scraper",
        "create",
        "https://example.com",
        "Extract title",
        "--name",
        "Example",
        "--timeout",
        "600",
        "--json",
    ]
    assert run.call_args.kwargs["env"]["BRIGHTDATA_API_KEY"] == "test-key"
    client.close()


def test_cli_scraper_creation_failure_raises_error() -> None:
    client = make_client()
    completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="authentication failed")

    with (
        patch("app.services.brightdata.shutil.which", return_value="brightdata"),
        patch("app.services.brightdata.subprocess.run", return_value=completed),
    ):
        with pytest.raises(BrightDataError, match="authentication failed"):
            client.create_scraper("Example", "https://example.com", "Extract title")

    client.close()


def test_cli_scraper_creation_timeout_raises_error() -> None:
    client = make_client()

    with (
        patch("app.services.brightdata.shutil.which", return_value="brightdata"),
        patch(
            "app.services.brightdata.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="brightdata", timeout=600),
        ),
    ):
        with pytest.raises(BrightDataTimeoutError, match="CLI scraper creation"):
            client.create_scraper("Example", "https://example.com", "Extract title")

    client.close()


def test_cli_scraper_creation_without_collector_id_raises_error() -> None:
    client = make_client()
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout='{"status":"done"}', stderr="")

    with (
        patch("app.services.brightdata.shutil.which", return_value="brightdata"),
        patch("app.services.brightdata.subprocess.run", return_value=completed),
    ):
        with pytest.raises(BrightDataError, match="valid collector_id"):
            client.create_scraper("Example", "https://example.com", "Extract title")

    client.close()


def test_dataset_polls_building_status_until_array_is_returned() -> None:
    client = make_client()
    client._request = Mock(
        side_effect=[
            response(202, {"status": "building"}),
            response(200, [{"title": "Launch"}]),
        ]
    )

    assert client._wait_for_dataset("j_demo") == [{"title": "Launch"}]
    assert client._request.call_count == 2
    client.close()


def test_dataset_timeout() -> None:
    client = make_client(poll_timeout=0)

    with pytest.raises(BrightDataTimeoutError, match="collection"):
        client._wait_for_dataset("j_demo")

    client.close()


def test_dataset_unexpected_response_raises_error() -> None:
    client = make_client()
    client._request = Mock(return_value=response(200, {"message": "not a dataset status"}))

    with pytest.raises(BrightDataError, match="unexpected dataset response"):
        client._wait_for_dataset("j_demo")

    client.close()
