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
    ["07655566677", "1970-01-01T01:00:00", "10:00", "OUTGOING", 0],  # invalid is free
    ["08005556667", "1970-01-01T01:00:00", "10:00", "OUTGOING", 0],  # free is free
    ["+111222333444", "1970-01-01T12:00:00", "09:59", "OUTGOING", 850],  # international day 
    ["+111222333444", "1970-01-01T01:00:00", "09:59", "OUTGOING", 850],  # international night, should be same as day 
    ["07624555666", "1970-01-01T12:00:00", "09:59", "OUTGOING", 300],  # mobile day
    ["07624555666", "1970-01-01T01:00:00", "09:59", "OUTGOING", 100],  # mobile night
    ["01615556666", "1970-01-01T12:00:00", "09:59", "OUTGOING", 150],  # landline day
    ["01615556666", "1970-01-01T01:00:00", "09:59", "OUTGOING", 50],  # landline night
    ["07624555666", "1970-01-01T07:55:00", "09:59", "OUTGOING", 200],  # mobile split
    ["01615556666", "1970-01-01T19:55:00", "09:59", "OUTGOING", 100],  # landline day
])
def test_callCost(number, start, duration, direction, expected):
    call = CallLog(number, start, duration, direction)

    assert callCost(call, 0, 0) == (expected, 0, 0)


@pytest.mark.parametrize("number,start,duration,freeInternational,freeLocal,expected", [
    ["07624555666", "1970-01-01T01:00:00", "09:59", 0, 100, (0, 0, 90)],
    ["+01624555666", "1970-01-01T01:00:00", "09:59", 100, 0, (50, 90, 0)], # International still has connection charge
])
def test_callCost_freeMins(number, start, duration, freeInternational,
        freeLocal, expected):
    call = CallLog(number, start, duration, "OUTGOING")

    assert callCost(call, freeInternational, freeLocal) == expected
