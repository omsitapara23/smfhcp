import smfhcp.views.auth as auth
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


class DummyObject(object):
    pass


class TestAuth(TestCase):
    smfhcp_utils = utils.SmfhcpUtils()
    es_dao = DummyObject()
    es_mapper = DummyObject()
    dummy_smfhcp_utils = DummyObject()
    dummy_function = MagicMock()
    index_general_user_return_false = MagicMock(return_value=False)
    index_general_user_return_true = MagicMock(return_value=True)
    send_mail_raises_error = MagicMock(side_effect=SMTPException())
    send_mail_runs_correctly = MagicMock()
    check_email_existence_returns_true = MagicMock(return_value=(True, constants.SENT_INVITE))
    check_email_existence_returns_false = MagicMock(return_value=(False, constants.USER_ALREADY_INVITED))
    send_invitation_email_returns_false = MagicMock(return_value=False)
    send_invitation_email_returns_true = MagicMock(return_value=True)
    save_profile_picture_runs_ok = MagicMock(return_value='test_path')

    def setUp(self):
        self.factory = RequestFactory()
        for k in list(self.es_dao.__dict__):
            self.es_dao.__delattr__(k)
        for k in list(self.es_mapper.__dict__):
            self.es_mapper.__delattr__(k)
        for k in list(self.dummy_smfhcp_utils.__dict__):
            self.dummy_smfhcp_utils.__delattr__(k)

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

    def login_user_valid_test(self, is_doctor):
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=({
                                                                        'user_name': TEST_USER_NAME,
                                                                        'password_hash': TEST_PASSWORD_HASH,
                                                                        'email': TEST_EMAIL
                                                                    }, is_doctor))
        self.dummy_smfhcp_utils.find_hash = MagicMock(return_value=TEST_PASSWORD_HASH)
        post_data = {
            'user_name': TEST_USER_NAME,
            'password': TEST_PASSWORD
        }
        request = self.factory.post('/login/signup_email', post_data)
        request.session = dict()
        response = auth.login_user(request)
        self.assertEqual(request.session['user_name'], TEST_USER_NAME)
        self.assertEqual(request.session['email'], TEST_EMAIL)
        self.assertEqual(request.session['is_authenticated'], True)
        self.assertEqual(request.session['is_doctor'], is_doctor)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['redirect'], True)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['redirect_url'], '/')
        self.dummy_smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)
        self.dummy_smfhcp_utils.find_hash.assert_called_with(TEST_PASSWORD)

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
        request.user.username = TEST_USER_NAME
        request.user.email = TEST_EMAIL
        response = auth.index(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.es_dao.get_general_user_by_user_name.assert_called_with(TEST_USER_NAME)
        self.es_mapper.map_general_user.assert_called_with(TEST_USER_NAME, TEST_EMAIL)
        self.dummy_function.assert_called_with({"test": "body"})

    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_index_when_user_present(self):
        self.es_dao.get_general_user_by_user_name = MagicMock(return_value=True)
        request = self.factory.get('/login_info')
        request.session = dict()
        request.user = DummyObject()
        request.user.username = TEST_USER_NAME
        request.user.email = TEST_EMAIL
        response = auth.index(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.es_dao.get_general_user_by_user_name.assert_called_with(TEST_USER_NAME)

    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_index_general_user_when_third_party_user(self):
        body = {
            "test": "data",
        }
        self.es_dao.index_general_user = MagicMock()
        self.es_dao.search_users_by_email = MagicMock()
        _ = auth.index_general_user(body)
        self.es_dao.index_general_user.assert_called_with(body)
        self.es_dao.search_users_by_email.assert_not_called()

    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_index_general_user_when_custom_user_and_user_exists(self):
        body = {
            "user_name": TEST_USER_NAME,
            "email": TEST_EMAIL,
            "password_hash": "test_password_hash"
        }
        self.es_dao.search_users_by_email = MagicMock(return_value={
            "hits": {
                "total": {
                    "value": 1
                }
            }
        })
        response = auth.index_general_user(body)
        self.assertFalse(response)
        self.es_dao.search_users_by_email.assert_called_with(TEST_EMAIL)
        self.es_dao.search_users_by_email = MagicMock(return_value={
            "hits": {
                "total": {
                    "value": 0
                }
            }
        })
        self.es_dao.get_general_user_by_user_name = MagicMock()
        response = auth.index_general_user(body)
        self.assertFalse(response)
        self.es_dao.search_users_by_email.assert_called_with(TEST_EMAIL)
        self.es_dao.get_general_user_by_user_name.assert_called_with(TEST_USER_NAME)
        self.es_dao.search_users_by_email = MagicMock(return_value={
            "hits": {
                "total": {
                    "value": 0
                }
            }
        })
        self.es_dao.get_general_user_by_user_name = MagicMock(side_effect=elasticsearch.NotFoundError())
        self.es_dao.get_doctor_by_user_name = MagicMock()
        response = auth.index_general_user(body)
        self.assertFalse(response)
        self.es_dao.search_users_by_email.assert_called_with(TEST_EMAIL)
        self.es_dao.get_general_user_by_user_name.assert_called_with(TEST_USER_NAME)
        self.es_dao.get_doctor_by_user_name.assert_called_with(TEST_USER_NAME)

    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_index_general_user_when_custom_user_and_user_does_not_exist(self):
        body = {
            "user_name": TEST_USER_NAME,
            "email": TEST_EMAIL,
            "password_hash": "test_password_hash"
        }
        self.es_dao.search_users_by_email = MagicMock(return_value={
            "hits": {
                "total": {
                    "value": 0
                }
            }
        })
        self.es_dao.get_general_user_by_user_name = MagicMock(side_effect=elasticsearch.NotFoundError())
        self.es_dao.get_doctor_by_user_name = MagicMock(side_effect=elasticsearch.NotFoundError())
        self.es_dao.index_general_user = MagicMock()
        response = auth.index_general_user(body)
        self.assertTrue(response)
        self.es_dao.search_users_by_email.assert_called_with(TEST_EMAIL)
        self.es_dao.get_general_user_by_user_name.assert_called_with(TEST_USER_NAME)
        self.es_dao.get_doctor_by_user_name.assert_called_with(TEST_USER_NAME)
        self.es_dao.index_general_user.assert_called_with(body)

    def test_signup_email_when_request_not_post(self):
        self.permission_denied_test('/login/signup_email', auth.signup_email)

    @patch('smfhcp.views.auth.es_mapper', es_mapper)
    @patch('smfhcp.views.auth.index_general_user', index_general_user_return_false)
    def test_signup_email_when_user_already_exists(self):
        self.es_mapper.map_general_user = MagicMock(return_value={"test": "data"})
        post_data = {
            'user_name': TEST_USER_NAME,
            'password': TEST_PASSWORD,
            'email': TEST_EMAIL
        }
        request = self.factory.post('/login/signup_email', post_data)
        response = auth.signup_email(request)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'],
                         constants.USER_OR_EMAIL_ALREADY_EXISTS_MESSAGE)
        self.index_general_user_return_false.assert_called_with({"test": "data"})
        self.es_mapper.map_general_user.assert_called_with(TEST_USER_NAME, TEST_EMAIL, password=TEST_PASSWORD)

    @patch('smfhcp.views.auth.es_mapper', es_mapper)
    @patch('smfhcp.views.auth.index_general_user', index_general_user_return_true)
    def test_signup_email_when_user_does_not_exist(self):
        self.es_mapper.map_general_user = MagicMock(return_value={"test": "data"})
        post_data = {
            'user_name': TEST_USER_NAME,
            'password': TEST_PASSWORD,
            'email': TEST_EMAIL
        }
        request = self.factory.post('/login/signup_email', post_data)
        request.session = dict()
        response = auth.signup_email(request)
        self.assertEqual(request.session['user_name'], TEST_USER_NAME)
        self.assertEqual(request.session['email'], TEST_EMAIL)
        self.assertEqual(request.session['is_authenticated'], True)
        self.assertEqual(request.session['is_doctor'], False)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['redirect'], True)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['redirect_url'], '/')
        self.index_general_user_return_true.assert_called_with({"test": "data"})
        self.es_mapper.map_general_user.assert_called_with(TEST_USER_NAME, TEST_EMAIL, password=TEST_PASSWORD)

    def test_login_user_when_request_not_post(self):
        self.permission_denied_test('/login/login_user', auth.login_user)

    @patch('smfhcp.views.auth.smfhcp_utils', dummy_smfhcp_utils)
    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_login_user_when_user_not_valid(self):
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=(None, False))
        post_data = {
            'user_name': TEST_USER_NAME,
            'password': TEST_PASSWORD
        }
        request = self.factory.post('/login/signup_email', post_data)
        request.session = dict()
        response = auth.login_user(request)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'],
                         constants.USERNAME_AND_PASSWORD_DO_NOT_MATCH)
        self.dummy_smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)

    @patch('smfhcp.views.auth.smfhcp_utils', dummy_smfhcp_utils)
    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_login_user_when_user_valid_and_is_doctor(self):
        self.login_user_valid_test(True)

    @patch('smfhcp.views.auth.smfhcp_utils', dummy_smfhcp_utils)
    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_login_user_when_user_valid_and_is_general_user(self):
        self.login_user_valid_test(False)

    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_check_email_existence_when_email_already_exists(self):
        self.es_dao.search_users_by_email = MagicMock(return_value={
            "hits": {
                "total": {
                    "value": 1
                }
            }
        })
        response = auth.check_email_existence(TEST_EMAIL)
        self.assertFalse(response[0])
        self.assertEqual(response[1], constants.USER_ALREADY_EXISTS)
        self.es_dao.search_users_by_email.assert_called_with(TEST_EMAIL)

    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_check_email_existence_when_email_already_invited(self):
        self.es_dao.search_users_by_email = MagicMock(return_value={
            "hits": {
                "total": {
                    "value": 0
                }
            }
        })
        self.es_dao.get_doctor_activation_by_email_id = MagicMock(return_value=True)
        response = auth.check_email_existence(TEST_EMAIL)
        self.assertFalse(response[0])
        self.assertEqual(response[1], constants.USER_ALREADY_INVITED)
        self.es_dao.search_users_by_email.assert_called_with(TEST_EMAIL)
        self.es_dao.get_doctor_activation_by_email_id.assert_called_with(TEST_EMAIL)

    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_check_email_existence_when_email_valid_for_invite(self):
        self.es_dao.search_users_by_email = MagicMock(return_value={
            "hits": {
                "total": {
                    "value": 0
                }
            }
        })
        self.es_dao.get_doctor_activation_by_email_id = MagicMock(side_effect=elasticsearch.NotFoundError())
        response = auth.check_email_existence(TEST_EMAIL)
        self.assertTrue(response[0])
        self.assertEqual(response[1], constants.SENT_INVITE)
        self.es_dao.search_users_by_email.assert_called_with(TEST_EMAIL)
        self.es_dao.get_doctor_activation_by_email_id.assert_called_with(TEST_EMAIL)

    @patch('smfhcp.views.auth.send_mail', send_mail_raises_error)
    def test_send_invitation_email_when_error_in_sending_mail(self):
        test_email = TEST_EMAIL
        test_token = 123
        response = auth.send_invitation_email(test_email, test_token)
        self.send_mail_raises_error.assert_called_with(constants.INVITE_EMAIL_SUBJECT,
                                                       from_email=settings.EMAIL_HOST_USER,
                                                       recipient_list=[test_email],
                                                       html_message=ANY,
                                                       fail_silently=False,
                                                       message='')
        self.assertFalse(response)

    @patch('smfhcp.views.auth.send_mail', send_mail_runs_correctly)
    def test_send_invitation_email_when_sent_mail(self):
        test_email = TEST_EMAIL
        test_token = 123
        response = auth.send_invitation_email(test_email, test_token)
        self.send_mail_runs_correctly.assert_called_with(constants.INVITE_EMAIL_SUBJECT,
                                                         from_email=settings.EMAIL_HOST_USER,
                                                         recipient_list=[test_email],
                                                         html_message=ANY,
                                                         fail_silently=False,
                                                         message='')
        self.assertTrue(response)

    @patch('smfhcp.views.auth.check_email_existence', check_email_existence_returns_false)
    def test_send_invite_when_email_invalid(self):
        post_data = {
            'email': TEST_EMAIL
        }
        request = self.factory.post('/send_invite', post_data)
        response = auth.send_invite(request)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'],
                         constants.USER_ALREADY_INVITED)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['success'],
                         False)
        self.check_email_existence_returns_false.assert_called_with(TEST_EMAIL)

    @patch('smfhcp.views.auth.send_invitation_email', send_invitation_email_returns_false)
    @patch('smfhcp.views.auth.check_email_existence', check_email_existence_returns_true)
    def test_send_invite_when_mail_not_sent(self):
        post_data = {
            'email': TEST_EMAIL
        }
        request = self.factory.post('/send_invite', post_data)
        response = auth.send_invite(request)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'],
                         constants.COULD_NOT_SEND_EMAIL)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['success'],
                         False)
        self.send_invitation_email_returns_false.assert_called_with(TEST_EMAIL, ANY)
        self.check_email_existence_returns_true.assert_called_with(TEST_EMAIL)

    @patch('smfhcp.views.auth.send_invitation_email', send_invitation_email_returns_true)
    @patch('smfhcp.views.auth.check_email_existence', check_email_existence_returns_true)
    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_send_invite_when_mail_sent(self):
        self.es_dao.index_doctor_activation = MagicMock()
        post_data = {
            'email': TEST_EMAIL
        }
        request = self.factory.post('/send_invite', post_data)
        response = auth.send_invite(request)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'],
                         constants.INVITATION_SENT_SUCCESSFULLY)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['success'],
                         True)
        self.send_invitation_email_returns_true.assert_called_with(TEST_EMAIL, ANY)
        self.check_email_existence_returns_true.assert_called_with(TEST_EMAIL)
        self.es_dao.index_doctor_activation.assert_called_with(TEST_EMAIL, ANY)

    def test_doctor_signup_when_user_already_logged_in(self):
        request = self.factory.get('/doctor_signup/123')
        request.session = dict()
        request.session['is_authenticated'] = True
        response = auth.doctor_signup(request, 123)
        self.assertFalse(response.content.decode(constants.UTF_8).__contains__('value="123"'))

    def test_doctor_signup_when_user_not_logged_in(self):
        request = self.factory.get('/doctor_signup/123')
        request.session = dict()
        response = auth.doctor_signup(request, 123)
        self.assertTrue(response.content.decode(constants.UTF_8).__contains__('value="123"'))

    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_index_doctor(self):
        self.es_dao.index_doctor = MagicMock()
        post_data = {
            'user_name': TEST_USER_NAME,
            'email': TEST_EMAIL
        }
        request = self.factory.post('/create_profile', post_data)
        request.session = dict()
        auth.index_doctor(request, post_data, 'test_profile_picture')
        self.assertEqual(request.session['user_name'], TEST_USER_NAME)
        self.assertEqual(request.session['email'], TEST_EMAIL)
        self.assertEqual(request.session['is_authenticated'], True)
        self.assertEqual(request.session['is_doctor'], True)
        self.es_dao.index_doctor.assert_called_with(post_data, 'test_profile_picture')

    @patch('smfhcp.views.auth.logout_user', dummy_function)
    def test_logout(self):
        request = self.factory.get('/logout')
        request.session = dict()
        response = auth.logout(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.assertEqual(request.session['user_name'], None)
        self.assertEqual(request.session['email'], None)
        self.assertEqual(request.session['is_authenticated'], False)
        self.assertEqual(request.session['is_doctor'], None)
        self.dummy_function.assert_called_with(request)

    def test_create_profile_when_request_not_post(self):
        self.permission_denied_test('/create_profile', auth.create_profile)

    @patch('smfhcp.views.auth.smfhcp_utils', dummy_smfhcp_utils)
    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_create_profile_when_user_already_exists(self):
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=('not_none', False))
        post_data = {
            'user_name': TEST_USER_NAME
        }
        request = self.factory.post('/create_profile', post_data)
        response = auth.create_profile(request)
        self.dummy_smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'],
                         constants.USERNAME_ALREADY_EXISTS)

    @patch('smfhcp.views.auth.smfhcp_utils', dummy_smfhcp_utils)
    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_create_profile_when_user_not_invited(self):
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=(None, False))
        self.es_dao.get_doctor_activation_by_email_id = MagicMock(side_effect=elasticsearch.NotFoundError())
        post_data = {
            'user_name': TEST_USER_NAME,
            'email': TEST_EMAIL
        }
        request = self.factory.post('/create_profile', post_data)
        response = auth.create_profile(request)
        self.dummy_smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)
        self.es_dao.get_doctor_activation_by_email_id.assert_called_with(TEST_EMAIL)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'],
                         constants.EMAIL_DOES_NOT_HAVE_INVITE)

    @patch('smfhcp.views.auth.smfhcp_utils', dummy_smfhcp_utils)
    @patch('smfhcp.views.auth.es_dao', es_dao)
    def test_create_profile_when_otp_does_not_match(self):
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=(None, False))
        self.es_dao.get_doctor_activation_by_email_id = MagicMock(return_value={
            '_source': {
                'token': '123'
            }
        })
        post_data = {
            'user_name': TEST_USER_NAME,
            'email': TEST_EMAIL,
            'otp': 1234
        }
        request = self.factory.post('/create_profile', post_data)
        response = auth.create_profile(request)
        self.dummy_smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)
        self.es_dao.get_doctor_activation_by_email_id.assert_called_with(TEST_EMAIL)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['message'],
                         constants.OTP_EMAIL_PAIR_DOES_NOT_MATCH)

    @patch('smfhcp.views.auth.smfhcp_utils', dummy_smfhcp_utils)
    @patch('smfhcp.views.auth.es_dao', es_dao)
    @patch('smfhcp.views.auth.index_doctor', dummy_function)
    @patch('smfhcp.views.auth.save_profile_picture', save_profile_picture_runs_ok)
    def test_create_profile_when_profile_created(self):
        self.dummy_smfhcp_utils.find_user = MagicMock(return_value=(None, False))
        self.es_dao.get_doctor_activation_by_email_id = MagicMock(return_value={
            '_source': {
                'token': '123'
            }
        })
        post_data = {
            'user_name': TEST_USER_NAME,
            'email': TEST_EMAIL,
            'otp': 123
        }
        request = self.factory.post('/create_profile', post_data)
        response = auth.create_profile(request)
        self.dummy_smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)
        self.es_dao.get_doctor_activation_by_email_id.assert_called_with(TEST_EMAIL)
        self.save_profile_picture_runs_ok.assert_called_with(request)
        self.dummy_function.assert_called_with(request, request.POST, 'test_path')
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['redirect'], True)
        self.assertEqual(json.loads(response.content.decode(constants.UTF_8))['redirect_url'], '/')
