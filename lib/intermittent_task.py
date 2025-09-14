import datetime


class IntermittentTask(object):
    """
    Object that defines a task that is performed ON THREAD
    at some interval
    """

    def run(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        time_since_last_run: float = self.__task_interval__ * 2

        if self.__last_run__ is not None:
            time_since_last_run = (now - self.__last_run__).total_seconds()

        is_task_to_be_run: bool = time_since_last_run > self.__task_interval__

        if is_task_to_be_run:
            try:
                self.__task_callback__()
                self.__last_run__ = datetime.datetime.now(datetime.timezone.utc)
            except Exception as e:
                error_message = f"EX({self.__task_name__}):{e}"

                print(error_message)

    def __init__(self, task_name: str, task_interval: float, task_callback, logger=None):
        """
        Creates a new recurring task.
        The call back is called at the given time schedule.
        """

        self.__task_name__: str = task_name
        self.__task_interval__: float = task_interval
        self.__task_callback__ = task_callback
        self.__last_run__ = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=task_interval * 2)
