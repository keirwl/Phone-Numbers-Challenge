from datetime import datetime, timedelta

class CallLog:

    def __init__(self, number, startTime, duration, direction):
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
