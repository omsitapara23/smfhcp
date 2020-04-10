import elasticsearch
from random import randint
import smfhcp.constants as constants
import datetime
import pytz
import re


class SmfhcpUtils:
    def find_hash(self, input):
        if input is None:
            raise TypeError
        import hashlib
        return hashlib.sha256(str(input).encode(constants.UTF_8)).hexdigest()

    def random_with_n_digits(self, n):
        if n < 1:
            raise ValueError
        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1
        return randint(range_start, range_end)

    def find_user(self, user_name, es):
        try:
            res_user = es.get_general_user_by_user_name(user_name)
            return res_user['_source'], False
        except elasticsearch.NotFoundError:
            try:
                res_doctor = es.get_doctor_by_user_name(user_name)
                return res_doctor['_source'], True
            except elasticsearch.NotFoundError:
                return None, None

    def pretty_date(self, time):
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = now - time
        second_diff = diff.seconds
        day_diff = diff.days
        if day_diff < 0:
            return ''
        elif day_diff == 0:
            if second_diff < 10:
                return "just now"
            if second_diff < 60:
                return str(second_diff) + " seconds ago"
            if second_diff < 120:
                return "a minute ago"
            if second_diff < 3600:
                return str(second_diff // 60) + " minutes ago"
            if second_diff < 7200:
                return "an hour ago"
            else:
                return str(second_diff // 3600) + " hours ago"
        elif day_diff == 1:
            return "Yesterday"
        elif 30 <= day_diff < 365:
            return "{} months ago".format(day_diff // 30)
        elif 1 < day_diff < 30:
            return "{} days ago".format(day_diff)
        return "{} years ago".format(day_diff // 365)

    def create_time_from_utc_string(self, utc_string):
        string = re.sub(constants.UTC_PATTERN, constants.UTC_REPL, utc_string)
        dt = datetime.datetime.strptime(string, constants.UTC_REGEX)
        return dt.astimezone(pytz.UTC)

    def find_if_follows(self, request, doctor_user_name, es):
        if request.session['is_doctor']:
            res = es.get_doctor_by_user_name(request.session['user_name'])
            if "follow_list" in res["_source"] and str(doctor_user_name) in res["_source"]["follow_list"]:
                return True
        else:
            res = es.get_general_user_by_user_name(request.session['user_name'])
            if "follow_list" in res["_source"] and str(doctor_user_name) in res["_source"]["follow_list"]:
                return True
        return False
