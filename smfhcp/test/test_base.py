import smfhcp.views.base as base
import smfhcp.constants as constants
from django.test import TestCase, RequestFactory
from unittest.mock import MagicMock, patch


TEST_DOCTOR_NAME = 'test_doctor_name'
TEST_USER_NAME = 'test_user_name'
TEST_EMAIL = 'test_email'
TEST_DATE = 'test_date_utc_string'
TEST_TIME = 'test_time'


class DummyObject(object):
    pass


class TestBase(TestCase):
    es_dao = DummyObject()
    smfhcp_utils = DummyObject()

    def setUp(self):
        self.factory = RequestFactory()
        for k in list(self.es_dao.__dict__):
            self.es_dao.__delattr__(k)
        for k in list(self.smfhcp_utils.__dict__):
            self.smfhcp_utils.__delattr__(k)

    def test_base_view_when_user_not_authenticated(self):
        request = self.factory.get('/')
        request.session = dict()
        response = base.base_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.content.decode(constants.UTF_8).__contains__('id="nav-container"'))

    @patch('smfhcp.views.base.es_dao', es_dao)
    @patch('smfhcp.views.base.smfhcp_utils', smfhcp_utils)
    def test_base_view_when_user_authenticated(self):
        self.smfhcp_utils.find_user = MagicMock(return_value=({
            'user_name': TEST_USER_NAME,
            'email': TEST_EMAIL,
            'follow_list': [TEST_DOCTOR_NAME]
        }, False))
        self.es_dao.search_posts_by_doctor_name = MagicMock(return_value={
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'user_name': TEST_DOCTOR_NAME,
                            'date': TEST_DATE
                        }
                    }
                ]
            }
        })
        self.smfhcp_utils.create_time_from_utc_string = MagicMock(return_value=TEST_TIME)
        self.smfhcp_utils.pretty_date = MagicMock(return_value='pretty_date')
        request = self.factory.get('/')
        request.session = dict()
        request.session['user_name'] = TEST_USER_NAME
        request.session['is_authenticated'] = True
        response = base.base_view(request)
        self.assertEqual(response.status_code, 200)
        self.es_dao.search_posts_by_doctor_name.assert_called_with(TEST_DOCTOR_NAME)
        self.smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)
        self.smfhcp_utils.create_time_from_utc_string.assert_called_with(TEST_DATE)
        self.smfhcp_utils.pretty_date.assert_called_with(TEST_TIME)

    def test_trending_view_when_not_authenticated(self):
        request = self.factory.get('/trending')
        request.session = dict()
        response = base.trending_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    @patch('smfhcp.views.base.es_dao', es_dao)
    @patch('smfhcp.views.base.smfhcp_utils', smfhcp_utils)
    def test_trending_view_when_user_authenticated(self):
        self.es_dao.get_all_posts = MagicMock(return_value={
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'user_name': TEST_DOCTOR_NAME,
                            'date': TEST_DATE,
                            'view_count': 5
                        }
                    }
                ]
            }
        })
        self.smfhcp_utils.create_time_from_utc_string = MagicMock(return_value=TEST_TIME)
        self.smfhcp_utils.pretty_date = MagicMock(return_value='pretty_date')
        self.smfhcp_utils.find_if_follows = MagicMock(return_value=True)
        request = self.factory.get('/trending')
        request.session = dict()
        request.session['user_name'] = TEST_USER_NAME
        request.session['is_authenticated'] = True
        response = base.trending_view(request)
        self.assertEqual(response.status_code, 200)
        self.smfhcp_utils.create_time_from_utc_string.assert_called_with(TEST_DATE)
        self.smfhcp_utils.pretty_date.assert_called_with(TEST_TIME)
        self.smfhcp_utils.find_if_follows.assert_called_with(request, TEST_DOCTOR_NAME, self.es_dao)
        self.es_dao.get_all_posts.assert_called()

    def test_handler404(self):
        response = base.handler404(self.factory.get('/'), Exception())
        self.assertEqual(response.status_code, 404)

    def test_handler500(self):
        response = base.handler500(self.factory.get('/'))
        self.assertEqual(response.status_code, 500)
