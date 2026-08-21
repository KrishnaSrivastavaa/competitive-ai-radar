import json
import os
import re
import shutil
import subprocess
import time
from typing import Any

import httpx

from app.core.config import Settings, settings


class BrightDataError(Exception):
    """A Bright Data configuration, transport, API, or polling error."""


class BrightDataTimeoutError(BrightDataError):
    """A Bright Data asynchronous operation did not complete in time."""


class BrightDataClient:
    """Small synchronous client for Bright Data Scraper Studio's documented APIs."""

    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        headers = {}
        if config.bright_data_api_key:
            headers["Authorization"] = f"Bearer {config.bright_data_api_key}"
        self.client = httpx.Client(
            base_url=config.bright_data_api_base_url,
            headers=headers,
            timeout=config.bright_data_timeout_seconds,
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        if not self.config.bright_data_api_key:
            raise BrightDataError("BRIGHT_DATA_API_KEY is not configured")
        try:
            response = self.client.request(method, path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as exc:
            raise BrightDataTimeoutError("Bright Data request timed out") from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise BrightDataError(f"Bright Data API returned {exc.response.status_code}: {detail}") from exc
        except httpx.HTTPError as exc:
            raise BrightDataError(f"Bright Data request failed: {exc}") from exc

    @staticmethod
    def _json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise BrightDataError("Bright Data returned invalid JSON") from exc

    def create_scraper(self, name: str, url: str, description: str) -> str:
        """Create an AI-generated collector through Bright Data's official CLI."""
        if not self.config.bright_data_api_key:
            raise BrightDataError("BRIGHT_DATA_API_KEY is not configured")

        cli_path = shutil.which(self.config.bright_data_cli_command)
        if cli_path is None:
            raise BrightDataError(
                f"Bright Data CLI command not found: {self.config.bright_data_cli_command}"
            )

        command = [
            cli_path,
            "scraper",
            "create",
            url,
            description,
            "--name",
            name,
            "--timeout",
            str(self.config.bright_data_cli_timeout_seconds),
            "--json",
        ]
        environment = os.environ.copy()
        environment["BRIGHTDATA_API_KEY"] = self.config.bright_data_api_key
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.config.bright_data_cli_timeout_seconds,
                env=environment,
                check=False,
            )
        except FileNotFoundError as exc:
            raise BrightDataError(f"Bright Data CLI command not found: {cli_path}") from exc
        except subprocess.TimeoutExpired as exc:
            raise BrightDataTimeoutError("Bright Data CLI scraper creation timed out") from exc

        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "no CLI output"
            raise BrightDataError(f"Bright Data CLI scraper creation failed: {detail}")

        try:
            envelope = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise BrightDataError("Bright Data CLI did not return a JSON creation envelope") from exc
        if not isinstance(envelope, dict):
            raise BrightDataError("Bright Data CLI returned an invalid creation envelope")

        collector_id = envelope.get("collector_id")
        if not isinstance(collector_id, str) or not re.fullmatch(r"c_[A-Za-z0-9_-]+", collector_id):
            raise BrightDataError("Bright Data CLI did not return a valid collector_id")
        if envelope.get("status") != "done":
            detail = envelope.get("error") or f"status={envelope.get('status')!r}"
            raise BrightDataError(f"Bright Data CLI scraper creation failed: {detail}")
        return collector_id

    def collect(self, collector_id: str, source_url: str) -> tuple[str, Any]:
        """Trigger a collector with its default url input, then retrieve its dataset."""
        trigger = self._json(
            self._request(
                "POST",
                "/dca/trigger",
                params={"collector": collector_id, "queue_next": "1"},
                json=[{"url": source_url}],
            )
        )
        collection_id = trigger.get("collection_id") if isinstance(trigger, dict) else None
        if not isinstance(collection_id, str) or not collection_id:
            raise BrightDataError("Bright Data did not return a collection_id")
        return collection_id, self._wait_for_dataset(collection_id)

    def _wait_for_dataset(self, collection_id: str) -> Any:
        deadline = time.monotonic() + self.config.bright_data_poll_timeout_seconds
        while time.monotonic() < deadline:
            result = self._json(
                self._request("GET", "/dca/dataset", params={"id": collection_id})
            )
            if isinstance(result, list):
                return result
            # Bright Data documents a JSON status object while the dataset is building.
            # Poll by result shape, not by assuming a particular HTTP response status.
            if not isinstance(result, dict) or not isinstance(result.get("status"), str):
                raise BrightDataError("Bright Data returned an unexpected dataset response")
            time.sleep(self.config.bright_data_poll_interval_seconds)
        raise BrightDataTimeoutError("Timed out waiting for Bright Data collection")

    def close(self) -> None:
        self.client.close()


def get_bright_data_client() -> BrightDataClient:
    return BrightDataClient()
