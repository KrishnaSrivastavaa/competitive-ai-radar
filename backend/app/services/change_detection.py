from dataclasses import dataclass
from typing import Any

from app.services.normalization import canonical_json

IDENTITY_FIELDS = ("product_page_url", "url", "product_url", "id", "product_id", "sku")


@dataclass(frozen=True)
class DetectedChange:
    change_type: str
    summary: str
    diff_data: dict[str, Any]
    significance: str


def _record_key(record: Any) -> str:
    if isinstance(record, dict):
        for field in IDENTITY_FIELDS:
            value = record.get(field)
            if isinstance(value, (str, int, float)) and str(value):
                return f"{field}:{value}"
    return f"canonical:{canonical_json(record)}"


def _record_map(records: list[Any]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for record in records:
        key = _record_key(record)
        # A canonical suffix prevents duplicate identities from overwriting one another.
        if key in mapped:
            key = f"{key}|{canonical_json(record)}"
        mapped[key] = record
    return mapped


def _changed_fields(before: Any, after: Any, prefix: str = "") -> list[str]:
    if isinstance(before, dict) and isinstance(after, dict):
        changed: list[str] = []
        for key in sorted(set(before) | set(after)):
            path = f"{prefix}.{key}" if prefix else key
            if key not in before or key not in after:
                changed.append(path)
            else:
                changed.extend(_changed_fields(before[key], after[key], path))
        return changed
    if before != after:
        return [prefix or "value"]
    return []


def detect_changes(
    previous_data: list[Any] | None,
    current_data: list[Any],
    previous_hash: str | None,
    current_hash: str,
) -> DetectedChange:
    if previous_data is None:
        return DetectedChange(
            change_type="initial",
            summary=f"Initial snapshot: {len(current_data)} records captured.",
            diff_data={"added": current_data, "removed": [], "modified": []},
            significance="low",
        )

    if previous_hash == current_hash:
        return DetectedChange(
            change_type="unchanged",
            summary="No meaningful changes detected.",
            diff_data={"added": [], "removed": [], "modified": []},
            significance="none",
        )

    previous_records = _record_map(previous_data)
    current_records = _record_map(current_data)
    added_keys = sorted(set(current_records) - set(previous_records))
    removed_keys = sorted(set(previous_records) - set(current_records))
    shared_keys = sorted(set(previous_records) & set(current_records))
    modified = [
        {
            "record_key": key,
            "before": previous_records[key],
            "after": current_records[key],
            "changed_fields": _changed_fields(previous_records[key], current_records[key]),
        }
        for key in shared_keys
        if previous_records[key] != current_records[key]
    ]
    diff_data = {
        "added": [current_records[key] for key in added_keys],
        "removed": [previous_records[key] for key in removed_keys],
        "modified": modified,
    }

    if not added_keys and not removed_keys and not modified:
        return DetectedChange(
            change_type="unchanged",
            summary="No meaningful changes detected.",
            diff_data=diff_data,
            significance="none",
        )

    parts: list[str] = []
    if added_keys:
        parts.append(f"{len(added_keys)} products added")
    if removed_keys:
        parts.append(f"{len(removed_keys)} products removed")
    if modified:
        fields = sorted({field for item in modified for field in item["changed_fields"]})
        suffix = f": {', '.join(fields)} changed" if len(fields) == 1 else ""
        parts.append(f"{len(modified)} products modified{suffix}")

    if added_keys and not removed_keys and not modified:
        change_type = "added"
    elif removed_keys and not added_keys and not modified:
        change_type = "removed"
    else:
        change_type = "modified"

    removal_ratio = len(removed_keys) / len(previous_records) if previous_records else 0
    significance = "high" if removal_ratio >= 0.5 else "medium"
    return DetectedChange(
        change_type=change_type,
        summary="; ".join(parts) + ".",
        diff_data=diff_data,
        significance=significance,
    )
