from __future__ import annotations

import pytest

from may_backend.api.v1.endpoints import assets


def test_image_generation_log_omits_raw_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records: list[dict[str, object]] = []

    def fake_info(**fields: object) -> None:
        records.append(dict(fields))

    monkeypatch.setattr(assets.logger, "info", fake_info)

    request = assets.CreateImageGenerationRequest(
        image_key="assets/cat.png",
        prompt="  confidential prompt text  ",
    )
    response = assets.create_image_generation(request)

    assert response.prompt == "confidential prompt text"
    assert records == [
        {
            "event": "asset.image_generation.received",
            "image_key": "assets/cat.png",
            "prompt_length": len(response.prompt),
        }
    ]
    assert "prompt" not in records[0]
