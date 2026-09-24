from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from app.constants.status import Status
from app.exceptions import InternalError, NotFoundError, ValidationError, service_error
from app.services.audio_service import audio_service
from app.utils.validation import Validation


def test_input_validation():
    assert Validation.require_id("7", "voices_id") == 7
    assert Validation.optional_id(None, "projects_id") is None
    assert Validation.require_ref("12", "model_id") == 12 and Validation.require_ref("piper", "model_id") == "piper"
    assert Validation.limit(None) == 100 and Validation.limit(5) == 5
    for bad in (0, -3, "x", True):
        with pytest.raises(ValidationError) as caught:
            Validation.require_id(bad, "voices_id")
        assert caught.value.field == "voices_id"
    with pytest.raises(ValidationError):
        Validation.limit(5000)


def test_response_data_uses_json_types():
    data = Validation.response_data({
        "when": datetime(2026, 1, 2, tzinfo=timezone.utc), "path": Path("a/b.wav"), "status": Status.ACTIVE,
        "peaks": np.array([0.5, 1.0], dtype=np.float32), "count": np.int64(3), "bad": float("nan"), 4: (1, 2),
    })
    assert data == {"when": "2026-01-02T00:00:00+00:00", "path": str(Path("a/b.wav")), "status": 1,
                    "peaks": [0.5, 1.0], "count": 3, "bad": None, "4": [1, 2]}
    assert type(data["count"]) is int


def test_service_errors_are_logged_and_wrapped():
    missing = NotFoundError("Audio 5 not found")
    assert service_error(missing, "test") is missing and missing.logged
    unexpected = service_error(KeyError("boom"), "test")
    assert isinstance(unexpected, InternalError) and isinstance(unexpected.__cause__, KeyError)

    # A library error inside a service reaches callers as InternalError, never raw.
    with pytest.raises(InternalError):
        audio_service.apply_edit_ops(np.zeros(10, dtype=np.float32), 16000, [{"op": "insert"}])
