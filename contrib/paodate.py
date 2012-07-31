#!/usr/bin/env python
 
"""
    Pao Date Tools
    ==============
    Utilities for making date and time handling in Python easy. This is mainly
    accomplished with the new Date object which abstracts most of the 
    differences between datetime, date, time, timedelta, and relativedelta,
    allowing you to convert freely between all of them and providing useful
    utility methods.
    
    Please look at the README.rst file included with this project and the
    source code documentation and examples below for more information.

    Usage
    -----
    Import the paodate.py file into your project and use the Date and Delta
    objects.

    Requirements
    ------------
    The only requirement for this module is Python. Running this script will
    invoke all unit tests so you can see that everything works for your
    installation.

    Authors & Contributors
    ----------------------
    Patches are very welcome upstream, so feel free to fork and push your
    changes back up! The following people have worked on this project:

        * Daniel G. Taylor <dan@programmer-art.org>

    License
    -------
    This module is free software, released under the terms of the Python 
    Software Foundation License version 2, which can be found here:

        http://www.python.org/psf/license/

"""
__version__ = "1.2"

import calendar
import time
 
from datetime import datetime, date, timedelta

class Delta(object):
    """
        An object representing a difference between date/times. This object
        has several advantages over Python's built-in timedelta object.
        
         * Attributes like years, months, days, minutes, hours, seconds,
           microseconds
         * You can easily convert to a timedelta or a number of seconds
         * Convenience methods, e.g. for human-friendly display
        
        Notes:
        
         * When dealing with months it is assumed that one month is equal
           to exactly 30 days. To get an exact number of seconds always use
           the Delta().total_seconds property.
         * One year is assumed to be exactly 365 days.
        
            >>> d = Delta()
            >>> str(d)
            'Delta(0 seconds)'
            
            >>> d = Delta(123456)
            >>> str(d)
            'Delta(1 day, 10 hours, 17 minutes, 36 seconds)'
            >>> d.days
            1
            >>> d.minutes
            17
            >>> d.total_seconds
            123456.0
            >>> d.total_hours
            34.293333333333337
            
            >>> delta = Date(12345678) - Date(12340000)
            >>> str(delta)
            'Delta(1 hour, 34 minutes, 38 seconds)'
            
            >>> d = Date(12345678) + Delta(hours = 2, minutes = 7)
            >>> str(d)
            'Date(1970-05-24, 00:28:18)'
        
        @type td: timedelta, int, float, long or None
        @param td: An existing timedelta or number of seconds
        @type years: int, float, or long
        @param years: The number of years this delta represents
        @type months: int, float, or long
        @param months: The number of months this delta represents
        @type years: int, float, or long
        @param years: The number of years this delta represents
        @type years: int, float, or long
        @param years: The number of years this delta represents
        @type years: int, float, or long
        @param years: The number of years this delta represents
        @type years: int, float, or long
        @param years: The number of years this delta represents
    """
    def __init__(self, td = None, years = 0, months = 0, days = 0, hours = 0,
                 minutes = 0, seconds = 0):
        if td is None:
            self.td = timedelta()
        elif type(td) is timedelta:
            self.td = td
        elif type(td) in [int, float, long]:
            self.td = timedelta(seconds=td)
        else:
            raise ValueError("You must pass a valid timedelta object, number " \
                             "of years, months, days, hours, minutes, " \
                             "seconds, or nothing instead of %s" % td)
        
        days = years * 365 + months * 30 + days
        seconds = hours * 60 * 60 + minutes * 60 + seconds
        
        self.td = timedelta(days=self.td.days + days, seconds=self.td.seconds + seconds, microseconds=self.td.microseconds)
    
    def __repr__(self):
        """
            Return a nice string representation of this delta.
            
                >>> str(Delta())
                'Delta(0 seconds)'
                
                >>> str(Delta(months=1, days=2, minutes=3))
                'Delta(1 month, 2 days, 3 minutes)'
            
            @rtype: str
            @return: String representation of this delta
        """
        return "Delta(%s)" % self.friendly
    
    def _get_timedelta(self):
        """
            Get the underlying timedelta object.
            
            @rtype: timedelta
            @return: The underlying timedelta
        """
        return self.td
    
    def _set_timedelta(self, value):
        """
            Set the underlying timedelta object.
            
            @type value: timedelta
            @param value: The timedelta object to set
        """
        self.td = value
    
    timedelta = property(_get_timedelta, _set_timedelta)
    
    @property
    def friendly(self):
        """
            Get a friendly, human-readable representation of this delta.
            
                >>> Delta().friendly
                '0 seconds'
                
                >>> Delta(123456).friendly
                '1 day, 10 hours, 17 minutes, 36 seconds'
            
            @rtype: str
            @return: Friendly string
        """
        data = []
        
        for attr in ["year", "month", "day", "hour", "minute", "second"]:
            val = getattr(self, attr + "s")
            if val:
                data.append("%d %s" % (val, val == 1 and attr or (attr + "s")))
        
        if not data:
          data.append("0 seconds")
        
        return ", ".join(data)
    
    def _get_microseconds(self):
        """
            Get the number of microseconds.
            
                >>> d = Date(12345678) - Date(12345670.5)
                >>> d.microseconds
                500000
            
            @rtype: int
            @return: Number of microseconds
        """
        return self.td.microseconds
    
    def _set_microseconds(self, value):
        """
            Set the number of microseconds.
            
                >>> d = Delta()
                >>> d.microseconds
                0
                >>> d.microseconds = 5000
                >>> d.microseconds
                5000
            
            @type value: int or long
            @param value: Number of microseconds
        """
        value -= self.microseconds
        self.td = timedelta(seconds=self.total_seconds + (value / 1000000.0))
    
    microseconds = property(_get_microseconds, _set_microseconds)
    
    @property
    def total_microseconds(self):
        """
            Get the total number of microseconds in this delta.
            
                >>> d = Delta(minutes=3)
                >>> d.total_microseconds
                180000000.0
            
            @rtype: float
            @return: Number of microseconds
        """
        return float(self.td.days * 24 * 60 * 60 * 1000000 + self.td.seconds * 1000000 + self.td.microseconds)
    
    def _get_seconds(self):
        """
            Get the number of seconds.
            
                >>> d = Date(12345678) - Date(12345670.5)
                >>> d.seconds
                7
            
            @rtype: int
            @return: Number of seconds
        """
        return self.td.seconds % (60 * 60) % 60
    
    def _set_seconds(self, value):
        """
            Set the number of seconds.
            
                >>> d = Delta()
                >>> d.seconds
                0
                >>> d.seconds += 20
                >>> d.seconds
                20
            
            @type value: int or long
            @param value: Number of seconds
        """
        value -= self.seconds
        self.td = timedelta(seconds=self.total_seconds + value)
    
    seconds = property(_get_seconds, _set_seconds)
    
    @property
    def total_seconds(self):
        """
            Get the total number of seconds in this delta.
            
                >>> d = Delta(minutes=3)
                >>> d.total_seconds
                180.0
            
            @rtype: float
            @return: Number of seconds
        """
        return self.td.days * 24 * 60 * 60 + self.td.seconds + (self.td.microseconds / 1000000.0)
    
    def _get_minutes(self):
        """
            Get the number of minutes.
            
                >>> d = Delta(minutes=10)
                >>> d.minutes
                10
            
            @rtype: int
            @return: Number of minutes
        """
        return self.td.seconds % (60 * 60) / 60
    
    def _set_minutes(self, value):
        """
            Set the number of minutes.
            
                >>> d = Delta()
                >>> d.minutes = 10
                >>> d.minutes
                10
            
            @type value: int or long
            @param value: Number of minutes
        """
        value -= self.minutes
        self.td = timedelta(seconds=self.total_seconds + (value * 60.0))
    
    minutes = property(_get_minutes, _set_minutes)
    
    @property
    def total_minutes(self):
        """
            Get the total number of minutes in this delta.
            
                >>> d = Delta(hours=1.5)
                >>> d.total_minutes
                90.0
            
            @rtype: float
            @return: Number of minutes
        """
        return self.td.days * 24 * 60 + (self.td.seconds / 60.0) + (self.td.microseconds / 1000000.0 / 60.0)
    
    def _get_hours(self):
        """
            Get the number of hours.
            
                >>> d = Delta(hours=3)
                >>> d.hours
                3
            
            @rtype: int
            @return: Number of hours
        """
        return self.td.seconds / (60 * 60)
    
    def _set_hours(self, value):
        """
            Set the number of hours.
            
                >>> d = Delta(days=1)
                >>> d.hours -= 1
                >>> d.hours
                23
            
            @type value: int or long
            @param value: Number of hours
        """
        value -= self.hours
        self.td = timedelta(seconds=self.total_seconds + (value * 60.0 * 60.0))
    
    hours = property(_get_hours, _set_hours)
    
    @property
    def total_hours(self):
        """
            Get the total number of hours in this delta.
            
                >>> d = Delta(days = 1)
                >>> d.total_hours
                24.0
            
            @rtype: float
            @return: Number of hours
        """
        return self.td.days * 24 + (self.td.seconds / 60.0 / 60.0) + (self.td.microseconds / 1000000.0 / 60.0 / 60.0)
    
    def _get_days(self):
        """
            Get the number of days.
            
                >>> d = Delta(days=5)
                >>> d.days
                5
            
            @rtype: int
            @return: Number of days
        """
        return self.td.days % 365 % 30
    
    def _set_days(self, value):
        """
            Set the number of days.
            
                >>> d = Delta()
                >>> d.days = 5
                >>> d.days
                5
            
            @type value: int or long
            @param value: Number of days
        """
        value -= self.days
        self.td = timedelta(seconds=self.total_seconds + (value * 60.0 * 60 * 24))
    
    days = property(_get_days, _set_days)
    
    @property
    def total_days(self):
        """
            Get the total number of days in this delta.
            
                >>> d = Delta(months=3)
                >>> d.total_days
                90.0
            
            @rtype: float
            @return: Number of days
        """
        return self.td.days + (self.td.seconds / 24.0 / 60.0 / 60.0) + (self.td.microseconds / 100000.0 / 60.0 / 60.0 / 24.0)
    
    def _get_months(self):
        """
            Get the number of months.
            
                >>> d = Delta(years=0.9)
                >>> d.months
                10
            
            @rtype: int
            @return: Number of months
        """
        return self.td.days % 365 / 30
    
    def _set_months(self, value):
        """
            Set the number of months.
            
                >>> d = Delta()
                >>> d.months = 7
                >>> d.months
                7
            
            @type value: int or long
            @param value: Number of months
        """
        value -= self.months
        self.td = timedelta(seconds=self.total_seconds + (value * 60.0 * 60 * 24 * 30))
    
    months = property(_get_months, _set_months)
    
    @property
    def total_months(self):
        """
            Get the total number of months in this delta.
            
                >>> d = Delta(days=90)
                >>> d.total_months
                3.0
            
            @rtype: float
            @return: Number of months
        """
        return self.td.days / 30.0 + (self.td.seconds / 30.0 / 24.0 / 60.0 / 60.0) + (self.td.microseconds / 1000000.0 / 30.0 / 24.0 / 60.0 / 60.0)
    
    def _get_years(self):
        """
            Get the number of years.
            
                >>> d = Delta(years=1)
                >>> d.years
                1
            
            @rtype: int
            @return: Number of years
        """
        return self.td.days / 365
    
    def _set_years(self, value):
        """
            Set the number of years.
            
                >>> d = Delta()
                >>> d.years = 9
                >>> d.years
                9
            
            @type value: int or long
            @param value: Number of years
        """
        value -= self.years
        self.td = timedelta(seconds=self.total_seconds + (value * 60.0 * 60 * 24 * 365))
    
    years = property(_get_years, _set_years)
    
    @property
    def total_years(self):
        """
            Get the total number of years for this delta.
            
                >>> d = Delta(days=1095)
                >>> d.total_years
                3.0
            
            @rtype: float
            @return: Number of years
        """
        return self.td.days / 365.0 + (self.td.seconds / 365.0 / 24.0 / 60.0 / 60.0) + (self.td.microseconds / 1000000.0 / 365.0 / 24.0 / 60.0 / 60.0)

class Date(object):
    """
        An object representing a date and a time. This object has several
        advantages over Python's built-in date and time objects.
        
         * Attributes like the year, month, hour, etc are writable
         * You can easily get the datetime, date, tuple, and timestamp.
           representation of this date.
         * Convenience methods for various string representations.
         * Convenience methods for (start, end) tuples of the current day,
           month, or year.
        
            >>> d = Date(123456)
            >>> str(d)
            'Date(1970-01-02, 11:17:36)'
            >>> d.year += 10
            >>> str(d)
            'Date(1980-01-02, 11:17:36)'
            >>> d.month = 6
            >>> str(d)
            'Date(1980-06-02, 11:17:36)'
            >>> d.day += 256
            >>> str(d)
            'Date(1981-02-13, 11:17:36)'
            >>> d.day, d.month, d.year
            (13, 2, 1981)
            >>> d.tuple                     # doctest: +NORMALIZE_WHITESPACE
            time.struct_time(tm_year=1981, tm_mon=2, tm_mday=13, tm_hour=11,
                             tm_min=17, tm_sec=36, tm_wday=4, tm_yday=44,
                             tm_isdst=-1)
            >>> d.timestamp
            350907456
            >>> d.date
            datetime.date(1981, 2, 13)
            >>> d.datetime
            datetime.datetime(1981, 2, 13, 11, 17, 36)
            >>> d > Date(12345)
            True
            >>> d < Date(12345)
            False
        
    """
    def __init__(self, dt = None, years_ago = 0, months_ago = 0, days_ago = 0,
                 hours_ago = 0, minutes_ago = 0, seconds_ago = 0,
                 format = None, utc = False):
        """
            Create a new Date object, optionally passing in a timestamp, date or 
            datetime object to set the date/time from. If it is not given then 
            the date/time are set to now.
            
                >>> Date(1234567890)
                Date(2009-02-14, 00:31:30)
                >>> Date((2009, 2, 14))
                Date(2009-02-14, 00:00:00)
                >>> Date("2009-02-14", format = "%Y-%m-%d")
                Date(2009-02-14, 00:00:00)
                >>> Date(date(2009, 10, 2))
                Date(2009-10-02, 00:00:00)
                >>> Date(datetime(2007, 3, 24))
                Date(2007-03-24, 00:00:00)
            
            @type dt: timestamp, string, tuple, struct_time, date, or datetime
            @param dt: Date/time to set; if None the current date/time will
                       be set. If it is a string then format must also be set!
            @type years_ago: int
            @param years_ago: The number of years ago from dt to set the date
            @type months_ago: int
            @param months_ago: The number of months ago from dt to set the date
            @type days_ago: int
            @param days_ago: The number of days ago from dt to set the date
            @type hours_ago: int
            @param hours_ago: The number of hours ago from dt to set the date
            @type minutes_ago: int
            @param minutes_ago: The number of minutes ago from dt to set the
                                date
            @type seconds_ago: int
            @param seconds_ago: The number of seconds ago from dt to set the
                                date
            @type format: str
            @param format: The format to pass to strptime if dt is a string.
            @type utc: bool
            @param utc: If dt is None and utc is True, sets the date to 
                        datetime.utcnow instead of datetime.now
            @raise ValueError: If dt is not an int, date, or datetime object
        """
        if dt is None:
            self.dt = datetime.now()
        elif type(dt) in [float, int, long]:
            self.dt = datetime.fromtimestamp(dt)
        elif type(dt) in [str, unicode]:
            if format is None:
                raise ValueError("When passing in a string you must also " \
                                 "pass in a format description!")
            self.dt = datetime.strptime(dt, format)
        elif type(dt) in [list, tuple]:
            self.dt = datetime(*dt)
        elif type(dt) is time.struct_time:
            self.dt = datetime(dt.tm_year, dt.tm_mon, dt.tm_mday, dt.tm_hour, 
                               dt.tm_min, dt.tm_sec)
        elif type(dt) is date:
            self.dt = datetime.combine(dt, datetime.min.time())
        elif type(dt) is datetime:
            self.dt = dt
        else:
            raise ValueError("You must pass an int, long, float, 9-item " \
                             "list or tuple, date or datetime object! Got " \
                             "%s instead!" % str(dt))
        
        # Add / subtract time as requested
        self.add(**{
            "years": -years_ago,
            "months": -months_ago,
            "days": -days_ago,
            "hours": -hours_ago,
            "minutes": -minutes_ago,
            "seconds": -seconds_ago
        })
        
        if utc:
            self.dt = self.utc.dt
 
    def __repr__(self):
        """
            Return a nice string representation of this date.
            
                >>> str(Date(datetime(2009, 10, 2)))
                'Date(2009-10-02, 00:00:00)'
            
        """
        return self.strftime("Date(%Y-%m-%d, %H:%M:%S)")
    
    def __add__(self, value):
        """
            Pass additions in to the datetime object so that timedeltas still
            work!
            
                >>> d = Date(1234567890)
                >>> d + timedelta(days = 2)
                Date(2009-02-16, 00:31:30)
            
            @rtype: Date
            @return: The modified date object
        """
        if type(value) == Delta:
            value = value.timedelta
        
        return Date(self.dt.__add__(value))
    
    def __sub__(self, value):
        """
            Subtract a time delta or one date from another.
            
                >>> d1 = Date(1234567890)
                >>> d2 = Date(1234567900)
                >>> delta = d2 - d1
                >>> delta
                Delta(10 seconds)
                >>> d1
                Date(2009-02-14, 00:31:30)
                >>> d1 + delta
                Date(2009-02-14, 00:31:40)
            
            @rtype: Date or timedelta
            @return: The modified date object or date/time difference
        """
        if type(value) is timedelta:
            return Date(self.dt.__sub__(value))
        elif type(value) is Delta:
            return Date(self.dt.__sub__(value.timedelta))
        elif type(value) is Date:
            return Delta(self.dt - value.dt)
        else:
            raise TypeError("Expected Date or timedelta!")
    
    def __cmp__(self, value):
        """
            Compare this date object to another date object.
            
                >>> Date(12345) > Date(1234)
                True
                >>> Date(12345) < Date(1234)
                False
                >>> Date(12345) == Date(12345)
                True
            
            @rtype: int
            @return: -1 if it is smaller, 0 if they are equal, 1 if it is
                     greater than the other date object
        """
        if type(value) == Date:
            return cmp(self.dt, value.dt)
        else:
            raise TypeError("Invalid type!")
    
    def _get_datetime(self):
        """
            Return a datetime representation of this date/time, as would be
            given by datetime(...)
            
                >>> Date(1234567890).datetime
                datetime.datetime(2009, 2, 14, 0, 31, 30)
            
            @rtype: datetime
            @return: The datetime representation of this date/timme
        """
        return self.dt
    
    def _set_datetime(self, value):
        """
            Set the time from a datetime object.
            
                >>> d = Date(1234567890)
                >>> d.datetime = datetime(2009, 02, 14)
                >>> d
                Date(2009-02-14, 00:00:00)
            
            @type value: datetime
            @param value: The date/time to set
        """
        self.dt = value
    
    datetime = property(_get_datetime, _set_datetime)
    
    def _get_date(self):
        """
            Return a date representation of this date/time, as would be
            given by date(...)
            
                >>> Date(1234567890).date
                datetime.date(2009, 2, 14)
            
            @rtype: date
            @return: The date representation of this date/timme
        """
        return self.dt.date()
    
    def _set_date(self, value):
        """
            Set the date from a date object.
            
                >>> d = Date(1234567890)
                >>> d.date = date(2009, 2, 14)
                >>> d
                Date(2009-02-14, 00:31:30)
            
            @type value: date
            @param value: The date to set
        """
        self.dt = datetime.combine(value, self.dt.time())
    
    date = property(_get_date, _set_date)
    
    def _get_time(self):
        """
            Return a time representation of this date/time, as would be
            given by time(...)
            
                >>> Date(1234567890).time
                datetime.time(0, 31, 30)
            
            @rtype: time
            @return: The time representation of this date/timme
        """
        return self.dt.time()
    
    def _set_time(self, value):
        """
            Set the time from a time object.
            
                >>> d = Date(1234567890)
                >>> d.time = datetime(1980, 5, 23, 11, 2, 45).time()
                >>> d
                Date(2009-02-14, 11:02:45)
            
            @type value: time
            @param value: The time to set
        """
        self.dt = datetime.combine(self.dt.date(), value)
    
    time = property(_get_time, _set_time)
    
    def _get_tuple(self):
        """
            Return a tuple representation of this time, as would be given
            by datetime.timetuple()
            
                >>> Date(1234567890).tuple  # doctest: +NORMALIZE_WHITESPACE
                time.struct_time(tm_year=2009, tm_mon=2, tm_mday=14, 
                                 tm_hour=0, tm_min=31, tm_sec=30, tm_wday=5, 
                                 tm_yday=45, tm_isdst=-1)
            
            @rtype: time.struct_time
            @return: (year, month, day, hour, minute, second, weekday, 
                      year day, is daylight saving)
        """
        return self.dt.timetuple()
    
    def _set_tuple(self, value):
        """
            Set the time from a tuple as would be given by datetime.timetuple()
            
                >>> d = Date()
                >>> d.tuple = (2009, 2, 14, 0, 31, 30, 0, 0, -1)
                >>> d
                Date(2009-02-14, 00:31:30)
            
            @type value: time.struct_time or tuple
            @param value: (year, month, day, hour, minute, second, microsecond,
                           ?, tz)
        """
        self.dt = self.dt.fromtimestamp(int(time.mktime(value)))
    
    tuple = property(_get_tuple, _set_tuple)
    
    def _get_timestamp(self):
        """
            Get this date represented as a Unix timestamp. If this date is
            beyond MAX defined above, then MAX_TS is returned to prevent
            ValueError exceptions when converting to a timestamp.
            
                >>> Date(1234567890).timestamp
                1234567890
            
            Note: You cannot represent all possible dates with a timestamp
            value, and if you attempt to you may get an exception!
            
            @rtype: int
            @return: The timestamp representation of this date
        """
        if self > MAX:
            return MAX.timestamp
        else:
            return int(time.mktime(self.dt.timetuple()))
    
    def _set_timestamp(self, value):
        """
            Set this date from a Unix timestamp.
            
                >>> d = Date()
                >>> d.timestamp = 1234567890
                >>> d
                Date(2009-02-14, 00:31:30)
            
            @type value: int
            @param value: The timestamp to set
        """
        self.dt = self.dt.fromtimestamp(value)
    
    timestamp = property(_get_timestamp, _set_timestamp)
 
    def _get_year(self):
        """
            Get this date's year.
            
                >>> Date(1234567890).year
                2009
            
            @rtype: int
            @return: The currently set year [0, 9999]
        """
        return self.dt.year
    
    def _set_year(self, value):
        """
            Set this dates year.
            
                >>> d = Date(1234567890)
                >>> d.year = 1984
                >>> d
                Date(1984-02-14, 00:31:30)
                >>> d.year += 6
                >>> d
                Date(1990-02-14, 00:31:30)
            
            @type value: int
            @param value: The year to set
        """
        self.dt = self.dt.replace(year = value)
    
    year = property(_get_year, _set_year)
    
    def _get_month(self):
        """
            Get this date's month.
            
                >>> Date(1234567890).month
                2
            
            @rtype: int
            @return: The currently set month [1, 12]
        """
        return self.dt.month
    
    def _set_month(self, value):
        """
            Set this date's month. If passed a value larger than 12 then the
            year will roll over.
            
                >>> d = Date(1234567890)
                >>> d.month = 6
                >>> d
                Date(2009-06-14, 00:31:30)
                >>> d.month -= 3
                >>> d
                Date(2009-03-14, 00:31:30)
            
            @type value: int
            @param value: The month to set
        """
        self.dt += relativedelta(months = value - self.dt.month)
    
    month = property(_get_month, _set_month)
    
    def _get_week(self):
        """
            Get this date's week of the year.
            
                >>> Date(1234567890).week
                6
            
            @rtype: int
            @return: The currently set week [1, 52]
        """
        delta = self.dt - datetime(self.dt.year, 1, 1)
        return delta.days / 7
    
    def _set_week(self, value):
        """
            Set this date to the given week of the current year. If the current
            day is e.g. a Tuesday then after this operation it will still be
            a Tuesday. If passed a value larger than 52 then the year will roll
            over.
            
                >>> d = Date(1234567890)
                >>> d.week = 12
                >>> d
                Date(2009-03-28, 00:31:30)
            
            @type value: int
            @param value: The week to set
        """
        week = self._get_week()
        self.dt += timedelta(weeks = value - week)
    
    week = property(_get_week, _set_week)
    
    def _get_day(self):
        """
            Get this date's day.
            
                >>> Date(1234567890).day
                14
            
            @rtype: int
            @return: The currently set day
        """
        return self.dt.day
    
    def _set_day(self, value):
        """
            Set this date's day. To set the day to the last day of the month
            please use either Date.end_of_month or Date.days_in_month, as
            setting it to a value larger than the number of days in the current
            month will cause the month to roll over!
            
                >>> d = Date(1234567890)
                >>> d.day = 1
                >>> d
                Date(2009-02-01, 00:31:30)
            
            @type value: int
            @param int: The day to set
        """
        self.dt += timedelta(days = value - self.dt.day)
    
    day = property(_get_day, _set_day)
    
    def _get_hour(self):
        """
            Get this date's hour.
            
                >>> Date(1234567890).hour
                0
            
            @rtype: int
            @return: The currently set hour
        """
        return self.dt.hour
    
    def _set_hour(self, value):
        """
            Set this date's hour. If set to a value larger than 24 it will
            cause the day to roll over.
            
                >>> d = Date(1234567890)
                >>> d.hour = 10
                >>> d
                Date(2009-02-14, 10:31:30)
            
            @type value: int
            @param value: The hour to set
        """
        self.dt += timedelta(hours = value - self.dt.hour)
    
    hour = property(_get_hour, _set_hour)
    
    def _get_minute(self):
        """
            Get this date's minute.
            
                >>> Date(1234567890).minute
                31
            
            @rtype: int
            @return: The currently set minute
        """
        return self.dt.minute
    
    def _set_minute(self, value):
        """
            Set this date's minute. If set larger than 60 it will cause the 
            hour to roll over.
            
                >>> d = Date(1234567890)
                >>> d.minute = 5
                >>> d
                Date(2009-02-14, 00:05:30)
            
            @type value: int
            @param value: The minute to set
        """
        self.dt += timedelta(minutes = value - self.dt.minute)
    
    minute = property(_get_minute, _set_minute)
    
    def _get_second(self):
        """
            Get this date's second.
            
                >>> Date(1234567890).second
                30
            
            @rtype: int
            @return: The currently set second
        """
        return self.dt.second
    
    def _set_second(self, value):
        """
            Set this date's second. If set larger than 60 it will cause the
            minute to roll over.
            
                >>> d = Date(1234567890)
                >>> d.second = 5
                >>> d
                Date(2009-02-14, 00:31:05)
            
            @type value: int
            @param value: The second to set
        """
        self.dt += timedelta(seconds = value - self.dt.second)
    
    second = property(_get_second, _set_second)
    
    def _get_microsecond(self):
        """
            Get this date's microsecond.
            
                >>> Date(1234567890).microsecond
                0
            
            @rtype: int
            @return: The currently set microsecond
        """
        return self.dt.microsecond
    
    def _set_microsecond(self, value):
        """
            Set this date's microsecond.
            
                >>> d = Date(1234567890)
                >>> d.microsecond = 250
            
            @rtype value: int
            @param value: The microsecond to set
        """
        self.dt += timedelta(microseconds = value - self.dt.microsecond)
    
    microsecond = property(_get_microsecond, _set_microsecond)
    
    def add(self, years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
        """
            Add a number of years, months, days, hours, minutes, or seconds
            and return the modified Date.
        """
        for unit in ["years", "months", "days", "hours", "minutes", "seconds"]:
            setattr(self, unit[:-1], getattr(self, unit[:-1]) + locals()[unit])
        
        return self
    
    @property
    def utc(self):
        """
            Get a UTC version of this Date object.
            
                >>> d = Date(1234567890)
                >>> d.utc
                Date(2009-02-13, 23:31:30)
            
            @rtype: Date
            @return: A new UTC Date object
        """
        return Date(time.gmtime(self.timestamp))
    
    @property
    def days_in_month(self):
        """
            Get the number of days in the currently set date's month.
            
                >>> Date(1234567890).days_in_month
                28
                >>> Date(472812932).days_in_month
                31
            
            @rtype: int
            @return: The number of days in the month
        """
        return calendar.monthrange(self.year, self.month)[1]
    
    def strftime(self, format = "%d %b %Y"):
        """
            Convert this date to a string. See time.strftime(...).
            
                >>> Date(1234567890).strftime("%Y-%m-%d, %H:%M:%S")
                '2009-02-14, 00:31:30'
            
            @type format: str
            @param format: The format string, see time.strftime(...)
            @rtype: str
            @return: The string representation of this date from format
        """
        return time.strftime(format, self.tuple)
    
    @property
    def start_of_day(self):
        """
            Get a new date with the time part of this date/time set to zero,
            i.e. 00:00:00.000000.
            
                >>> Date(1234567890).start_of_day
                Date(2009-02-14, 00:00:00)
            
            @rtype: Date
            @return: A new date with min time
        """
        tuple = self.dt.timetuple()
        return Date(datetime(tuple[0], tuple[1], tuple[2]))
    
    @property
    def end_of_day(self):
        """
            Get a new date with the time part of this date/time set to the max,
            i.e. 23:59:59.999999.
            
                >>> Date(1234567890).end_of_day
                Date(2009-02-14, 23:59:59)
            
            @rtype: Date
            @return: A new date with max time
        """
        tuple = self.dt.timetuple()
        return Date(datetime(tuple[0], tuple[1], tuple[2], 23, 59, 59, 999999))
    
    @property
    def start_of_week(self):
        """
            Get the start date/time of this week.
            
                >>> Date(1234567890).start_of_week
                Date(2009-02-09, 00:00:00)
            
            @rtype: Date
            @return: A new date set to the beginning of this week
        """
        d = self.start_of_day
        d.day -= d.dt.weekday()
        return d
    
    @property
    def end_of_week(self):
        """
            Get the end date/time of this week.
            
                >>> Date(1234567890).end_of_week
                Date(2009-02-15, 23:59:59)
            
            @rtype: Date
            @return: A new date set to the end of this week
        """
        d = self.end_of_day
        d.day += (6 - d.dt.weekday())
        return d
    
    @property
    def start_of_month(self):
        """
            Get the start date/time of this month.
            
                >>> Date(1234567890).start_of_month
                Date(2009-02-01, 00:00:00)
            
            @rtype: Date
            @return: A new date set to the beginning of this month
        """
        return Date(datetime(self.dt.year, self.dt.month, 1))
    
    @property
    def end_of_month(self):
        """
            Get the end date/time of this month.
            
                >>> Date(1234567890).end_of_month
                Date(2009-02-28, 23:59:59)
            
            @rtype: Date
            @return: A new date set to the end of this month
        """
        return Date(datetime(self.dt.year, self.dt.month, 1, 23, 59, 59, 
                    999999) + relativedelta(months = 1, days = -1))
    
    @property
    def start_of_year(self):
        """
            Get the start date/time of this year.
            
                >>> Date(1234567890).start_of_year
                Date(2009-01-01, 00:00:00)
            
            @rtype: Date
            @return: A new date set to the beginning of this year
        """
        return Date(datetime(self.dt.year, 1, 1))
    
    @property
    def end_of_year(self):
        """
            Get the end date/time of this year.
            
                >>> Date(1234567890).end_of_year
                Date(2009-12-31, 23:59:59)
            
            @rtype: Date
            @return: A new date set to the end of this year
        """
        return Date(datetime(self.dt.year, 1, 1, 23, 59, 59, 999999) + \
                             relativedelta(years = 1, days = -1))
    
    @property
    def day_tuple(self):
        """
            Get a tuple of two L{Date}s representing the start and end of this
            day.
            
                >>> Date(1234567890).day_tuple
                (Date(2009-02-14, 00:00:00), Date(2009-02-14, 23:59:59))
                >>> tuple([d.timestamp for d in Date(1234567890).day_tuple])
                (1234566000, 1234652399)
            
            @rtype: tuple
            @return: (start, end) dates of the current day
        """
        return (self.start_of_day, self.end_of_day)
    
    @property
    def week_tuple(self):
        """
            Get a tuple of two L{Date}s representing the start and end of this
            week.
            
                >>> Date(1234567890).week_tuple
                (Date(2009-02-09, 00:00:00), Date(2009-02-15, 23:59:59))
            
            @rtype: tuple
            @return: (start, end) dates of the current week
        """
        return (self.start_of_week, self.end_of_week)
    
    @property
    def month_tuple(self):
        """
            Get a tuple of two L{Date}s representing the start and end of this
            month.
            
                >>> Date(1234567890).month_tuple
                (Date(2009-02-01, 00:00:00), Date(2009-02-28, 23:59:59))
                >>> tuple([d.date for d in Date(1234567890).month_tuple])
                (datetime.date(2009, 2, 1), datetime.date(2009, 2, 28))
            
            @rtype: tuple
            @return: (start, end) dates of the current month
        """
        return (self.start_of_month, self.end_of_month)
    
    @property
    def year_tuple(self):
        """
            Get a tuple of two L{Date}s representing the start and end of this
            year.
            
                >>> Date(1234567890).year_tuple
                (Date(2009-01-01, 00:00:00), Date(2009-12-31, 23:59:59))
            
            @rtype: tuple
            @return: (start, end) dates of the current year
        """
        return (self.start_of_year, self.end_of_year)
    
    @property
    def friendly(self):
        """
            Get a friendly representation of this date.
            
                >>> Date(datetime(2009, 2, 15)).friendly
                '15 Feb 2009'
            
            @rtype: str
            @return: The friendly representation of this date
        """
        return self.strftime("%d %b %Y")
    
    def _get_fancy(self, display_year = True):
        """
            Get a fancy representation of this date for invoices, forms, etc.
            
                >>> Date(datetime(2009, 2, 15)).fancy
                'February 15th, 2009'
            
            @rtype: str
            @return: The fancy representation of this date
        """
        if self.dt.day in [1, 21, 31]:
            extra = "st"
        elif self.dt.day == 2:
            extra = "nd"
        elif self.dt.day == 3:
            extra = "rd"
        else:
            extra = "th"
        
        if display_year:
            extra += ", %Y"
        
        return self.strftime("%B %d" + extra)
    
    fancy = property(_get_fancy)
    
    @property
    def fancy_no_year(self):
        """
            Get a fancy representation of this date for invoices, forms, etc.
            This version does not include the year!
            
                >>> Date(datetime(2009, 2, 15)).fancy_no_year
                'February 15th'
            
            @rtype: str
            @return: The fancy representation of this date minus the year
        """
        return self._get_fancy(False)
    
    @property
    def sql_date(self):
        """
            Return just the date portion of the SQL-friendly representation
            of this date/time.
            
                >>> Date(1234567890).sql_date
                "'2009-02-14'"
            
            @rtype: str
            @return: SQL-friendly representation of this date
        """
        return self.strftime("'%Y-%m-%d'")
    
    @property
    def sql_time(self):
        """
            Return just the time portion of the SQL-friendly representation
            of this date/time.
            
                >>> Date(1234567890).sql_time
                "'00:31:30'"
            
            @rtype: str
            @return: SQL-friendly representation of this time
        """
        return self.strftime("'%H:%M:%S'")
    
    @property
    def sql(self):
        """
            Get an SQL-friendly representation of this date/time that can be
            used in SQL expressions to be passed to a backend database.
            
                >>> Date(1234567890).sql
                "'2009-02-14 00:31:30'"
            
            @rtype: str
            @return: SQL-friendly representation of this date/time
        """
        return self.sql_date[:-1] + " " + self.sql_time[1:]
    
    @property
    def is_today(self):
        """
            Return whether this date is today or not.
            
                >>> Date(1234567890).is_today
                False
                >>> Date().is_today
                True
            
            @rtype: bool
            @return: True if this date is today, False otherwise
        """
        return self.dt.date() == datetime.today().date()
    
    @property
    def is_future_date(self):
        """
            Return whether this date (ignoring time) is in the future.
            
                >>> Date().is_future_date
                False
                >>> Date(days_ago = -1).is_future_date
                True
            
            @rtype: bool
            @return: True if this date is in the future, False otherwise
        """
        return self.dt.date() > datetime.today().date()
    
    @property
    def is_past_date(self):
        """
            Return whether this date (ignoring time) is in the past.
            
                >>> Date().is_past_date
                False
                >>> Date(12345).is_past_date
                True
            
            @rtype: bool
            @return: True if this date is in the past, False otherwise
        """
        return self.dt.date() < datetime.today().date()

"""
    ===========================================================================
    Begin relativedelta code
    Copyright (c) 2003-2007  Gustavo Niemeyer <gustavo@niemeyer.net>
    License: PSF
    ===========================================================================
"""

class weekday(object):
    __slots__ = ["weekday", "n"]

    def __init__(self, weekday, n=None):
        self.weekday = weekday
        self.n = n

    def __call__(self, n):
        if n == self.n:
            return self
        else:
            return self.__class__(self.weekday, n)

    def __eq__(self, other):
        try:
            if self.weekday != other.weekday or self.n != other.n:
                return False
        except AttributeError:
            return False
        return True

    def __repr__(self):
        s = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")[self.weekday]
        if not self.n:
            return s
        else:
            return "%s(%+d)" % (s, self.n)

MO, TU, WE, TH, FR, SA, SU = weekdays = tuple([weekday(x) for x in range(7)])

class relativedelta:
    """
The relativedelta type is based on the specification of the excelent
work done by M.-A. Lemburg in his mx.DateTime extension. However,
notice that this type does *NOT* implement the same algorithm as
his work. Do *NOT* expect it to behave like mx.DateTime's counterpart.

There's two different ways to build a relativedelta instance. The
first one is passing it two date/datetime classes:

    relativedelta(datetime1, datetime2)

And the other way is to use the following keyword arguments:

    year, month, day, hour, minute, second, microsecond:
        Absolute information.

    years, months, weeks, days, hours, minutes, seconds, microseconds:
        Relative information, may be negative.

    weekday:
        One of the weekday instances (MO, TU, etc). These instances may
        receive a parameter N, specifying the Nth weekday, which could
        be positive or negative (like MO(+1) or MO(-2). Not specifying
        it is the same as specifying +1. You can also use an integer,
        where 0=MO.

    leapdays:
        Will add given days to the date found, if year is a leap
        year, and the date found is post 28 of february.

    yearday, nlyearday:
        Set the yearday or the non-leap year day (jump leap days).
        These are converted to day/month/leapdays information.

Here is the behavior of operations with relativedelta:

1) Calculate the absolute year, using the 'year' argument, or the
   original datetime year, if the argument is not present.

2) Add the relative 'years' argument to the absolute year.

3) Do steps 1 and 2 for month/months.

4) Calculate the absolute day, using the 'day' argument, or the
   original datetime day, if the argument is not present. Then,
   subtract from the day until it fits in the year and month
   found after their operations.

5) Add the relative 'days' argument to the absolute day. Notice
   that the 'weeks' argument is multiplied by 7 and added to
   'days'.

6) Do steps 1 and 2 for hour/hours, minute/minutes, second/seconds,
   microsecond/microseconds.

7) If the 'weekday' argument is present, calculate the weekday,
   with the given (wday, nth) tuple. wday is the index of the
   weekday (0-6, 0=Mon), and nth is the number of weeks to add
   forward or backward, depending on its signal. Notice that if
   the calculated date is already Monday, for example, using
   (0, 1) or (0, -1) won't change the day.
    """

    def __init__(self, dt1=None, dt2=None,
                 years=0, months=0, days=0, leapdays=0, weeks=0,
                 hours=0, minutes=0, seconds=0, microseconds=0,
                 year=None, month=None, day=None, weekday=None,
                 yearday=None, nlyearday=None,
                 hour=None, minute=None, second=None, microsecond=None):
        if dt1 and dt2:
            if not isinstance(dt1, datetime.date) or \
               not isinstance(dt2, datetime.date):
                raise TypeError, "relativedelta only diffs datetime/date"
            if type(dt1) is not type(dt2):
                if not isinstance(dt1, datetime):
                    dt1 = datetime.fromordinal(dt1.toordinal())
                elif not isinstance(dt2, datetime):
                    dt2 = datetime.fromordinal(dt2.toordinal())
            self.years = 0
            self.months = 0
            self.days = 0
            self.leapdays = 0
            self.hours = 0
            self.minutes = 0
            self.seconds = 0
            self.microseconds = 0
            self.year = None
            self.month = None
            self.day = None
            self.weekday = None
            self.hour = None
            self.minute = None
            self.second = None
            self.microsecond = None
            self._has_time = 0

            months = (dt1.year*12+dt1.month)-(dt2.year*12+dt2.month)
            self._set_months(months)
            dtm = self.__radd__(dt2)
            if dt1 < dt2:
                while dt1 > dtm:
                    months += 1
                    self._set_months(months)
                    dtm = self.__radd__(dt2)
            else:
                while dt1 < dtm:
                    months -= 1
                    self._set_months(months)
                    dtm = self.__radd__(dt2)
            delta = dt1 - dtm
            self.seconds = delta.seconds+delta.days*86400
            self.microseconds = delta.microseconds
        else:
            self.years = years
            self.months = months
            self.days = days+weeks*7
            self.leapdays = leapdays
            self.hours = hours
            self.minutes = minutes
            self.seconds = seconds
            self.microseconds = microseconds
            self.year = year
            self.month = month
            self.day = day
            self.hour = hour
            self.minute = minute
            self.second = second
            self.microsecond = microsecond

            if type(weekday) is int:
                self.weekday = weekdays[weekday]
            else:
                self.weekday = weekday

            yday = 0
            if nlyearday:
                yday = nlyearday
            elif yearday:
                yday = yearday
                if yearday > 59:
                    self.leapdays = -1
            if yday:
                ydayidx = [31,59,90,120,151,181,212,243,273,304,334,366]
                for idx, ydays in enumerate(ydayidx):
                    if yday <= ydays:
                        self.month = idx+1
                        if idx == 0:
                            self.day = ydays
                        else:
                            self.day = yday-ydayidx[idx-1]
                        break
                else:
                    raise ValueError, "invalid year day (%d)" % yday

        self._fix()

    def _fix(self):
        if abs(self.microseconds) > 999999:
            s = self.microseconds//abs(self.microseconds)
            div, mod = divmod(self.microseconds*s, 1000000)
            self.microseconds = mod*s
            self.seconds += div*s
        if abs(self.seconds) > 59:
            s = self.seconds//abs(self.seconds)
            div, mod = divmod(self.seconds*s, 60)
            self.seconds = mod*s
            self.minutes += div*s
        if abs(self.minutes) > 59:
            s = self.minutes//abs(self.minutes)
            div, mod = divmod(self.minutes*s, 60)
            self.minutes = mod*s
            self.hours += div*s
        if abs(self.hours) > 23:
            s = self.hours//abs(self.hours)
            div, mod = divmod(self.hours*s, 24)
            self.hours = mod*s
            self.days += div*s
        if abs(self.months) > 11:
            s = self.months//abs(self.months)
            div, mod = divmod(self.months*s, 12)
            self.months = mod*s
            self.years += div*s
        if (self.hours or self.minutes or self.seconds or self.microseconds or
            self.hour is not None or self.minute is not None or
            self.second is not None or self.microsecond is not None):
            self._has_time = 1
        else:
            self._has_time = 0

    def _set_months(self, months):
        self.months = months
        if abs(self.months) > 11:
            s = self.months//abs(self.months)
            div, mod = divmod(self.months*s, 12)
            self.months = mod*s
            self.years = div*s
        else:
            self.years = 0

    def __radd__(self, other):
        if not isinstance(other, date):
            raise TypeError, "unsupported type for add operation"
        elif self._has_time and not isinstance(other, datetime):
            other = datetime.fromordinal(other.toordinal())
        year = (self.year or other.year)+self.years
        month = self.month or other.month
        if self.months:
            assert 1 <= abs(self.months) <= 12
            month += self.months
            if month > 12:
                year += 1
                month -= 12
            elif month < 1:
                year -= 1
                month += 12
        day = min(calendar.monthrange(year, month)[1],
                  self.day or other.day)
        repl = {"year": year, "month": month, "day": day}
        for attr in ["hour", "minute", "second", "microsecond"]:
            value = getattr(self, attr)
            if value is not None:
                repl[attr] = value
        days = self.days
        if self.leapdays and month > 2 and calendar.isleap(year):
            days += self.leapdays
        ret = (other.replace(**repl)
               + timedelta(days=days,
                                    hours=self.hours,
                                    minutes=self.minutes,
                                    seconds=self.seconds,
                                    microseconds=self.microseconds))
        if self.weekday:
            weekday, nth = self.weekday.weekday, self.weekday.n or 1
            jumpdays = (abs(nth)-1)*7
            if nth > 0:
                jumpdays += (7-ret.weekday()+weekday)%7
            else:
                jumpdays += (ret.weekday()-weekday)%7
                jumpdays *= -1
            ret += timedelta(days=jumpdays)
        return ret

    def __rsub__(self, other):
        return self.__neg__().__radd__(other)

    def __add__(self, other):
        if not isinstance(other, relativedelta):
            raise TypeError, "unsupported type for add operation"
        return relativedelta(years=other.years+self.years,
                             months=other.months+self.months,
                             days=other.days+self.days,
                             hours=other.hours+self.hours,
                             minutes=other.minutes+self.minutes,
                             seconds=other.seconds+self.seconds,
                             microseconds=other.microseconds+self.microseconds,
                             leapdays=other.leapdays or self.leapdays,
                             year=other.year or self.year,
                             month=other.month or self.month,
                             day=other.day or self.day,
                             weekday=other.weekday or self.weekday,
                             hour=other.hour or self.hour,
                             minute=other.minute or self.minute,
                             second=other.second or self.second,
                             microsecond=other.second or self.microsecond)

    def __sub__(self, other):
        if not isinstance(other, relativedelta):
            raise TypeError, "unsupported type for sub operation"
        return relativedelta(years=other.years-self.years,
                             months=other.months-self.months,
                             days=other.days-self.days,
                             hours=other.hours-self.hours,
                             minutes=other.minutes-self.minutes,
                             seconds=other.seconds-self.seconds,
                             microseconds=other.microseconds-self.microseconds,
                             leapdays=other.leapdays or self.leapdays,
                             year=other.year or self.year,
                             month=other.month or self.month,
                             day=other.day or self.day,
                             weekday=other.weekday or self.weekday,
                             hour=other.hour or self.hour,
                             minute=other.minute or self.minute,
                             second=other.second or self.second,
                             microsecond=other.second or self.microsecond)

    def __neg__(self):
        return relativedelta(years=-self.years,
                             months=-self.months,
                             days=-self.days,
                             hours=-self.hours,
                             minutes=-self.minutes,
                             seconds=-self.seconds,
                             microseconds=-self.microseconds,
                             leapdays=self.leapdays,
                             year=self.year,
                             month=self.month,
                             day=self.day,
                             weekday=self.weekday,
                             hour=self.hour,
                             minute=self.minute,
                             second=self.second,
                             microsecond=self.microsecond)

    def __nonzero__(self):
        return not (not self.years and
                    not self.months and
                    not self.days and
                    not self.hours and
                    not self.minutes and
                    not self.seconds and
                    not self.microseconds and
                    not self.leapdays and
                    self.year is None and
                    self.month is None and
                    self.day is None and
                    self.weekday is None and
                    self.hour is None and
                    self.minute is None and
                    self.second is None and
                    self.microsecond is None)

    def __mul__(self, other):
        f = float(other)
        return relativedelta(years=self.years*f,
                             months=self.months*f,
                             days=self.days*f,
                             hours=self.hours*f,
                             minutes=self.minutes*f,
                             seconds=self.seconds*f,
                             microseconds=self.microseconds*f,
                             leapdays=self.leapdays,
                             year=self.year,
                             month=self.month,
                             day=self.day,
                             weekday=self.weekday,
                             hour=self.hour,
                             minute=self.minute,
                             second=self.second,
                             microsecond=self.microsecond)

    def __eq__(self, other):
        if not isinstance(other, relativedelta):
            return False
        if self.weekday or other.weekday:
            if not self.weekday or not other.weekday:
                return False
            if self.weekday.weekday != other.weekday.weekday:
                return False
            n1, n2 = self.weekday.n, other.weekday.n
            if n1 != n2 and not ((not n1 or n1 == 1) and (not n2 or n2 == 1)):
                return False
        return (self.years == other.years and
                self.months == other.months and
                self.days == other.days and
                self.hours == other.hours and
                self.minutes == other.minutes and
                self.seconds == other.seconds and
                self.leapdays == other.leapdays and
                self.year == other.year and
                self.month == other.month and
                self.day == other.day and
                self.hour == other.hour and
                self.minute == other.minute and
                self.second == other.second and
                self.microsecond == other.microsecond)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __div__(self, other):
        return self.__mul__(1/float(other))

    def __repr__(self):
        l = []
        for attr in ["years", "months", "days", "leapdays",
                     "hours", "minutes", "seconds", "microseconds"]:
            value = getattr(self, attr)
            if value:
                l.append("%s=%+d" % (attr, value))
        for attr in ["year", "month", "day", "weekday",
                     "hour", "minute", "second", "microsecond"]:
            value = getattr(self, attr)
            if value is not None:
                l.append("%s=%s" % (attr, `value`))
        return "%s(%s)" % (self.__class__.__name__, ", ".join(l))

"""
    ===========================================================================
    End relativedelta code
    ===========================================================================
"""

"""
    The mininum and maximun dates are system-dependent, so we pick some 
    fairly sane defaults below that should be useful for most real-world
    applications. If they are not you can easily override them to suit
    your application domain.
"""
MIN = Date(0)
MAX = Date(datetime(2038, 1, 1))

if __name__ == "__main__":
    import os
    
    # Set the test time zone so dates aren't off by X hours in your local
    # time zone.
    os.environ['TZ'] = 'Europe/Amsterdam'
    time.tzset()
    
    # Run unit tests for this module, e.g. via `python date.py` in a shell.
    import doctest
    doctest.testmod()

