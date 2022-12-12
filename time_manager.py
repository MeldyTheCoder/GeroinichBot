import time
from datetime import datetime, timedelta, timezone
import calendar
from typing import Union


class TimeManager:
    def __init__(self):
        self.timezone = timezone(timedelta(hours=3), 'МСК')
        self.weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        self.months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        self.__graduate_start_time = 1630443600  # 1 сентября 2021
        self.__semesters = [17*7, 24*7]
        self.__holidays = [2*7, 0]
        self.date_pattern = '%d/%m/%Y %H:%M'

    @property
    def now(self):
        return datetime.now(tz=self.timezone)

    @property
    def current_timestamp(self):
        return self.now.timestamp()

    def month_days(self, year: int = 0, month: int = 0):
        if not year:
            year = self.now.year
        if not month:
            month = self.now.month

        return calendar.monthrange(year, month)

    @property
    def current_weekday(self):
        return self.weekdays[self.now.isoweekday()-1]

    def string_to_date(self, string: str):
        return datetime.strptime(string, self.date_pattern)

    @property
    def timestamp(self):
        return self.now.timestamp()

    @property
    def current_month(self):
        return self.months[self.now.month-1]

    def strftime(self, date: Union[int, datetime] = None):
        if not date:
            date = self.now
        elif isinstance(date, int):
            date = self.fromtimestamp(date)
        return date.strftime(self.date_pattern)

    def get_month_string(self, month: int):
        return self.months[month - 1]

    def get_weekday_string(self, weekday: int):
        return self.weekdays[weekday - 1]

    def fromtimestamp(self, date: int):
        return datetime.fromtimestamp(date, tz=self.timezone)

    def day_start(self, date: Union[datetime] = None):
        if not date:
            date = self.now
        date = date - timedelta(hours=date.hour, minutes=date.minute, seconds=date.second, microseconds=date.microsecond)
        return date

    def week_start(self, date: Union[datetime] = None):
        date = self.day_start(date)
        date -= timedelta(days=date.isoweekday()-1)
        return date

    def month_start(self, date: Union[datetime] = None):
        date = self.day_start(date)
        date -= timedelta(days=date.day-1)
        return date

    def month_range(self, date: Union[datetime] = None, timestamp: bool = False):
        start = self.month_start(date)
        if not date:
            date = self.now
        end = start + timedelta(days=self.month_days(date.year, date.month)[1])
        if timestamp:
            return (start.timestamp(), end.timestamp())
        return (start, end)

    def week_range(self, date: Union[datetime] = None, timestamp: bool = False):
        start = self.week_start(date)
        end = start + timedelta(days=7)
        if timestamp:
            return (start.timestamp(), end.timestamp())
        return (start, end)

    def day_range(self, date: Union[datetime] = None, timestamp: bool = False):
        start = self.day_start(date)
        end = start + timedelta(days=1)
        if timestamp:
            return (start.timestamp(), end.timestamp())
        return (start, end)

    def graduate_range(self, date: Union[datetime] = None, timestamp: bool = False):
        if not date:
            date = self.now
        date_string = '01/09/{year} 00:00:00'.format(year=date.year)
        start = datetime.strptime(date_string, "%d/%m/%Y %H:%M:%S")
        end = start
        for index, semester in enumerate(self.__semesters):
            end += timedelta(days=semester)
            end += timedelta(days=self.__holidays[index])

        if timestamp:
            return (start.timestamp(), end.timestamp())
        return (start, end)

    def semesters_time_slices(self, date: Union[datetime] = None, timestamp: bool = False):
        start_pos = self.graduate_range(date)[0]
        slices = []
        days = 0
        for index, semester in enumerate(self.__semesters):
            if not index:
                start = start_pos
            else:
                start = start_pos + timedelta(days=days)
            end = start + timedelta(days=semester)
            slices.append((start, end))
            days += self.__holidays[index] + semester
        if timestamp:
            slices = [(int(slice_item[0].timestamp()), int(slice_item[1].timestamp())) for slice_item in slices]
        return slices

    def get_grade(self, date: Union[datetime] = None):
        if not date:
            date = self.now
        current_grade_start = self.graduate_range(date, timestamp=True)[0]
        grade_diff = current_grade_start - self.__graduate_start_time
        grade = (grade_diff / 60 / 60 / 24 // 365) + 1
        return int(round(grade, 0))

    def get_semester(self, date: Union[datetime] = None):
        if not date:
            date = self.now
        slices = self.semesters_time_slices(date, timestamp=True)
        for index, semester in enumerate(slices):
            if int(date.timestamp()) in iter(range(*semester)):
                return index
        return None

    @property
    def current_semester(self):
        return self.get_semester()

print(TimeManager().current_semester)


