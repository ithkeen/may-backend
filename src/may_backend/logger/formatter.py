"""JSON Lines formatting."""

from collections.abc import Mapping
import json


def format_json_line(record: Mapping[str, object]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
