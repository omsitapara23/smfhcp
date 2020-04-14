import smfhcp.views.password as password
from django.test import TestCase
from unittest.mock import MagicMock, patch, ANY
import smfhcp.utils.utils as utils
import smfhcp.constants as constants
from django.test import RequestFactory
import elasticsearch
from django.core.exceptions import PermissionDenied
import json
from smtplib import SMTPException
from django.conf import settings

TEST_USER_NAME = 'test_user_name'
TEST_EMAIL = 'test_email'
TEST_PASSWORD = 'test_password'
TEST_PASSWORD_HASH = 'test_password_hash'
TEST_OTP = "test_otp"


class DummyObject(object):
    pass


class TestPassword(TestCase):
    smfhcp_utils = utils.SmfhcpUtils()
    es_dao = DummyObject()
    dummy_smfhcp_utils = DummyObject()
    send_mail_raises_error = MagicMock(side_effect=SMTPException())
    send_mail_runs_correctly = MagicMock()
    send_password_reset_email_success = MagicMock()
    get_random_string_test = MagicMock(return_value='123456')

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

    @patch('smfhcp.views.password.send_mail', send_mail_runs_correctly)
    def test_send_password_reset_email_success(self):
        res = {
            'user_name': TEST_USER_NAME,
            'email': TEST_EMAIL
        }
        response = password.send_password_reset_email(res, TEST_OTP)
        self.send_mail_runs_correctly.assert_called_with(constants.PASSWORD_RESET_REQUEST_SUBJECT,
                                                         from_email=settings.EMAIL_HOST_USER,
                                                         recipient_list=[TEST_EMAIL],
                                                         html_message=ANY,
                                                         fail_silently=False,
                                                         message='')
        self.assertTrue(response)

    @patch('smfhcp.views.password.send_mail', send_mail_raises_error)
    def test_send_password_reset_email_failure(self):
        res = {
            'user_name': TEST_USER_NAME,
            'email': TEST_EMAIL
        }
        response = password.send_password_reset_email(res, TEST_OTP)
        self.send_mail_raises_error.assert_called_with(constants.PASSWORD_RESET_REQUEST_SUBJECT,
                                                       from_email=settings.EMAIL_HOST_USER,
                                                       recipient_list=[TEST_EMAIL],
                                                       html_message=ANY,
                                                       fail_silently=False,
                                                       message='')
        self.assertFalse(response)

    def test_forgot_password_when_request_not_Post(self):
        self.permission_denied_test('/forgot_password', password.forgot_password)

    @patch('smfhcp.views.password.es_dao', es_dao)
    @patch('smfhcp.views.password.smfhcp_utils', dummy_smfhcp_utils)
    def test_forgot_password_when_request_is_Post_but_res_None(self):
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=(None, None))
        post_data = {
            'user_name': TEST_USER_NAME
        }
        request = self.factory.post('/forgot_password', post_data)
        request.session = dict()
        response = password.forgot_password(request)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'], 'User does not exist')
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['success'], False)
        self.dummy_smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)

    @patch('smfhcp.views.password.es_dao', es_dao)
    @patch('smfhcp.views.password.smfhcp_utils', dummy_smfhcp_utils)
    def test_forgot_password_when_password_hash_not_present(self):
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=('not_none', False))
        post_data = {
            'user_name': TEST_USER_NAME
        }
        request = self.factory.post('/forgot_password', post_data)
        request.session = dict()
        response = password.forgot_password(request)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'],
                         'User has signed up through a third-party service.')
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['success'], False)
        self.dummy_smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)

    @patch('smfhcp.views.password.es_dao', es_dao)
    @patch('smfhcp.views.password.smfhcp_utils', dummy_smfhcp_utils)
    @patch('smfhcp.views.password.send_password_reset_email', send_password_reset_email_success)
    def test_forgot_password_when_user_already_present(self):
        self.es_dao.get_forgot_password_token_by_user_name = MagicMock()
        self.es_dao.add_token_to_forgot_password_token_list = MagicMock()
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=({
                                                                        'user_name': TEST_USER_NAME,
                                                                        'password_hash': TEST_PASSWORD_HASH,
                                                                        'email': TEST_EMAIL
                                                                    }, False))
        post_data = {
            'user_name': TEST_USER_NAME
        }
        request = self.factory.post('/forgot_password', post_data)
        request.session = dict()
        response = password.forgot_password(request)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'],
                         'A password reset conformation mail has been sent to {}'.format(TEST_EMAIL))
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['success'], True)
        self.es_dao.get_forgot_password_token_by_user_name.assert_called_with(TEST_USER_NAME)

    @patch('smfhcp.views.password.es_dao', es_dao)
    @patch('smfhcp.views.password.smfhcp_utils', dummy_smfhcp_utils)
    @patch('smfhcp.views.password.send_password_reset_email', send_password_reset_email_success)
    def test_forgot_password_when_user_not_present(self):
        self.es_dao.get_forgot_password_token_by_user_name = MagicMock(side_effect=elasticsearch.NotFoundError)
        self.es_dao.index_forgot_password_token = MagicMock()
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=({
                                                                        'user_name': TEST_USER_NAME,
                                                                        'password_hash': TEST_PASSWORD_HASH,
                                                                        'email': TEST_EMAIL
                                                                    }, False))
        post_data = {
            'user_name': TEST_USER_NAME
        }
        request = self.factory.post('/forgot_password', post_data)
        request.session = dict()
        response = password.forgot_password(request)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'],
                         'A password reset conformation mail has been sent to {}'.format(TEST_EMAIL))
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['success'], True)
        self.es_dao.get_forgot_password_token_by_user_name.assert_called_with(TEST_USER_NAME)

    @patch('smfhcp.views.password.es_dao', es_dao)
    def test_reset_password_get_user_not_found(self):
        self.es_dao.get_forgot_password_token_by_user_name = MagicMock(side_effect=elasticsearch.NotFoundError)
        request = self.factory.get('/reset_password/test_user_name/test_otp')
        request.session = dict()
        response = password.reset_password(request, TEST_USER_NAME, TEST_OTP)
        self.assertEqual(response.status_code, 404)

    @patch('smfhcp.views.password.es_dao', es_dao)
    def test_reset_password_get_otp_not_found(self):
        self.es_dao.get_forgot_password_token_by_user_name = MagicMock()
        request = self.factory.get('/reset_password/test_user_name/test_otp')
        request.session = dict()
        response = password.reset_password(request, TEST_USER_NAME, TEST_OTP)
        self.assertEqual(response.status_code, 404)

    @patch('smfhcp.views.password.es_dao', es_dao)
    def test_reset_password_get_success(self):
        self.es_dao.get_forgot_password_token_by_user_name = MagicMock(return_value={
            '_source': {
                'token': [TEST_OTP]
            }
        })
        request = self.factory.get('/reset_password/test_user_name/test_otp')
        request.session = dict()
        response = password.reset_password(request, TEST_USER_NAME, TEST_OTP)
        self.assertEqual(response.status_code, 200)

    @patch('smfhcp.views.password.es_dao', es_dao)
    @patch('smfhcp.views.password.smfhcp_utils', dummy_smfhcp_utils)
    def test_reset_password_post_when_doctor(self):
        self.es_dao.delete_forgot_password_token = MagicMock()
        self.es_dao.update_password_by_user_name = MagicMock()
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=({
                                                                        'user_name': TEST_USER_NAME,
                                                                        'password_hash': TEST_PASSWORD_HASH,
                                                                        'email': TEST_EMAIL
                                                                    }, True))
        post_data = {
            'new_password': 'new_password'
        }
        request = self.factory.post('/reset_password/test_user/test_otp', post_data)
        request.session = dict()
        request.session['is_doctor'] = True
        request.session['user_name'] = TEST_USER_NAME
        request.session['email'] = TEST_EMAIL
        request.session['is_authenticated'] = True
        response = password.reset_password(request, TEST_USER_NAME, TEST_OTP)
        self.assertEqual(response.status_code, 302)
        self.es_dao.delete_forgot_password_token.assert_called_with(TEST_USER_NAME)
        self.dummy_smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)
        self.es_dao.update_password_by_user_name.asser_called_with(TEST_USER_NAME, 'new_password', True)

    @patch('smfhcp.views.password.es_dao', es_dao)
    @patch('smfhcp.views.password.smfhcp_utils', dummy_smfhcp_utils)
    def test_reset_password_post_when_general_user(self):
        self.es_dao.delete_forgot_password_token = MagicMock()
        self.es_dao.update_password_by_user_name = MagicMock()
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=({
                                                                        'user_name': TEST_USER_NAME,
                                                                        'password_hash': TEST_PASSWORD_HASH,
                                                                        'email': TEST_EMAIL
                                                                    }, False))
        post_data = {
            'new_password': 'new_password'
        }
        request = self.factory.post('/reset_password/test_user/test_otp', post_data)
        request.session = dict()
        request.session['is_doctor'] = False
        request.session['user_name'] = TEST_USER_NAME
        request.session['email'] = TEST_EMAIL
        request.session['is_authenticated'] = True
        response = password.reset_password(request, TEST_USER_NAME, TEST_OTP)
        self.assertEqual(response.status_code, 302)
        self.es_dao.delete_forgot_password_token.assert_called_with(TEST_USER_NAME)
        self.dummy_smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)
        self.es_dao.update_password_by_user_name.asser_called_with(TEST_USER_NAME, 'new_password', False)

    def test_reset_password_when_request_not_get_or_post(self):
        request = self.factory.put('/reset_password/test_user/test_otp')
        with self.assertRaises(PermissionDenied):
            _ = password.reset_password(request, TEST_USER_NAME, TEST_OTP)
