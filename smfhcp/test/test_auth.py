import smfhcp.views.auth as auth
from django.test import TestCase
from unittest.mock import MagicMock, patch
import smfhcp.utils.utils as utils
import smfhcp.constants as constants
from django.test import RequestFactory
import elasticsearch


class DummyObject(object):
    pass


class TestAuth(TestCase):
    smfhcp_utils = utils.SmfhcpUtils()
    es_dao = DummyObject()
    es_mapper = DummyObject()
    dummy_function = MagicMock()

    def setUp(self):
        self.factory = RequestFactory()
        for k in list(self.es_dao.__dict__):
            self.es_dao.__delattr__(k)
        for k in list(self.es_mapper.__dict__):
            self.es_mapper.__delattr__(k)

    def test_login_view_when_user_authenticated(self):
        request = self.factory.get('/login')
        request.session = dict()
        request.session['is_authenticated'] = True
        response = auth.login_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    def test_login_view_when_user_not_authenticated(self):
        request = self.factory.get('/login')
        request.session = dict()
        request.session['is_authenticated'] = False
        response = auth.login_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content.decode(constants.UTF_8)), 0)
        request.session = dict()
        response = auth.login_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content.decode(constants.UTF_8)), 0)

    @patch('smfhcp.views.auth.es_dao', es_dao)
    @patch('smfhcp.views.auth.es_mapper', es_mapper)
    @patch('smfhcp.views.auth.index_general_user', dummy_function)
    def test_index_when_user_not_present(self):
        self.es_dao.get_general_user_by_user_name = MagicMock(side_effect=elasticsearch.NotFoundError())
        self.es_mapper.map_general_user = MagicMock(return_value={"test": "body"})
        request = self.factory.get('/login_info')
        request.session = dict()
        request.user = DummyObject()
        request.user.username = "test_user_name"
        request.user.email = "test_email"
        response = auth.index(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.es_dao.get_general_user_by_user_name.assert_called_with("test_user_name")
        self.es_mapper.map_general_user.assert_called_with('test_user_name', 'test_email')
        self.dummy_function.assert_called_with({"test": "body"})

    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_index_when_user_present(self):
        self.es_dao.get_general_user_by_user_name = MagicMock(return_value=True)
        request = self.factory.get('/login_info')
        request.session = dict()
        request.user = DummyObject()
        request.user.username = "test_user_name"
        request.user.email = "test_email"
        response = auth.index(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.es_dao.get_general_user_by_user_name.assert_called_with("test_user_name")
