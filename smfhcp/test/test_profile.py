import smfhcp.views.profile as profile
from django.test import TestCase
from unittest.mock import MagicMock, patch
import smfhcp.utils.utils as utils
import smfhcp.constants as constants
from django.test import RequestFactory
from django.core.exceptions import PermissionDenied
from django.http import QueryDict
import json

TEST_DOCTOR_NAME = 'test_doctor_name'
TEST_USER_NAME = 'test_user_name'
TEST_EMAIL = 'test_email'
TEST_DATE = 'test_date_utc_string'
TEST_TIME = 'test_time'


class DummyObject(object):
    pass


class TestProfile(TestCase):
    smfhcp_utils = utils.SmfhcpUtils()
    es_dao = DummyObject()
    # es_mapper = DummyObject()
    dummy_function = MagicMock()

    def setUp(self):
        self.factory = RequestFactory()
        for k in list(self.es_dao.__dict__):
            self.es_dao.__delattr__(k)
        for k in list(self.smfhcp_utils.__dict__):
            self.smfhcp_utils.__delattr__(k)

    def permission_denied_test(self, url, function):
        request1 = self.factory.get(url)
        request2 = self.factory.put(url)
        request3 = self.factory.delete(url)
        request4 = self.factory.head(url)
        with self.assertRaises(PermissionDenied):
            _ = function(request1)
            _ = function(request2)
            _ = function(request3)
            _ = function(request4)

    def test_view_profile_when_user_not_authenticated(self):
        request = self.factory.get('/view_profile')
        request.session = dict()
        request.session['is_authenticated'] = False
        response = profile.view_profile(request, 'test_user_name')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    @patch('smfhcp.views.profile.es_dao', es_dao)
    @patch('smfhcp.views.profile.smfhcp_utils', smfhcp_utils)
    def test_view_profile_when_user_authenticated(self):
        self.es_dao.get_doctor_by_user_name = MagicMock(return_value=({
            '_source': {
                'user_name': 'test_user_name',
                'full_name': 'test_full_name',
                'email': 'test_email',
                'qualification': 'test_qualification',
                'research_interests': ['test_research_interests'],
                'profession': 'test_profession',
                'institution': 'test_institution',
                'clinical_interests': ['test_clinical_interests'],
                'follow_list': ['test_doctor_name'],
                'post_count': 0,
                'follower_count': 0,
                'profile_picture': 'test_profile_picture.jpg'
            }
        }))
        self.es_dao.search_posts_by_doctor_name = MagicMock(return_value=({
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'user_name': 'test_user_name',
                            'date': 'test_date_utc_string'
                        }
                    }
                ],
                'total': {
                    'value': 0
                }
            }
        }))
        self.smfhcp_utils.create_time_from_utc_string = MagicMock(return_value=TEST_TIME)
        self.smfhcp_utils.pretty_date = MagicMock(return_value='pretty_date')
        self.smfhcp_utils.find_if_follows = MagicMock(return_value='true')
        request = self.factory.get('/view_profile')
        request.session = dict()
        request.session['is_authenticated'] = True
        response = profile.view_profile(request, 'test_user_name')
        self.assertEqual(response.status_code, 200)
        self.es_dao.get_doctor_by_user_name.assert_called_with('test_user_name')
        self.es_dao.search_posts_by_doctor_name.assert_called_with('test_user_name')
        self.smfhcp_utils.create_time_from_utc_string.assert_called_with(TEST_DATE)
        self.smfhcp_utils.pretty_date.assert_called_with(TEST_TIME)

    @patch('smfhcp.views.profile.es_dao', es_dao)
    @patch('smfhcp.views.profile.smfhcp_utils', smfhcp_utils)
    def test_view_profile_when_user_authenticated_profile_picture_absent(self):
        self.es_dao.get_doctor_by_user_name = MagicMock(return_value=({
            '_source': {
                'user_name': 'test_user_name',
                'full_name': 'test_full_name',
                'email': 'test_email',
                'qualification': 'test_qualification',
                'research_interests': ['test_research_interests'],
                'profession': 'test_profession',
                'institution': 'test_institution',
                'clinical_interests': ['test_clinical_interests'],
                'follow_list': ['test_doctor_name'],
                'post_count': 0,
                'follower_count': 0
            }
        }))
        self.es_dao.search_posts_by_doctor_name = MagicMock(return_value=({
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'user_name': 'test_user_name',
                            'date': 'test_date_utc_string'
                        }
                    }
                ],
                'total': {
                    'value': 1
                }
            }
        }))
        self.smfhcp_utils.create_time_from_utc_string = MagicMock(return_value=TEST_TIME)
        self.smfhcp_utils.pretty_date = MagicMock(return_value='pretty_date')
        self.smfhcp_utils.find_if_follows = MagicMock(return_value='true')
        request = self.factory.get('/view_profile')
        request.session = dict()
        request.session['is_authenticated'] = True
        response = profile.view_profile(request, 'test_user_name')
        self.assertEqual(response.status_code, 200)
        self.es_dao.get_doctor_by_user_name.assert_called_with('test_user_name')
        self.es_dao.search_posts_by_doctor_name.assert_called_with('test_user_name')
        self.smfhcp_utils.create_time_from_utc_string.assert_called_with(TEST_DATE)
        self.smfhcp_utils.pretty_date.assert_called_with(TEST_TIME)

    def test_update_profile_when_request_not_post(self):
        self.permission_denied_test('/update_profile', profile.update_profile)

    @patch('smfhcp.views.profile.es_dao', es_dao)
    def test_update_profile_when_request_post(self):
        self.es_dao.update_profile = MagicMock()
        post_data = {
            'user_name': TEST_USER_NAME
        }
        request = self.factory.post('/update_profile', post_data)
        request.session = dict()
        request.session['user_name'] = 'test_user_name'
        response = profile.update_profile(request)

        query_dict = QueryDict('', mutable=True)
        query_dict.update(post_data)
        self.es_dao.update_profile.assert_called_with('test_user_name', query_dict)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['redirect'], True)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['redirect_url'],
                         '/view_profile/test_user_name')

    def test_follow_or_unfollow_when_request_not_post(self):
        self.permission_denied_test('/follow_or_unfollow', profile.follow_or_unfollow)

    @patch('smfhcp.views.profile.es_dao', es_dao)
    def test_follow_or_unfollow_when_request_post_follow(self):
        self.es_dao.add_to_follow_list = MagicMock()
        post_data = {
            'follow': 'true',
            'doctor_name': 'test_doctor_name'
        }
        request = self.factory.post('/follow_or_unfollow', post_data)
        request.session = dict()
        request.session['user_name'] = 'test_user_name'
        request.session['is_doctor'] = 'true'

        self.es_dao.update_follow_count = MagicMock()
        _ = profile.follow_or_unfollow(request)
        self.es_dao.add_to_follow_list.assert_called_with('test_user_name', 'test_doctor_name', 'true')

        query_dict = QueryDict('', mutable=True)
        query_dict.update(post_data)
        self.es_dao.update_follow_count.assert_called_with(query_dict)

    @patch('smfhcp.views.profile.es_dao', es_dao)
    def test_follow_or_unfollow_when_request_post_unfollow(self):
        self.es_dao.remove_from_follow_list = MagicMock()
        post_data = {
            'follow': 'false',
            'doctor_name': 'test_doctor_name'
        }
        request = self.factory.post('/follow_or_unfollow', post_data)
        request.session = dict()
        request.session['user_name'] = 'test_user_name'
        request.session['is_doctor'] = 'true'

        self.es_dao.update_follow_count = MagicMock()
        _ = profile.follow_or_unfollow(request)
        self.es_dao.remove_from_follow_list.assert_called_with('test_user_name', 'test_doctor_name', 'true')

        query_dict = QueryDict('', mutable=True)
        query_dict.update(post_data)
        self.es_dao.update_follow_count.assert_called_with(query_dict)

    def test_get_follow_list_when_request_not_ajax(self):
        self.permission_denied_test('/get_follow_list', profile.get_follow_list)

    def test_get_follow_list_when_request_ajax_user_not_authenticated(self):
        with self.assertRaises(PermissionDenied):
            request = self.factory.get('/get_follow_list', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            request.session = dict()
            request.session['is_authenticated'] = False
            _ = profile.get_follow_list(request)

    @patch('smfhcp.views.profile.es_dao', es_dao)
    def test_get_follow_list_when_request_ajax_user_authenticated(self):
        self.es_dao.get_doctor_by_user_name = MagicMock(return_value=({
            '_source': {
                'follow_list': ['test_doctor_name']
            }
        }))
        request = self.factory.get('/get_follow_list', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.session = dict()
        request.session['is_authenticated'] = True
        request.session['user_name'] = 'test_user_name'
        response = profile.get_follow_list(request)
        self.es_dao.get_doctor_by_user_name.assert_called_with('test_user_name')
        me = {
            'id': 'test_user_name',
            'name': 'test_user_name'
        }
        talk_body = {
            'id': 'test_doctor_name',
            'name': 'test_doctor_name'
        }
        follow_list = []
        follow_list.append(talk_body)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['me'], me)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['follow_list'], follow_list)
