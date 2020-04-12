from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.test import TestCase
from unittest.mock import MagicMock, patch
import elasticsearch
import smfhcp.views.post as post


TEST_DATE_UTC_STRING = "test_date_utc_string"
TEST_PRETTY_DATE = "2020-05-11 14:12:06.000 05:00"
TEST_POST_ID = "1234"
TEST_USER_NAME = "test_user_name"


class DummyObject(object):
    pass


class TestPost(TestCase):
    smfhcp_utils = DummyObject()
    es_dao = DummyObject()
    es_mapper = DummyObject()
    dummy_function = MagicMock()

    def setUp(self):
        self.factory = RequestFactory()
        for k in list(self.es_dao.__dict__):
            self.es_dao.__delattr__(k)
        for k in list(self.es_mapper.__dict__):
            self.es_mapper.__delattr__(k)

    def test_view_post_user_is_not_authenticated(self):
        request = self.factory.get('/view_post/1234')
        request.session = dict()
        request.session['is_authenticated'] = False
        response = post.view_post(request, TEST_POST_ID)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    def test_view_post_post_not_present(self):
        self.es_dao.get_post_by_id = MagicMock(side_effect=elasticsearch.NotFoundError())
        request = self.factory.get('/view_post/1234')
        request.session = dict()
        request.session['is_authenticated'] = True
        response = post.view_post(request, TEST_POST_ID)
        self.assertEqual(response.status_code, 200)

    @patch('smfhcp.views.post.es_dao', es_dao)
    @patch('smfhcp.views.post.smfhcp_utils', smfhcp_utils)
    def test_view_post_user_is_authenticated(self):
        import datetime
        test_time = datetime.datetime.now(datetime.timezone.utc)
        post_data = {'_source': {"date": TEST_DATE_UTC_STRING,
                                 "found": True,
                                 "isFollowing": True,
                                 "post_id": TEST_POST_ID,
                                 "comments": [
                                     {"date": TEST_DATE_UTC_STRING,
                                      "replies": [
                                          {"date": TEST_DATE_UTC_STRING}
                                      ]}
                                 ],
                                 "user_name": TEST_USER_NAME}
                     }
        self.es_dao.get_post_by_id = MagicMock(return_value=post_data)
        self.es_dao.update_post_view_count = MagicMock()
        self.smfhcp_utils.create_time_from_utc_string = MagicMock(return_value=test_time)
        self.smfhcp_utils.pretty_date = MagicMock(return_value=TEST_PRETTY_DATE)
        self.smfhcp_utils.find_if_follows = MagicMock(return_value=True)
        request = self.factory.get('/view_post/1234')
        request.session = dict()
        request.session['is_authenticated'] = True
        response = post.view_post(request, TEST_POST_ID)
        self.assertEqual(response.status_code, 200)
        self.es_dao.get_post_by_id.assert_called_with(TEST_POST_ID)
        self.smfhcp_utils.create_time_from_utc_string.assert_called_with(TEST_DATE_UTC_STRING)
        self.smfhcp_utils.find_if_follows.assert_called_with(request, TEST_USER_NAME, self.es_dao)
        self.es_dao.update_post_view_count.assert_called_with(TEST_POST_ID)

    def test_create_case_study_throws_permission_denied_exception(self):
        request = self.factory.get('create_post/case_study/')
        request.session = dict()
        with self.assertRaises(PermissionDenied):
            post.create_case_study(request)

    @patch('smfhcp.views.post.es_dao', es_dao)
    def test_create_case_study_valid_request(self):
        self.es_dao.get_doctor_by_user_name = MagicMock()
        self.es_dao.index_post = MagicMock(result={"_id": TEST_POST_ID})
        self.es_dao.update_post_count = MagicMock()
        request = self.factory.post('create_post/case_study/')
        request.session = dict()
        request.session["user_name"] = TEST_USER_NAME
        response = post.create_case_study(request)
        self.assertEqual(response.status_code, 200)
        self.es_dao.update_post_count.assert_called_with(TEST_USER_NAME)

    def test_create_general_post_throws_permission_denied_exception(self):
        request = self.factory.get('create_post/general_post/')
        request.session = dict()
        with self.assertRaises(PermissionDenied):
            post.create_general_post(request)

    @patch('smfhcp.views.post.es_dao', es_dao)
    def test_create_general_post_valid_request(self):
        self.es_dao.get_doctor_by_user_name = MagicMock()
        self.es_dao.index_post = MagicMock(result={"_id": TEST_POST_ID})
        self.es_dao.update_post_count = MagicMock()
        request = self.factory.post('create_post/general_post/')
        request.session = dict()
        request.session["user_name"] = TEST_USER_NAME
        response = post.create_general_post(request)
        self.assertEqual(response.status_code, 200)
        self.es_dao.update_post_count.assert_called_with(TEST_USER_NAME)

    def test_add_comment_throws_permission_denied_exception(self):
        request = self.factory.get('add_comment/')
        request.session = dict()
        with self.assertRaises(PermissionDenied):
            post.add_comment(request)

    @patch('smfhcp.views.post.es_dao', es_dao)
    @patch('smfhcp.views.post.smfhcp_utils', smfhcp_utils)
    @patch('smfhcp.views.post.es_mapper', es_mapper)
    def test_add_comment_valid_request(self):
        self.smfhcp_utils.find_hash = MagicMock(return_value=TEST_POST_ID)
        self.es_mapper.map_comment = MagicMock()
        self.es_dao.add_comment_by_post_id = MagicMock()
        request = self.factory.post('add_comment/')
        request.session = dict()
        response = post.add_comment(request)
        self.assertEqual(response.status_code, 200)
        self.es_mapper.map_comment.assert_called_with(request.POST, TEST_POST_ID)

    def test_add_reply_throws_permission_denied_exception(self):
        request = self.factory.get('add_reply/')
        request.session = dict()
        with self.assertRaises(PermissionDenied):
            post.add_reply(request)

    @patch('smfhcp.views.post.es_dao', es_dao)
    @patch('smfhcp.views.post.smfhcp_utils', smfhcp_utils)
    @patch('smfhcp.views.post.es_mapper', es_mapper)
    def test_add_reply_valid_request(self):
        self.es_mapper.map_reply = MagicMock()
        self.es_dao.add_reply_by_post_id_and_comment_id = MagicMock()
        request = self.factory.post('add_reply/')
        request.session = dict()
        response = post.add_reply(request)
        self.assertEqual(response.status_code, 200)
        self.es_mapper.map_reply.assert_called_with(request.POST)
