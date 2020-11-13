import csv
from collections import defaultdict
from datetime import datetime, time, timedelta
import json
from math import ceil

nightStart = time(hour=20)
nightEnd = time(hour=8)


class CallLog:

    def __init__(self, number, startTime, duration, direction):
        """Assumes input is already sanitised and correctly-formatted"""
        self.number = self.normaliseNumber(number)
        self.startTime = datetime.fromisoformat(startTime)
        self.duration = self.parseDuration(duration)
        self.direction = direction

    @staticmethod
    def normaliseNumber(number):
        """As a phone number can be represented in different ways, normalise these
        differences down to one representation, to simplify comparing and keying on
        the number."""

        if number[0] == "+":
            number = number.replace("+", "00")

        # make "international-looking" local calls local
        if number.startswith("0044"):
            # only replace once to avoid changing valid 0044
            # sequence in middle of number
            number = number.replace("0044", "0", 1)

        return number

    @staticmethod
    def parseDuration(duration):
        """Parses a string of 'MM:SS' to a datetime.timedelta
        Assumes the string is well-formatted with padding 0s"""
        mins = int(duration[:2])
        secs = int(duration[3:])
        return timedelta(minutes=mins, seconds=secs)

    def getCallType(self):
        if self.number.startswith("00"):
            return "international"

        if self.number.startswith("01") or self.number.startswith("02"):
            return "landline"

        if self.number.startswith("080"):
            return "free"

        if self.number.startswith("07"):
            if self.number[2] == "6":
                if self.number.startswith("07624"):
                    return "mobile"
                else:
                    return "invalid"

            return "mobile"

        return "invalid"


def callCost(call, freeInternational, freeLocal):
    """Calculates cost of a logged call, taking into account free minutes on
    the tariff. Returns cost and remaining free minutes."""
    callType = call.getCallType()
    cost = 0

    if call.direction == "INCOMING" or callType == "free" or callType == "invalid":
        return cost, freeInternational, freeLocal

    if callType == "international":
        cost += 50  # connection charge

        mins = startedMins(call.duration)
        chargedMins = max(mins - freeInternational, 0)
        remainingFree = max(freeInternational - mins, 0)

        cost += chargedMins * 80
        return cost, remainingFree, freeLocal

    # All remaining calls must be landline or mobile. These need to be split
    # into overnight and daytime minutes, but only considering non-free minutes
    mins = startedMins(call.duration)
    remainingFree = max(freeLocal - mins, 0)
    if freeLocal > mins:
        return cost, freeInternational, remainingFree

    chargeStart = call.startTime + timedelta(minutes=remainingFree)
    chargeEnd = call.startTime + call.duration
    mins = startedMins(chargeEnd - chargeStart)

    if chargeStart.time() > nightEnd and chargeEnd.time() < nightStart:
        # Whole charged call is within daytime rate
        if callType == "landline":
            return 15 * mins, freeInternational, remainingFree
        else:
            return 30 * mins, freeInternational, remainingFree

    if chargeStart.time() < nightEnd and chargeEnd.time() > nightStart:
        # Whole charged call is within nighttime rate
        if callType == "landline":
            cost = 15 * mins
        else:
            cost = 30 * mins

        # Spec doesn't specify how to deal with fractions of pennies,
        # assuming floor instead of round
        cost = cost//3
        return cost, freeInternational, remainingFree

    # Call time is split between day and night
    dayMins = max(startedMins(timedelta(hours=nightEnd.hour,
        minutes=nightEnd.minute) - timedelta(hours=chargeStart.hour,
            minutes=chargeStart.minute, seconds=chargeStart.second)), 0)
    nightMins = max(startedMins(timedelta(hours=nightStart.hour,
        minutes=nightStart.minute) - timedelta(hours=chargeEnd.hour,
            minutes=chargeEnd.minute, seconds=chargeEnd.second)), 0)

    if callType == "landline":
        cost += 15 * dayMins
        cost += (15 * nightMins)//3
    else:
        cost += 30 * dayMins
        cost += (30 * nightMins)//3

    return cost, freeInternational, remainingFree


def startedMins(duration):
    """Returns number of 'started' mins in a timedelta, which is always the
    number of clock minutes plus 1, e.g. 00:59 is 1 minute, 01:00 is two"""
    if duration.total_seconds() == 0:
        return 0
    else:
        return ceil(duration / timedelta(minutes=1))


def parseCallLog(callLogFilePath):
    """Takes CSV of call log lines and returns list of CallLog objects"""
    calls = []

    with open(callLogFilePath) as csvFile:
        for line in csv.reader(csvFile):
            calls.append(CallLog(line[0], line[1], line[2], line[3]))

    return calls


def findMostExpensiveNumber(callLogFilePath):
    # dict of {number: cost}, defaults to zero
    cumulativeCosts = defaultdict(int)
    freeInternational = 10
    freeLocal = 100
    callLog = parseCallLog(callLogFilePath)

    for call in callLog:
        cost, freeInternational, freeLocal = callCost(
                call, freeInternational, freeLocal)

        cumulativeCosts[call.number] += cost

    maxCost = 0
    maxNumber = ""

    for number, cost in cumulativeCosts:
        if cost > maxCost:
            maxCost = cost
            maxNumber = number

    costString = "£{:}:{:}".format(maxCost//100, maxCost % 100)

    return json.format({
        "PhoneNumber": maxNumber,
        "TotalAmount": costString,
    })
