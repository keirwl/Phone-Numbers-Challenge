from datetime import datetime
import pytest

from .phone import CallLog, callCost


def test_normalise():
    assert CallLog.normaliseNumber("01615556666") == CallLog.normaliseNumber("+441615556666")
    assert CallLog.normaliseNumber("01615556666") == CallLog.normaliseNumber("00441615556666")
    # ensure non-prefix "0044" isn't changed
    assert CallLog.normaliseNumber("01615550044") == CallLog.normaliseNumber("00441615550044")


@pytest.mark.parametrize("number,expected", [
    ["07624555666", "mobile"],
    ["07655566677", "invalid"],
    ["07555666777", "mobile"],
    ["08005556667", "free"],
    ["08885556667", "invalid"],
    ["01234567890", "landline"],
    ["02012345678", "landline"],
    ["03333444555", "invalid"],
    ["00111222333444", "international"],
    ["+111222333444", "international"],
    ["+447624555666", "mobile"],
    ["00447624555666", "mobile"],
    ["+448005556667", "free"],
])
def test_callType(number, expected):
    startTime = datetime.now().isoformat()
    duration = "04:05"
    direction = "OUTGOING"

    assert CallLog(number, startTime, duration, direction).getCallType() == expected


@pytest.mark.parametrize("number,start,duration,direction,expected", [
    ["07624555666", "1970-01-01T01:00:00", "10:00", "INCOMING", 0],  # INCOMING is free
])
def test_callCost(number, start, duration, direction, expected):
    call = CallLog(number, start, duration, direction)

    assert callCost(call, 0, 0) == (expected, 0, 0)
