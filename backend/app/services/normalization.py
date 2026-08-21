import hashlib
import json
from typing import Any


def normalize_result(result: Any) -> Any:
    """Recursively make extracted JSON deterministic without changing list order."""
    if isinstance(result, dict):
        return {key: normalize_result(result[key]) for key in sorted(result)}
    if isinstance(result, list):
        return [normalize_result(item) for item in result]
    return result


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_content_hash(normalized_result: Any) -> str:
    return hashlib.sha256(canonical_json(normalized_result).encode("utf-8")).hexdigest()
