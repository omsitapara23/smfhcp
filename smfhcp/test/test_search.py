import smfhcp.views.search as search
import smfhcp.constants as constants
from django.test import TestCase, RequestFactory
from unittest.mock import MagicMock, patch


TEST_TAG = "test_tag"
TEST_SEARCH_QUERY = "test_search_query"
TEST_USER_NAME = "test_user_name"
TEST_DOCTOR_NAME = "test_doctor_name"
TEST_DATE = 'test_date_utc_string'
TEST_TIME = 'test_time'
TEST_PRETTY_DATE = 'test_pretty_date'
TEST_POST_ID = "test_post_id"
TEST_PROFILE_PICTURE = 'profile_picture.jpg'


class DummyObject(object):
    pass


class TestSearch(TestCase):
    es_dao = DummyObject()
    smfhcp_utils = DummyObject()
    find_if_follows_when_following = MagicMock()
    get_profile_picture_when_default_profile_picture = MagicMock()

    def setUp(self):
        self.factory = RequestFactory()
        for k in list(self.es_dao.__dict__):
            self.es_dao.__delattr__(k)
        for k in list(self.smfhcp_utils.__dict__):
            self.smfhcp_utils.__delattr__(k)

    def test_search_when_user_not_authenticated(self):
        request = self.factory.get('/search')
        request.session = dict()
        response = search.search(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    def test_tagged_when_user_not_authenticated(self):
        request = self.factory.get('/tagged/' + TEST_TAG)
        request.session = dict()
        response = search.tagged(request, 123)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    @patch('smfhcp.views.search.es_dao', es_dao)
    @patch('smfhcp.views.search.smfhcp_utils', smfhcp_utils)
    @patch('smfhcp.views.search.find_if_follows', find_if_follows_when_following)
    @patch('smfhcp.views.search.get_profile_picture', get_profile_picture_when_default_profile_picture)
    def test_search_for_any_query(self):
        request = self.factory.get('/search', data={
            'q': TEST_SEARCH_QUERY
        })
        request.session = dict()
        request.session['is_authenticated'] = True
        request.session['user_name'] = TEST_USER_NAME
        self.smfhcp_utils.find_user = MagicMock(return_value=({
                                                                  'user_name': TEST_USER_NAME,
                                                                  'follow_list': [TEST_DOCTOR_NAME]
                                                              }, False))
        self.es_dao.search_for_doctors = MagicMock(return_value={
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'user_name': TEST_DOCTOR_NAME
                        }
                    }
                ]
            }
        })
        self.es_dao.search_for_posts = MagicMock(return_value={
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'user_name': TEST_DOCTOR_NAME,
                            'date': TEST_DATE
                        },
                        '_id': TEST_POST_ID
                    }
                ]
            }
        })
        self.smfhcp_utils.create_time_from_utc_string = MagicMock(return_value=TEST_TIME)
        self.smfhcp_utils.pretty_date = MagicMock(return_value=TEST_PRETTY_DATE)
        response = search.search(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, TEST_SEARCH_QUERY)
        self.assertContains(response, TEST_PRETTY_DATE)
        self.smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)
        self.es_dao.search_for_doctors.assert_called_with(TEST_SEARCH_QUERY)
        self.es_dao.search_for_posts.assert_called_with(TEST_SEARCH_QUERY)
        self.smfhcp_utils.create_time_from_utc_string.assert_called_with(TEST_DATE)
        self.smfhcp_utils.pretty_date.assert_called_with(TEST_TIME)
        self.get_profile_picture_when_default_profile_picture.assert_called()
        self.find_if_follows_when_following.assert_called()

    @patch('smfhcp.views.search.es_dao', es_dao)
    @patch('smfhcp.views.search.smfhcp_utils', smfhcp_utils)
    @patch('smfhcp.views.search.find_if_follows', find_if_follows_when_following)
    def test_tagged_for_any_tag(self):
        request = self.factory.get('/tagged/' + TEST_TAG)
        request.session = dict()
        request.session['is_authenticated'] = True
        request.session['user_name'] = TEST_USER_NAME
        self.smfhcp_utils.find_user = MagicMock(return_value=({
            'user_name': TEST_USER_NAME,
            'follow_list': [TEST_DOCTOR_NAME]
        }, False))
        self.es_dao.search_for_tags = MagicMock(return_value={
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'user_name': TEST_DOCTOR_NAME,
                            'date': TEST_DATE
                        },
                        '_id': TEST_POST_ID
                    }
                ]
            }
        })
        self.smfhcp_utils.create_time_from_utc_string = MagicMock(return_value=TEST_TIME)
        self.smfhcp_utils.pretty_date = MagicMock(return_value=TEST_PRETTY_DATE)
        response = search.tagged(request, TEST_TAG)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, TEST_TAG)
        self.assertContains(response, TEST_PRETTY_DATE)
        self.smfhcp_utils.find_user.assert_called_with(TEST_USER_NAME, self.es_dao)
        self.es_dao.search_for_tags.assert_called_with(TEST_TAG)
        self.smfhcp_utils.create_time_from_utc_string.assert_called_with(TEST_DATE)
        self.smfhcp_utils.pretty_date.assert_called_with(TEST_TIME)
        self.find_if_follows_when_following.assert_called()

    def test_find_if_follows_when_following(self):
        hit = {
            '_source': {
                'user_name': TEST_DOCTOR_NAME
            }
        }
        res = {
            'user_name': TEST_USER_NAME,
            'follow_list': [TEST_DOCTOR_NAME]
        }
        search.find_if_follows(hit, res)
        self.assertTrue(hit['_source']['isFollowing'])

    def test_find_if_follows_when_not_following(self):
        hit = {
            '_source': {
                'user_name': TEST_DOCTOR_NAME
            }
        }
        res = {
            'user_name': TEST_USER_NAME,
            'follow_list': []
        }
        search.find_if_follows(hit, res)
        self.assertFalse(hit['_source']['isFollowing'])

    def test_get_profile_picture_when_default_profile_picture(self):
        hit = {
            '_source': {
                'user_name': TEST_DOCTOR_NAME
            }
        }
        search.get_profile_picture(hit)
        self.assertEqual(hit['_source']['profile_picture'], constants.DEFAULT_PROFILE_PICTURE)

    def test_get_profile_picture_when_has_profile_picture(self):
        hit = {
            '_source': {
                'user_name': TEST_DOCTOR_NAME,
                'profile_picture': TEST_PROFILE_PICTURE
            }
        }
        search.get_profile_picture(hit)
        self.assertEqual(hit['_source']['profile_picture'], constants.PROFILE_PICTURE_PATH_BASE + TEST_PROFILE_PICTURE)
