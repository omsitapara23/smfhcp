from django.test import TestCase
from unittest.mock import MagicMock, call
import smfhcp.utils.utils as utils
import smfhcp.constants as constants
import elasticsearch


class TestUtils(TestCase):
    smfhcp_utils = utils.SmfhcpUtils()
    es = elasticsearch.Elasticsearch()

    def test_find_hash_when_valid_input(self):
        test_string = "test"
        returned_hash = self.smfhcp_utils.find_hash(test_string)
        import hashlib
        test_hash = hashlib.sha256(test_string.encode(constants.UTF_8)).hexdigest()
        self.assertEqual(returned_hash, test_hash, "Asserted and returned hash did not match.")

    def test_find_hash_when_None_input(self):
        with self.assertRaises(TypeError):
            self.smfhcp_utils.find_hash(None)

    def test_random_with_n_digits_when_n_greater_than_0(self):
        returned_value = self.smfhcp_utils.random_with_n_digits(5)
        self.assertIsInstance(returned_value, int)
        import math
        self.assertEquals(int(math.log10(returned_value))+1, 5)

    def test_random_with_n_digits_when_n_less_than_1(self):
        with self.assertRaises(ValueError):
            self.smfhcp_utils.random_with_n_digits(0)
        with self.assertRaises(ValueError):
            self.smfhcp_utils.random_with_n_digits(-1)

    def test_create_time_from_utc_string(self):
        utc_string = "2020-03-15T06:46:08.899691+00:00"
        returned_time = self.smfhcp_utils.create_time_from_utc_string(utc_string)
        self.assertEqual(str(returned_time.date()), "2020-03-15")
        self.assertEqual(returned_time.ctime().split(" ")[0], "Sun")
        self.assertEqual(str(returned_time.hour), "6")
        self.assertEqual(str(returned_time.minute), "46")
        self.assertEqual(str(returned_time.second), "8")

    def test_find_user_when_general_user(self):
        test_user_name = "test_user_name"
        self.es.get = MagicMock(return_value={'_source': {"test": "pass"}})
        res, is_doctor = self.smfhcp_utils.find_user(test_user_name, self.es)
        self.es.get.assert_called_with(index=constants.GENERAL_USER_INDEX, id=test_user_name)
        self.assertFalse(is_doctor)
        self.assertEqual(res['test'], 'pass')

    def test_find_user_when_doctor(self):
        test_user_name = "test_user_name"
        self.es.get = MagicMock(side_effect=mock_es_get_function_for_doctor)
        res, is_doctor = self.smfhcp_utils.find_user(test_user_name, self.es)
        calls = [call(index=constants.GENERAL_USER_INDEX, id=test_user_name), call(index=constants.DOCTOR_INDEX,
                                                                                   id=test_user_name)]
        self.es.get.assert_has_calls(calls)
        self.assertTrue(is_doctor)
        self.assertEqual(res['test'], 'pass')

    def test_find_user_when_neither_general_user_nor_doctor(self):
        test_user_name = "test_user_name"
        self.es.get = MagicMock(side_effect=mock_es_get_function_for_None)
        res, is_doctor = self.smfhcp_utils.find_user(test_user_name, self.es)
        calls = [call(index=constants.GENERAL_USER_INDEX, id=test_user_name), call(index=constants.DOCTOR_INDEX,
                                                                                   id=test_user_name)]
        self.es.get.assert_has_calls(calls)
        self.assertIsNone(is_doctor)
        self.assertIsNone(res)

    def test_find_if_follows_when_general_user(self):
        request = Request()
        test_user_name = 'test_user_name'
        doctor_user_name = 'test_doctor_user_name'
        request.session = dict()
        request.session['user_name'] = test_user_name
        request.session['is_doctor'] = False
        self.es.get = MagicMock(return_value={'_source': {"follow_list": [doctor_user_name]}})
        res = self.smfhcp_utils.find_if_follows(request, doctor_user_name, self.es)
        self.es.get.assert_called_with(index=constants.GENERAL_USER_INDEX, id=test_user_name)
        self.assertTrue(res)
        self.es.get = MagicMock(return_value={'_source': {"follow_list": []}})
        res = self.smfhcp_utils.find_if_follows(request, doctor_user_name, self.es)
        self.es.get.assert_called_with(index=constants.GENERAL_USER_INDEX, id=test_user_name)
        self.assertFalse(res)
        self.es.get = MagicMock(return_value={'_source': {}})
        res = self.smfhcp_utils.find_if_follows(request, doctor_user_name, self.es)
        self.es.get.assert_called_with(index=constants.GENERAL_USER_INDEX, id=test_user_name)
        self.assertFalse(res)

    def test_find_if_follows_when_doctor(self):
        request = Request()
        test_user_name = 'test_user_name'
        doctor_user_name = 'test_doctor_user_name'
        request.session = dict()
        request.session['user_name'] = test_user_name
        request.session['is_doctor'] = True
        self.es.get = MagicMock(return_value={'_source': {"follow_list": [doctor_user_name]}})
        res = self.smfhcp_utils.find_if_follows(request, doctor_user_name, self.es)
        self.es.get.assert_called_with(index=constants.DOCTOR_INDEX, id=test_user_name)
        self.assertTrue(res)
        self.es.get = MagicMock(return_value={'_source': {"follow_list": []}})
        res = self.smfhcp_utils.find_if_follows(request, doctor_user_name, self.es)
        self.es.get.assert_called_with(index=constants.DOCTOR_INDEX, id=test_user_name)
        self.assertFalse(res)
        self.es.get = MagicMock(return_value={'_source': {}})
        res = self.smfhcp_utils.find_if_follows(request, doctor_user_name, self.es)
        self.es.get.assert_called_with(index=constants.DOCTOR_INDEX, id=test_user_name)
        self.assertFalse(res)

    def test_pretty_date(self):
        import datetime
        test_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)
        diff = self.smfhcp_utils.pretty_date(test_time)
        self.assertEqual(diff, "")
        test_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=9)
        diff = self.smfhcp_utils.pretty_date(test_time)
        self.assertEqual(diff, "just now")
        test_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=20)
        diff = self.smfhcp_utils.pretty_date(test_time)
        self.assertEqual(diff.split(' ', 1)[1], "seconds ago")
        test_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=80)
        diff = self.smfhcp_utils.pretty_date(test_time)
        self.assertEqual(diff, "a minute ago")
        test_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=140)
        diff = self.smfhcp_utils.pretty_date(test_time)
        self.assertEqual(diff, "2 minutes ago")
        test_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1, minutes=1)
        diff = self.smfhcp_utils.pretty_date(test_time)
        self.assertEqual(diff, "an hour ago")
        test_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2, minutes=1)
        diff = self.smfhcp_utils.pretty_date(test_time)
        self.assertEqual(diff, "2 hours ago")
        test_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24, minutes=1)
        diff = self.smfhcp_utils.pretty_date(test_time)
        self.assertEqual(diff, "Yesterday")
        test_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2, hours=2)
        diff = self.smfhcp_utils.pretty_date(test_time)
        self.assertEqual(diff, "2 days ago")
        test_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30, hours=2)
        diff = self.smfhcp_utils.pretty_date(test_time)
        self.assertEqual(diff, "1 months ago")
        test_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365, hours=2)
        diff = self.smfhcp_utils.pretty_date(test_time)
        self.assertEqual(diff, "1 years ago")


def mock_es_get_function_for_doctor(**kwargs):
    for key, value in kwargs.items():
        if key == "index" and value == constants.GENERAL_USER_INDEX:
            raise elasticsearch.NotFoundError
        else:
            return {'_source': {"test": "pass"}}


def mock_es_get_function_for_None(**kwargs):
    for key, value in kwargs.items():
        if key == "index" and value == constants.GENERAL_USER_INDEX:
            raise elasticsearch.NotFoundError
        elif key == "index" and value == constants.DOCTOR_INDEX:
            raise elasticsearch.NotFoundError


class Request(object):
    pass
