"""Storage domain data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Mapping


@dataclass(frozen=True)
class PresignedPutUrl:
    url: str
    method: Literal["PUT"]
    headers: Mapping[str, str]
    key: str
    expires_at: datetime
    expires_in_seconds: int
