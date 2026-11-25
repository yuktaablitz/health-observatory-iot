import pytest

import vitals
from vitals import ELEVATED, HIGH, NORMAL, classify, parse_reading


@pytest.mark.parametrize("t,level", [
    (25.0, NORMAL), (29.9, NORMAL),
    (29.5, NORMAL),            # was unclassified in the original code (29 < t < 30)
    (30.0, ELEVATED), (31.0, ELEVATED),
    (31.1, HIGH), (45.0, HIGH),
])
def test_classify_has_no_gaps(t, level):
    assert classify(t) == level


def test_body_temperature_thresholds(monkeypatch):
    monkeypatch.setenv("NORMAL_MAX_C", "37.5")
    monkeypatch.setenv("ELEVATED_MAX_C", "38.5")
    assert classify(36.8) == NORMAL
    assert classify(38.0) == ELEVATED
    assert classify(39.2) == HIGH


def test_bad_thresholds_rejected(monkeypatch):
    monkeypatch.setenv("NORMAL_MAX_C", "32")
    monkeypatch.setenv("ELEVATED_MAX_C", "31")
    with pytest.raises(ValueError):
        vitals.thresholds()


def test_parse_reading_keeps_optional_fields():
    r = parse_reading({"patient_id": " bed-01 ", "temperature_c": "30.4", "humidity": 55.0, "seq": 7})
    assert r == {"patient_id": "bed-01", "temperature_c": 30.4, "humidity": 55.0, "seq": 7}


@pytest.mark.parametrize("body", [
    [], {}, {"patient_id": "bed-01"}, {"temperature_c": 30},
    {"patient_id": "", "temperature_c": 30}, {"patient_id": "bed-01", "temperature_c": "hot"},
    {"patient_id": "bed-01", "temperature_c": 200},
])
def test_parse_reading_rejects_bad_input(body):
    with pytest.raises(ValueError):
        parse_reading(body)
