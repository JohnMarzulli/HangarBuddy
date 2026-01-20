from datetime import datetime, timedelta, timezone


class TimeCorrectionReport:
    """
    A single report of a time received, and what the
    current system thinks the time is.

    Used to derive a time delta.
    """

    def __init__(self, reportedTime: datetime):
        self.__reportedTime__: datetime = reportedTime.astimezone(timezone.utc)
        self.__currentTime__: datetime = datetime.now(tz=reportedTime.tzinfo)
        self.__offset__ = self.__reportedTime__ - self.__currentTime__
        self.offset_seconds: float = self.__offset__.total_seconds()


class TimeCorrection:
    """
    System to help correct time recieved vs system time.

    Uses the messages into the system as an authoritative way
    without having to use GPS or other system.
    """

    def __init__(self) -> None:
        self.__reports__: list[TimeCorrectionReport] = []

    def add_report(self, reportedTime: datetime) -> None:
        """
        Add a time correction report.

        Args:
            reportedTime (datetime): The time reported by the external source.
        """
        report = TimeCorrectionReport(reportedTime)
        self.__reports__.append(report)
        self.__reports__ = self.__reports__[-10:]

    def get_corrected_time(self, time: datetime) -> datetime:
        """
        Get the corrected current time based on the reports.

        Returns:
            datetime: The corrected current time.
        """
        if not self.__reports__:
            return time

        total_offset: float = 0.0
        for report in self.__reports__:
            total_offset += report.offset_seconds

        average_offset = total_offset / len(self.__reports__)

        return time.astimezone(timezone.utc) + timedelta(seconds=average_offset)

    def get_time(self) -> datetime:
        """
        Get the corrected current time based on the reports.

        Returns:
            datetime: The corrected current time.
        """
        return self.get_corrected_time(datetime.now(tz=timezone.utc))


TIME_CORRECTION = TimeCorrection()
